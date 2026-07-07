"""Agent Memory RAG: semantic search with sentence-transformers.

Commands:
    python memory_rag.py build       # Build/rebuild full embedding index
    python memory_rag.py update      # Incremental update (only changed files)
    python memory_rag.py search "query" [--top_k 5] [--scope CORE,guides] [--layer L2]
    python memory_rag.py stats       # Show index statistics
    python memory_rag.py benchmark   # Compare semantic vs TF-IDF
"""

import io
import json
import os
import re
import sqlite3
import struct
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

# --- Config ---
SCRIPT_DIR = Path(__file__).resolve().parent
DOCS_ROOT = Path(os.environ.get("AGENT_MEMORY_DOCS_ROOT", str(SCRIPT_DIR.parent.parent / "docs")))
DB_PATH = SCRIPT_DIR / "memory_index.db"
CHUNK_MAX_CHARS = 1500
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384  # MiniLM-L12-v2 produces 384-dim vectors

# --- Model singleton ---
_st_model = None

def get_model():
    global _st_model
    if _st_model is None:
        from sentence_transformers import SentenceTransformer
        print(f"Loading model: {MODEL_NAME} ...")
        t0 = time.time()
        _st_model = SentenceTransformer(MODEL_NAME)
        print(f"Model loaded in {time.time()-t0:.1f}s (dim={EMBEDDING_DIM})")
    return _st_model

def embed_texts(texts: list) -> np.ndarray:
    """Embed a list of texts, returns shape (N, EMBEDDING_DIM)."""
    model = get_model()
    return model.encode(texts, show_progress_bar=len(texts) > 50, normalize_embeddings=True)

def embed_single(text: str) -> np.ndarray:
    """Embed a single text."""
    model = get_model()
    return model.encode([text], normalize_embeddings=True)[0]

