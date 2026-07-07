"""Agent Memory Graph: validate related links + export Mermaid diagram.

Commands:
    python memory_graph.py validate   # Check related links integrity
    python memory_graph.py export     # Export Mermaid graph to docs/ai/MEMORY_GRAPH.md
    python memory_graph.py stats      # Graph statistics
"""

import json
import os
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

DOCS_ROOT = Path(os.environ.get("AGENT_MEMORY_DOCS_ROOT", str(Path(__file__).resolve().parent.parent / "docs")))

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

def collect_graph():
    """Build adjacency list from related links."""
    files = sorted(f for f in DOCS_ROOT.rglob("*.md") if "archive" not in f.parts and f.is_file())
    graph = {}  # rel_path -> {fm, related_paths}
    name_to_paths = {}  # filename.md -> [full rel paths]

    for f in files:
        try:
            content = f.read_text(encoding="utf-8-sig")
        except:
            continue
        fm = parse_frontmatter(content)
        rel = str(f.relative_to(DOCS_ROOT)).replace("\\", "/")
        graph[rel] = {"fm": fm, "related": []}
        fname = f.name
        name_to_paths.setdefault(fname, []).append(rel)

    # Resolve related links
    broken = []
    for rel, data in graph.items():
        related_raw = data["fm"].get("related", [])
        for link in related_raw:
            # Parse [[filename.md]] format
            m = re.match(r'\[\[(.+?)\]\]', link)
            if not m:
                continue
            target_name = m.group(1)
            if target_name in name_to_paths:
                for tp in name_to_paths[target_name]:
                    data["related"].append(tp)
            else:
                broken.append((rel, target_name))

    return graph, broken, name_to_paths

def validate():
    """Validate related links integrity."""
    graph, broken, name_map = collect_graph()
    total_files = len(graph)
    total_links = sum(len(d["related"]) for d in graph.values())
    files_with_links = sum(1 for d in graph.values() if d["related"])

    print(f"=== Related Links Validation ===")
    print(f"Files: {total_files}")
    print(f"Files with related links: {files_with_links}")
    print(f"Total resolved links: {total_links}")

    if broken:
        print(f"\nBroken links ({len(broken)}):")
        for src, target in broken:
            print(f"  {src} -> [[{target}]] (NOT FOUND)")
    else:
        print(f"\nBroken links: 0 (all OK)")

    # Check for one-way links (A->B but not B->A)
    one_way = []
    for rel, data in graph.items():
        for target in data["related"]:
            if target in graph:
                back_links = [r.replace("[[", "").replace("]]", "") for r in graph[target]["fm"].get("related", [])]
                src_name = rel.split("/")[-1]
                if src_name not in back_links:
                    one_way.append((rel, target))

    print(f"\nOne-way links (A->B but B doesn't link back): {len(one_way)}")
    if one_way and len(one_way) <= 20:
        for src, tgt in one_way[:20]:
            print(f"  {src} -> {tgt}")

    return len(broken) == 0

