"""Batch-inject YAML frontmatter into docs/ md files.

Usage:
    python scripts/add_frontmatter.py [--dry-run]

Reads AGENT_MEMORY_SCHEMA.md rules to auto-fill type/layer/tags/scope/related/updated.
Skips files that already have frontmatter (--- block at line 1).
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

# --- Config ---
DOCS_ROOT = Path(os.environ.get("AGENT_MEMORY_DOCS_ROOT", str(Path(__file__).resolve().parent.parent.parent / "docs")))
TODAY = datetime.now().strftime("%Y-%m-%d")

# Directory -> defaults mapping
DIR_DEFAULTS = {
    "CORE":      {"type": "reference",    "layer": "L1-instruction", "scope": "CORE"},
    "ai":        {"type": "reference",    "layer": "L2-reference",   "scope": "ai"},
    "api":       {"type": "reference",    "layer": "L2-reference",   "scope": "api"},
    "deploy":    {"type": "howto",        "layer": "L2-reference",   "scope": "deploy"},
    "design":    {"type": "explanation",  "layer": "L3-background",  "scope": "design"},
    "guides":    {"type": "howto",        "layer": "L2-reference",   "scope": "guides"},
    "lessons-learned": {"type": "lesson", "layer": "L3-background",  "scope": "lessons-learned"},
    "plans":     {"type": "plan",         "layer": "L3-background",  "scope": "plans"},
    "reports":   {"type": "report",       "layer": "L3-background",  "scope": "reports"},
}

# Special file overrides (relative to docs/)
FILE_OVERRIDES = {
    "ai/HANDOFF.md": {"type": "reference", "layer": "L1-instruction"},
    "ai/DECISIONS.md": {"type": "adr"},
    "ai/DECISIONS-LATE.md": {"type": "adr"},
    "ai/AGENT_RUNTIME.md": {"type": "explanation"},
    "guides/PRD.md": {"type": "explanation", "layer": "L2-reference"},
    "guides/PRD_ADMIN.md": {"type": "explanation", "layer": "L2-reference"},
    "guides/ARCHITECTURE.md": {"type": "explanation", "layer": "L2-reference"},
    "guides/UX_CHECKLIST.md": {"type": "reference", "layer": "L2-reference"},
    "guides/COPYWRITING.md": {"type": "reference", "layer": "L2-reference"},
    "guides/DEBUG_RULES.md": {"type": "reference", "layer": "L2-reference"},
    "guides/FACTUALITY_RULES.md": {"type": "reference", "layer": "L2-reference"},
    "guides/ENCODING.md": {"type": "reference", "layer": "L2-reference"},
    "guides/COMMANDS.md": {"type": "reference", "layer": "L2-reference"},
    "guides/DIRECTORY.md": {"type": "reference", "layer": "L2-reference"},
    "guides/QUICKSTART.md": {"type": "howto", "layer": "L1-instruction"},
    "guides/SETUP.md": {"type": "howto", "layer": "L2-reference"},
    "guides/STARTUP.md": {"type": "howto", "layer": "L2-reference"},
    "guides/PRODUCTION.md": {"type": "howto", "layer": "L2-reference"},
    "guides/GIT_SYNC.md": {"type": "reference", "layer": "L2-reference"},
    "guides/CODEX_SYNC.md": {"type": "reference", "layer": "L2-reference"},
    "guides/CODE_REVIEW_CHECKLIST.md": {"type": "reference", "layer": "L2-reference"},
    "guides/FIGMA_MCP_SETUP.md": {"type": "howto", "layer": "L3-background"},
    "guides/TROUBLESHOOT_TAURI_LOGIN.md": {"type": "howto", "layer": "L3-background"},
    "guides/SETUP_FEISHU_BRIDGE.md": {"type": "howto", "layer": "L3-background"},
    "guides/STARTUP_TUTORIAL.md": {"type": "howto", "layer": "L2-reference"},
    "api/DB_SCHEMA.md": {"type": "reference", "tags": ["database", "schema", "backend"]},
    "api/DRYRUN618_API.md": {"type": "reference", "layer": "L3-background"},
    "api/overview.md": {"tags": ["api", "backend"]},
    "design/LANDING_PAGE_DESIGN.md": {"tags": ["frontend", "ux", "copywriting", "design"]},
    "design/LANDING_PAGE_WIREFRAMES.md": {"tags": ["frontend", "ux", "design"]},
    "design/LANDING_PAGE_WIREFRAMES_P2.md": {"tags": ["frontend", "ux", "design"]},
    "design/LANDING_PAGE_TECH.md": {"tags": ["frontend", "design", "performance"]},
    "design/APP_ICON_DESIGN.md": {"tags": ["frontend", "design", "desktop"]},
    "design/DESIGN-D3.2.md": {"tags": ["frontend", "ux", "design", "desktop"]},
    "CORE/FEATURES.md": {"tags": ["planning", "features", "infrastructure"]},
    "CORE/ROADMAP.md": {"tags": ["planning", "infrastructure"]},
    "CORE/ARCHITECTURE.md": {"type": "adr", "tags": ["backend", "frontend", "ai", "infrastructure"]},
}

# Filename -> tags inference
TAG_KEYWORDS = {
    "auth": ["auth", "backend", "api"],
    "billing": ["billing", "backend", "api"],
    "marketplace": ["marketplace", "backend", "api"],
    "employees": ["employees", "backend", "api"],
    "tasks": ["tasks", "backend", "api"],
    "knowledge": ["knowledge", "backend", "api"],
    "reviews": ["reviews", "backend", "api"],
    "exports": ["exports", "backend", "api"],
    "system": ["system", "backend", "api"],
    "cloud": ["cloud", "deployment", "api"],
    "config": ["config", "backend", "api"],
    "devices": ["devices", "backend", "api"],
    "websocket": ["websocket", "backend", "api"],
    "errors": ["errors", "backend", "api"],
    "database": ["database", "backend"],
    "deploy": ["deployment", "ecs"],
    "ecs": ["deployment", "ecs"],
    "login": ["auth", "frontend", "debugging"],
    "handoff": ["handoff", "infrastructure"],
    "startup": ["infrastructure", "backend", "frontend"],
    "troubleshoot": ["debugging"],
    "mcp": ["ai", "skills"],
    "figma": ["design", "frontend"],
    "landing": ["frontend", "ux", "design"],
    "icon": ["design", "frontend"],
    "ux": ["ux", "frontend"],
    "copywriting": ["copywriting", "ux"],
    "ratelimit": ["backend", "debugging", "performance"],
    "fetch": ["frontend", "debugging"],
    "e2e": ["testing"],
    "audit": ["review", "testing"],
    "workflow": ["ai", "backend"],
    "agent": ["ai", "infrastructure"],
    "memory": ["memory", "ai", "infrastructure"],
    "rag": ["memory", "ai"],
    "schema": ["database", "schema"],
    "feishu": ["infrastructure", "integration"],
    "prd": ["planning", "ux"],
    "architecture": ["infrastructure", "backend", "frontend"],
    "phase": ["planning"],
    "stage": ["planning", "reports"],
}

# Related links per directory
RELATED_BY_DIR = {
    "CORE": ["[[ARCHITECTURE.md]]", "[[FEATURES.md]]"],
    "ai": ["[[HANDOFF.md]]", "[[REGISTRY.md]]"],
    "api": ["[[overview.md]]", "[[DB_SCHEMA.md]]"],
    "deploy": ["[[ECS_STRATEGY.md]]", "[[DEPLOY_GUIDE.md]]"],
    "design": ["[[LANDING_PAGE_DESIGN.md]]"],
    "guides": ["[[PRD.md]]", "[[ARCHITECTURE.md]]"],
    "lessons-learned": ["[[INDEX.md]]"],
    "plans": ["[[AGENT_MEMORY_INFRA.md]]"],
    "reports": ["[[INDEX.md]]"],
}


def infer_tags(filename: str, dir_name: str) -> list:
    """Infer tags from filename and directory."""
    tags = set()
    fname_lower = filename.lower().replace(".md", "")
    for keyword, ktags in TAG_KEYWORDS.items():
        if keyword in fname_lower:
            tags.update(ktags)
    if dir_name == "api":
        tags.add("api")
        tags.add("backend")
    if dir_name == "deploy":
        tags.add("deployment")
    if dir_name == "reports":
        tags.add("planning")
    if not tags:
        tags.add("infrastructure")
    return sorted(list(tags))[:6]


def has_frontmatter(content: str) -> bool:
    """Check if content already has YAML frontmatter."""
    return content.startswith("---\n") or content.startswith("---\r\n")


def build_frontmatter(rel_path: str, dir_name: str, filename: str) -> str:
    """Build YAML frontmatter string for a file."""
    # Start with directory defaults
    defaults = DIR_DEFAULTS.get(dir_name, {"type": "reference", "layer": "L2-reference", "scope": dir_name})
    fm = dict(defaults)

    # Apply file overrides
    for override_path, overrides in FILE_OVERRIDES.items():
        if rel_path.replace("\\", "/") == override_path:
            fm.update(overrides)
            break

    # Infer tags if not set
    tags = fm.get("tags", infer_tags(filename, dir_name))

    # Related
    related = RELATED_BY_DIR.get(dir_name, [])

    # Build YAML
    lines = ["---"]
    lines.append(f"type: {fm['type']}")
    lines.append(f"layer: {fm['layer']}")
    lines.append(f"tags: [{', '.join(tags)}]")
    lines.append(f"related: [{', '.join(related)}]")
    lines.append(f"scope: {fm.get('scope', dir_name)}")
    lines.append(f"updated: {TODAY}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def process_file(filepath: Path, docs_root: Path, dry_run: bool) -> tuple:
    """Process a single md file. Returns (status, message)."""
    rel = filepath.relative_to(docs_root)
    rel_str = str(rel)
    dir_name = rel.parts[0] if len(rel.parts) > 0 else ""
    filename = rel.name

    # Skip INDEX.md in reports (special)
    if rel_str == "reports\\INDEX.md" or rel_str == "reports/templates\\COMPLETION_REPORT_TEMPLATE.md":
        return "skip", f"SKIP (special): {rel_str}"

    try:
        content = filepath.read_text(encoding="utf-8-sig")
    except Exception as e:
        return "error", f"ERROR reading {rel_str}: {e}"

    if has_frontmatter(content):
        return "skip", f"SKIP (has frontmatter): {rel_str}"

    frontmatter = build_frontmatter(rel_str, dir_name, filename)
    new_content = frontmatter + content

    if dry_run:
        return "dry", f"DRY-RUN: Would add frontmatter to {rel_str}"

    try:
        filepath.write_text(new_content, encoding="utf-8-sig")
        return "ok", f"OK: {rel_str}"
    except Exception as e:
        return "error", f"ERROR writing {rel_str}: {e}"


def main():
    dry_run = "--dry-run" in sys.argv
    docs_root = DOCS_ROOT

    if not docs_root.exists():
        print(f"ERROR: docs root not found: {docs_root}")
        sys.exit(1)

    # Collect all md files (non-archive)
    md_files = sorted([
        f for f in docs_root.rglob("*.md")
        if "archive" not in f.parts and f.is_file()
    ])

    print(f"=== Batch Frontmatter Injection {'(DRY RUN)' if dry_run else ''} ===")
    print(f"Found {len(md_files)} md files in {docs_root}")
    print()

    stats = {"ok": 0, "skip": 0, "dry": 0, "error": 0}
    for f in md_files:
        status, msg = process_file(f, docs_root, dry_run)
        stats[status] = stats.get(status, 0) + 1
        print(msg)

    print()
    print(f"=== Summary ===")
    print(f"OK: {stats['ok']} | Skipped: {stats['skip']} | Dry-run: {stats['dry']} | Errors: {stats['error']}")
    print(f"Total: {len(md_files)}")


if __name__ == "__main__":
    main()