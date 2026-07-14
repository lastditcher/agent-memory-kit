"""AIruzhi Memory MCP Server - final version

Model pre-loads in a background thread at startup (before MCP event loop starts).
Search/stats/rebuild are sync functions called via asyncio.to_thread.
"""

import asyncio
import json
import os
import sqlite3
import struct
import sys
import threading
import time
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR / "memory_index.db"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

server = Server("AIruzhi Memory")

# --- Model preload in background thread (starts immediately at import time) ---
_st_model = None
_load_time = None
_model_ready = threading.Event()


def _preload_model():
    global _st_model, _load_time
    try:
        from sentence_transformers import SentenceTransformer
        t0 = time.time()
        _st_model = SentenceTransformer(MODEL_NAME)
        _load_time = time.time() - t0
    except Exception:
        pass
    finally:
        _model_ready.set()


# Start loading NOW, before asyncio.run()
threading.Thread(target=_preload_model, daemon=True).start()


def _get_model():
    _model_ready.wait(timeout=120)
    if _st_model is None:
        raise RuntimeError("Model failed to load")
    return _st_model


# --- Tool functions (sync, will be called via to_thread) ---

def _stats():
    if not DB_PATH.exists():
        return "Index not built yet."
    conn = sqlite3.connect(str(DB_PATH))
    tc = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    tf = conn.execute("SELECT COUNT(DISTINCT file_path) FROM chunks").fetchone()[0]
    row = conn.execute("SELECT value FROM meta WHERE key='last_build'").fetchone()
    lb = row[0] if row else "unknown"
    conn.close()
    db_size = DB_PATH.stat().st_size
    return "Index: {} files, {} chunks, {} KB, last={}, model_load={:.1f}s".format(
        tf, tc, db_size // 1024, lb, _load_time or 0
    )


def _search(query, top_k=5):
    if not DB_PATH.exists():
        return "Error: Index not built."
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute(
        "SELECT file_path, chunk_index, chunk_text, frontmatter_json, embedding FROM chunks"
    ).fetchall()
    if not rows:
        return "Error: Index is empty."
    model = _get_model()
    import numpy as np
    q_vec = model.encode([query], normalize_embeddings=True)[0]
    results = []
    for file_path, chunk_idx, chunk_text, fm_json, emb_blob in rows:
        fm = json.loads(fm_json) if fm_json else {}
        dim = len(emb_blob) // 4
        chunk_vec = np.array(struct.unpack("{}f".format(dim), emb_blob), dtype=np.float32)
        sim = float(np.dot(q_vec, chunk_vec))
        results.append({
            "file": file_path,
            "score": round(sim, 4),
            "text": chunk_text[:300],
            "layer": fm.get("layer", ""),
            "scope": fm.get("scope", ""),
        })
    results.sort(key=lambda x: x["score"], reverse=True)
    top = results[:top_k]
    if not top:
        return "No results found."
    lines = ["Top {} results for: {}\n".format(len(top), query)]
    for i, r in enumerate(top, 1):
        lines.append("[{}] {} (score: {})".format(i, r["file"], r["score"]))
        lines.append("    {}...".format(r["text"][:200]))
        lines.append("")
    return "\n".join(lines)


# --- MCP handlers ---

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="memory_search",
            description="Search AIruzhi project docs using semantic similarity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {"type": "integer", "description": "Max results", "default": 5},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="memory_stats",
            description="Show memory index statistics.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name, arguments):
    if name == "memory_search":
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 5)
        result = await asyncio.to_thread(_search, query, top_k)
    elif name == "memory_stats":
        result = await asyncio.to_thread(_stats)
    else:
        result = "Unknown tool: {}".format(name)
    return [TextContent(type="text", text=result)]


async def main():
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())