# --- SQLite ---

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        chunk_text TEXT NOT NULL,
        frontmatter_json TEXT,
        embedding BLOB,
        updated TEXT,
        UNIQUE(file_path, chunk_index)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY, value TEXT
    )""")
    conn.commit()
    return conn

def set_meta(conn, key, value):
    conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value))
    conn.commit()

def get_meta(conn, key):
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row[0] if row else None

# --- Frontmatter ---

def parse_frontmatter(content):
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    result = {}
    for line in content[3:end].strip().split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            val = val.strip()
            if val.startswith("[") and val.endswith("]"):
                items = [i.strip().strip('"').strip("'") for i in val[1:-1].split(",") if i.strip()]
                result[key.strip()] = items
            else:
                result[key.strip()] = val
    return result

def get_body(content):
    if not content.startswith("---"):
        return content
    end = content.find("---", 3)
    return content[end + 3:].strip() if end != -1 else content

# --- Chunking ---

def chunk_text(text, max_chars=CHUNK_MAX_CHARS):
    sections = re.split(r'\n(?=#{1,4} )', text)
    chunks, current = [], ""
    for section in sections:
        if len(current) + len(section) <= max_chars:
            current += ("\n" if current else "") + section
        else:
            if current:
                chunks.append(current.strip())
            if len(section) > max_chars:
                paragraphs = section.split("\n\n")
                sub = ""
                for para in paragraphs:
                    if len(sub) + len(para) <= max_chars:
                        sub += ("\n\n" if sub else "") + para
                    else:
                        if sub:
                            chunks.append(sub.strip())
                        sub = para
                current = sub if sub else ""
            else:
                current = section
    if current.strip():
        chunks.append(current.strip())
    return chunks if chunks else [text[:max_chars]]

# --- Build ---

def collect_files():
    if not DOCS_ROOT.exists():
        print(f"ERROR: docs root not found: {DOCS_ROOT}")
        return []
    files = sorted(f for f in DOCS_ROOT.rglob("*.md") if "archive" not in f.parts and f.is_file())
    result = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8-sig")
        except:
            continue
        fm = parse_frontmatter(content)
        if fm:
            rel = str(f.relative_to(DOCS_ROOT)).replace("\\", "/")
            result.append((rel, content, fm))
    return result

def build_index(full=False):
    conn = get_db()
    files = collect_files()
    if not files:
        print("No files with frontmatter found.")
        return

    last_build = get_meta(conn, "last_build") if not full else None
    to_update = []
    for rel, content, fm in files:
        updated = fm.get("updated", "1970-01-01")
        if full or not last_build or updated >= last_build:
            row = conn.execute("SELECT updated FROM chunks WHERE file_path=? LIMIT 1", (rel,)).fetchone()
            if row and row[0] == updated and not full:
                continue
            to_update.append((rel, content, fm))

    if not to_update:
        print(f"Index up to date. {len(files)} files tracked.")
        stats(conn)
        return

    print(f"Updating {len(to_update)} of {len(files)} files...")
    for rel, _, _ in to_update:
        conn.execute("DELETE FROM chunks WHERE file_path=?", (rel,))

    all_entries = []
    for rel, content, fm in to_update:
        body = get_body(content)
        for idx, chunk in enumerate(chunk_text(body)):
            all_entries.append((rel, idx, chunk, json.dumps(fm, ensure_ascii=False), fm.get("updated", "")))

    if not all_entries:
        print("No text to embed.")
        return

    texts = [e[2] for e in all_entries]
    print(f"Embedding {len(texts)} chunks with {MODEL_NAME}...")
    t0 = time.time()
    vectors = embed_texts(texts)
    print(f"Embedded in {time.time()-t0:.1f}s")

    for entry, vec in zip(all_entries, vectors):
        rel, idx, chunk, fm_json, updated = entry
        blob = struct.pack(f'{EMBEDDING_DIM}f', *vec)
        conn.execute(
            "INSERT INTO chunks (file_path, chunk_index, chunk_text, frontmatter_json, embedding, updated) VALUES (?,?,?,?,?,?)",
            (rel, idx, chunk, fm_json, blob, updated)
        )

    set_meta(conn, "last_build", datetime.now().strftime("%Y-%m-%d"))
    set_meta(conn, "model", MODEL_NAME)
    set_meta(conn, "dim", str(EMBEDDING_DIM))
    conn.commit()
    print(f"Done. {len(all_entries)} chunks indexed from {len(to_update)} files.")
    stats(conn)

def stats(conn=None):
    if conn is None:
        conn = get_db()
    tc = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    tf = conn.execute("SELECT COUNT(DISTINCT file_path) FROM chunks").fetchone()[0]
    lb = get_meta(conn, "last_build")
    model = get_meta(conn, "model")
    dim = get_meta(conn, "dim")
    db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
    print(f"Index: {tf} files, {tc} chunks, model={model}, dim={dim}, {db_size/1024:.0f} KB, last={lb}")

# --- Search ---

def search(query, top_k=5, scope_filter=None, layer_filter=None):
    conn = get_db()
    rows = conn.execute("SELECT file_path, chunk_index, chunk_text, frontmatter_json, embedding FROM chunks").fetchall()
    if not rows:
        print("Index is empty. Run: python memory_rag.py build")
        return []

    q_vec = embed_single(query)

    results = []
    for file_path, chunk_idx, chunk_text, fm_json, emb_blob in rows:
        fm = json.loads(fm_json) if fm_json else {}
        if scope_filter and fm.get("scope") not in scope_filter:
            continue
        if layer_filter and fm.get("layer") not in layer_filter:
            continue
        dim = len(emb_blob) // 4
        chunk_vec = np.array(struct.unpack(f'{dim}f', emb_blob), dtype=np.float32)
        sim = float(np.dot(q_vec, chunk_vec))
        results.append({
            "file": file_path,
            "chunk_index": chunk_idx,
            "score": round(sim, 4),
            "text": chunk_text[:500],
            "type": fm.get("type", ""),
            "layer": fm.get("layer", ""),
            "tags": fm.get("tags", []),
            "scope": fm.get("scope", ""),
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

# --- Benchmark ---

def benchmark():
    """Run semantic search on test queries and show results."""
    test_queries = [
        ("ECS 部署策略", "deploy/ECS_STRATEGY.md"),
        ("登录失败 fetch", "lessons-learned/LL-LOGIN-FETCH-FIX.md"),
        ("模板管理 管理后台", "guides/PRD_ADMIN.md"),
        ("数据库迁移", "api/DB_SCHEMA.md"),
        ("前后端分离 架构", "guides/ARCHITECTURE.md"),
    ]
    print("=== Semantic Search Benchmark ===\n")
    for query, expected in test_queries:
        results = search(query, top_k=3)
        top1 = results[0]["file"] if results else "N/A"
        hit = expected in top1
        print(f"Q: {query}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {top1} (score={results[0]['score']})")
        print(f"  {'HIT' if hit else 'MISS'}")
        if not hit and len(results) > 1:
            for r in results[1:]:
                if expected in r["file"]:
                    print(f"  Found at rank {results.index(r)+1}: {r['file']} (score={r['score']})")
                    break
        print()

# --- CLI ---

def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]

    if cmd == "build":
        build_index(full=True)
    elif cmd == "update":
        build_index(full=False)
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: python memory_rag.py search \"query\" [--top_k N] [--scope X,Y] [--layer Z]")
            return
        query = sys.argv[2]
        top_k, scope_filter, layer_filter = 5, None, None
        args = sys.argv[3:]
        i = 0
        while i < len(args):
            if args[i] == "--top_k" and i + 1 < len(args):
                top_k = int(args[i + 1]); i += 2
            elif args[i] == "--scope" and i + 1 < len(args):
                scope_filter = args[i + 1].split(","); i += 2
            elif args[i] == "--layer" and i + 1 < len(args):
                layer_filter = args[i + 1].split(","); i += 2
            else:
                i += 1
        results = search(query, top_k, scope_filter, layer_filter)
        print(f"=== Top {len(results)} results for: {query} ===\n")
        for i, r in enumerate(results, 1):
            print(f"[{i}] {r['file']} (score: {r['score']})")
            print(f"    type={r['type']} layer={r['layer']} scope={r['scope']} tags={r['tags']}")
            print(f"    {r['text'][:200]}...")
            print()
    elif cmd == "stats":
        stats()
    elif cmd == "benchmark":
        benchmark()
    else:
        print(f"Unknown: {cmd}\n{__doc__}")

if __name__ == "__main__":
    main()