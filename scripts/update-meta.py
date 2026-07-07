#!/usr/bin/env python3
"""
更新项目元数据（技术栈、名称、描述）
支持多种文档格式，智能匹配并更新。

用法:
  python update-meta.py ./docs --tech "Python/FastAPI/Next.js"
  python update-meta.py ./docs --name "新名称" --desc "新描述"
  python update-meta.py ./docs --tech "新栈" --dry-run  # 预览不写入
"""

import sys
import re
import argparse
from pathlib import Path

def write_utf8(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def update_tech_in_content(content, new_tech):
    """智能更新技术栈字段，支持多种格式"""
    updated = False
    
    # 格式 1: Markdown 表格行 | 技术栈 | xxx |
    pattern1 = r'(\|\s*技术栈\s*\|)\s*[^|]*(\|)'
    if re.search(pattern1, content):
        content = re.sub(pattern1, f'\\g<1> {new_tech} \\2', content)
        updated = True
    
    # 格式 2: 引用块 > 技术栈：xxx 或 > 技术栈: xxx
    pattern2 = r'(>\s*技术栈[：:]\s*).*'
    if re.search(pattern2, content):
        content = re.sub(pattern2, f'\\g<1>{new_tech}', content)
        updated = True
    
    # 格式 3: 普通行 技术栈：xxx 或 技术栈: xxx
    pattern3 = r'(^技术栈[：:]\s*).*'
    if re.search(pattern3, content, re.MULTILINE):
        content = re.sub(pattern3, f'\\g<1>{new_tech}', content, flags=re.MULTILINE)
        updated = True
    
    return content, updated

def update_name_in_content(content, new_name):
    """智能更新项目名称"""
    updated = False
    
    # 格式 1: # 标题
    pattern1 = r'(^#\s+).*'
    if re.search(pattern1, content, re.MULTILINE):
        content = re.sub(pattern1, f'# {new_name}', content, count=1, flags=re.MULTILINE)
        updated = True
    
    # 格式 2: > 项目：xxx
    pattern2 = r'(>\s*项目[：:]\s*).*'
    if re.search(pattern2, content):
        content = re.sub(pattern2, f'\\g<1>{new_name}', content)
        updated = True
    
    return content, updated

def update_meta(docs_root, info, dry_run=False):
    updated = []
    
    # 需要更新的文件
    target_files = [
        "CORE/ARCHITECTURE.md",
        "CORE/ROADMAP.md",
        "ai/HANDOFF.md",
        "guides/PRD.md",
    ]
    
    for rel_path in target_files:
        target = docs_root / rel_path
        if not target.exists():
            print(f"  [SKIP] {rel_path} (不存在)")
            continue
        
        content = target.read_text(encoding="utf-8")
        original = content
        file_updated = False
        
        # 更新技术栈
        if "tech" in info:
            content, u = update_tech_in_content(content, info["tech"])
            if u:
                file_updated = True
        
        # 更新名称
        if "name" in info:
            content, u = update_name_in_content(content, info["name"])
            if u:
                file_updated = True
        
        if file_updated and content != original:
            if dry_run:
                print(f"  [DRY-RUN] {rel_path} (将被更新)")
            else:
                write_utf8(target, content)
                updated.append(rel_path)
                print(f"  [UPDATE] {rel_path}")
        else:
            print(f"  [OK] {rel_path} (无需更新)")
    
    return updated

def main():
    parser = argparse.ArgumentParser(description="更新项目元数据")
    parser.add_argument("docs_path", help="docs 目录路径")
    parser.add_argument("--name", help="更新项目名称")
    parser.add_argument("--desc", help="更新项目简述")
    parser.add_argument("--tech", help="更新技术栈")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际写入")
    
    args = parser.parse_args()
    docs_root = Path(args.docs_path).resolve()
    
    info = {}
    if args.name:
        info["name"] = args.name
    if args.desc:
        info["desc"] = args.desc
    if args.tech:
        info["tech"] = args.tech
    
    if not info:
        print("[ERROR] 请至少指定一个参数 (--name/--desc/--tech)")
        parser.print_help()
        sys.exit(1)
    
    print("=" * 50)
    print("  更新项目元数据")
    print("=" * 50)
    print(f"\n文档目录: {docs_root}")
    print(f"更新内容:")
    for k, v in info.items():
        print(f"  {k}: {v}")
    
    if args.dry_run:
        print(f"\n[DRY-RUN 模式] 只预览，不写入")
    
    print()
    updated = update_meta(docs_root, info, args.dry_run)
    
    print(f"\n" + "=" * 50)
    if args.dry_run:
        print("  预览完成（未写入）")
    else:
        print(f"  完成: 更新了 {len(updated)} 个文件")
    print("=" * 50)

if __name__ == "__main__":
    main()