def export_mermaid():
    """Export graph as Mermaid diagram."""
    graph, broken, name_map = collect_graph()

    # Build edges (deduplicated)
    edges = set()
    nodes = set()
    for rel, data in graph.items():
        short_src = rel.split("/")[-1].replace(".md", "")
        scope = data["fm"].get("scope", "other")
        nodes.add((short_src, scope))
        for target in data["related"]:
            short_tgt = target.split("/")[-1].replace(".md", "")
            tgt_scope = graph.get(target, {}).get("fm", {}).get("scope", "other")
            nodes.add((short_tgt, tgt_scope))
            edge = tuple(sorted([short_src, short_tgt]))
            edges.add(edge)

    # Group by scope for styling
    scope_colors = {
        "CORE": "#ff6b6b",
        "ai": "#4ecdc4",
        "api": "#45b7d1",
        "deploy": "#96ceb4",
        "guides": "#ffeaa7",
        "design": "#dda0dd",
        "plans": "#98d8c8",
        "reports": "#f7dc6f",
        "lessons-learned": "#bb8fce",
    }

    lines = ["```mermaid"]
    lines.append("graph LR")

    # Subgraphs by scope
    scope_groups = defaultdict(list)
    for name, scope in nodes:
        scope_groups[scope].append(name)

    for scope, names in sorted(scope_groups.items()):
        safe_scope = scope.replace("-", "_")
        lines.append(f"    subgraph {safe_scope}[\"{scope}\"]")
        for name in sorted(names):
            safe_name = name.replace("-", "_").replace(".", "_").replace(" ", "_")
            lines.append(f"        {safe_name}[\"{name}\"]")
        lines.append("    end")

    # Edges
    for src, tgt in sorted(edges):
        safe_src = src.replace("-", "_").replace(".", "_").replace(" ", "_")
        safe_tgt = tgt.replace("-", "_").replace(".", "_").replace(" ", "_")
        lines.append(f"    {safe_src} --- {safe_tgt}")

    lines.append("```")

    # Write document
    md = []
    md.append("---")
    md.append("type: explanation")
    md.append("layer: L3-background")
    md.append("tags: [memory, infrastructure, visualization]")
    md.append('related: ["[[AGENT_MEMORY_SCHEMA.md]]", "[[MEMORY_PROTOCOL.md]]"]')
    md.append("scope: ai")
    md.append("updated: 2026-07-06")
    md.append("---")
    md.append("")
    md.append("# Agent 记忆知识图谱")
    md.append("")
    md.append(f"> **自动导出**：由 memory_graph.py 生成")
    md.append(f"> **节点**：{len(nodes)} | **边**：{len(edges)} | **范围**：{len(scope_groups)} 个 scope")
    md.append("")
    md.append("## 文档关联图")
    md.append("")
    md.extend(lines)
    md.append("")
    md.append("## 统计")
    md.append("")
    md.append("| Scope | 文档数 |")
    md.append("|-------|--------|")
    for scope, names in sorted(scope_groups.items()):
        md.append(f"| {scope} | {len(names)} |")
    md.append("")

    out_path = DOCS_ROOT / "ai" / "MEMORY_GRAPH.md"
    out_path.write_text("\n".join(md), encoding="utf-8-sig")
    print(f"Exported Mermaid graph to {out_path}")
    print(f"Nodes: {len(nodes)}, Edges: {len(edges)}, Scopes: {len(scope_groups)}")

def stats():
    """Graph statistics."""
    graph, broken, name_map = collect_graph()
    scope_counts = defaultdict(int)
    type_counts = defaultdict(int)
    layer_counts = defaultdict(int)
    degree = defaultdict(int)

    for rel, data in graph.items():
        fm = data["fm"]
        scope_counts[fm.get("scope", "unknown")] += 1
        type_counts[fm.get("type", "unknown")] += 1
        layer_counts[fm.get("layer", "unknown")] += 1
        degree[rel] = len(data["related"])

    print("=== Memory Graph Statistics ===")
    print(f"Total files: {len(graph)}")
    print(f"Broken links: {len(broken)}")
    print(f"\nBy scope:")
    for s, c in sorted(scope_counts.items(), key=lambda x: -x[1]):
        print(f"  {s}: {c}")
    print(f"\nBy type:")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")
    print(f"\nBy layer:")
    for l, c in sorted(layer_counts.items(), key=lambda x: -x[1]):
        print(f"  {l}: {c}")

    if degree:
        top = sorted(degree.items(), key=lambda x: -x[1])[:10]
        print(f"\nTop 10 most connected:")
        for path, d in top:
            print(f"  {path}: {d} links")

def main():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "validate":
        validate()
    elif cmd == "export":
        export_mermaid()
    elif cmd == "stats":
        stats()
    else:
        print(f"Unknown: {cmd}")

if __name__ == "__main__":
    main()