"""Agent Memory Kit: one-click setup.

Usage:
    python setup.py <docs_path> [--force] [--skip-model]

Steps:
    1. Validate docs_path exists and has md files
    2. Inject frontmatter into all md files (skip if already present)
    3. Download embedding model (skip if already cached)
    4. Build semantic search index
    5. Validate related links
    6. Print summary
"""

import io
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def main():
    if len(sys.argv) < 2:
        print("Usage: python setup.py <docs_path> [--force] [--skip-model]")
        print("  docs_path:  path to your project's docs/ directory")
        print("  --force:    rebuild index even if already exists")
        print("  --skip-model: skip model download check")
        sys.exit(1)

    docs_path = Path(sys.argv[1]).resolve()
    force = "--force" in sys.argv
    skip_model = "--skip-model" in sys.argv

    print("=" * 50)
    print("Agent Memory Kit - Setup")
    print("=" * 50)
    print(f"Docs path: {docs_path}")
    print()

    # Step 1: Validate
    print("[1/5] Validating docs path...")
    if not docs_path.exists():
        print(f"  ERROR: {docs_path} does not exist")
        sys.exit(1)
    md_files = list(docs_path.rglob("*.md"))
    md_non_archive = [f for f in md_files if "archive" not in f.parts]
    print(f"  Found {len(md_files)} md files ({len(md_non_archive)} non-archive)")
    if len(md_non_archive) == 0:
        print("  ERROR: No md files found outside archive/")
        sys.exit(1)

    # Step 2: Inject frontmatter
    print("[2/5] Injecting frontmatter...")
    scripts_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(scripts_dir))
    os.environ["DOCS_ROOT_OVERRIDE"] = str(docs_path)

    # Monkey-patch DOCS_ROOT in add_frontmatter
    import importlib
    import add_frontmatter as af
    af.DOCS_ROOT = docs_path

    dry_count = 0
    skip_count = 0
    ok_count = 0
    for f in sorted(md_non_archive):
        try:
            content = f.read_text(encoding="utf-8-sig")
        except:
            continue
        if af.has_frontmatter(content):
            skip_count += 1
            continue
        rel = str(f.relative_to(docs_path)).replace("\\", "/")
        dir_name = Path(rel).parts[0] if len(Path(rel).parts) > 0 else ""
        filename = Path(rel).name
        frontmatter = af.build_frontmatter(rel, dir_name, filename)
        new_content = frontmatter + content
        try:
            f.write_text(new_content, encoding="utf-8-sig")
            ok_count += 1
        except Exception as e:
            print(f"  ERROR: {rel}: {e}")
    print(f"  Injected: {ok_count} | Skipped (already has): {skip_count}")

    # Step 3: Model check
    if not skip_model:
        print("[3/5] Checking embedding model...")
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            print(f"  Model ready (dim={model.get_embedding_dimension()})")
            del model
        except ImportError:
            print("  WARNING: sentence-transformers not installed")
            print("  Run: pip install sentence-transformers --no-deps")
        except Exception as e:
            print(f"  WARNING: Model download needed: {e}")
            print("  Will download on first index build")
    else:
        print("[3/5] Skipping model check")

    # Step 4: Build index
    print("[4/5] Building semantic index...")
    import memory_rag as rag
    rag.DOCS_ROOT = docs_path
    db_path = scripts_dir / "memory_index.db"
    if db_path.exists() and not force:
        print("  Index already exists. Use --force to rebuild.")
        rag.stats()
    else:
        if db_path.exists():
            db_path.unlink()
        try:
            rag.build_index(full=True)
        except Exception as e:
            print(f"  WARNING: Index build failed: {e}")
            print("  You can retry later with: python memory_rag.py build")

    # Step 5: Validate links
    print("[5/5] Validating related links...")
    import memory_graph as mg
    mg.DOCS_ROOT = docs_path
    try:
        graph, broken, _ = mg.collect_graph()
        print(f"  Files: {len(graph)} | Broken links: {len(broken)}")
        if broken:
            for src, tgt in broken[:5]:
                print(f"    {src} -> [[{tgt}]] (NOT FOUND)")
    except Exception as e:
        print(f"  WARNING: Validation failed: {e}")

    # Summary
    print()
    print("=" * 50)
    print("Setup complete!")
    print("=" * 50)
    print()
    print("Usage:")
    print(f"  python {scripts_dir}/memory_rag.py search \"your question\" --top_k 5")
    print(f"  python {scripts_dir}/memory_graph.py validate")
    print(f"  python {scripts_dir}/memory_graph.py export")
    print()
    print("For more info, see README.md")


if __name__ == "__main__":
    main()