#!/usr/bin/env python3
"""
agent-memory-kit 引导式安装器
==============================
作用:将"docs治理体系 + Agent外挂记忆"整套方法论快速部署到任意项目.
设计理念:不只是复制文件,而是引导用户建立完整的 Agent 记忆基础设施.

用法:
  python setup.py <docs_path>                    # 交互式(推荐首次使用)
  python setup.py <docs_path> --name "项目名"    # 非交互式
  python setup.py <docs_path> --quick             # 快速模式(跳过已有文件)
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime

KIT_DIR = Path(__file__).parent.parent
TEMPLATE_DIR = KIT_DIR / "templates"
DOCS_TEMPLATE_DIR = TEMPLATE_DIR / "docs"

# ═══════════════════════════════════════════════════════
#  1. 交互式收集项目信息
# ═══════════════════════════════════════════════════════

def collect_project_info(args):
    """交互式收集项目信息,或从命令行参数读取"""
    info = {}
    
    if args.name:
        info["name"] = args.name
    else:
        info["name"] = input("\n项目名称(如 MyProject): ").strip()
        if not info["name"]:
            info["name"] = "MyProject"
    
    if args.desc:
        info["desc"] = args.desc
    else:
        info["desc"] = input("项目简述(一句话): ").strip()
        if not info["desc"]:
            info["desc"] = f"{info['name']} 项目"
    
    if args.tech:
        info["tech"] = args.tech
    else:
        info["tech"] = input("技术栈(如 Python/FastAPI/Next.js): ").strip()
        if not info["tech"]:
            info["tech"] = "待补充"
    
    return info


# ═══════════════════════════════════════════════════════
#  2. 生成 docs/ 骨架
# ═══════════════════════════════════════════════════════

DOCS_DIRS = [
    "CORE",
    "ai",
    "guides",
    "api",
    "reports",
    "plans",
    "archive",
    "images",
]

def scaffold_docs(docs_root: Path, info: dict, quick: bool):
    """创建 docs/ 目录骨架和核心文档"""
    created = []
    
    # 创建目录
    for d in DOCS_DIRS:
        p = docs_root / d
        if not p.exists():
            p.mkdir(parents=True)
            created.append(f"docs/{d}/")
    
    # 生成核心文档(如果不存在)
    generators = [
        ("CORE/FEATURES.md", gen_features, info),
        ("CORE/ROADMAP.md", gen_roadmap, info),
        ("CORE/ARCHITECTURE.md", gen_architecture, info),
        ("ai/HANDOFF.md", gen_handoff, info),
        ("ai/HANDOFF_LOG.md", gen_handoff_log, info),
        ("ai/REGISTRY.md", gen_registry, info),
        ("ai/DECISIONS.md", gen_decisions, info),
        ("guides/PRD.md", gen_prd, info),
        ("guides/UX_CHECKLIST.md", gen_ux_checklist, info),
        ("guides/DEBUG_RULES.md", gen_debug_rules, info),
        ("guides/FACTUALITY_RULES.md", gen_factuality_rules, info),
        ("reports/INDEX.md", gen_report_index, info),
    ]
    
    for rel_path, gen_func, gen_info in generators:
        target = docs_root / rel_path
        if target.exists() and quick:
            continue
        if not target.exists():
            content = gen_func(gen_info)
            write_utf8(target, content)
            created.append(f"docs/{rel_path}")
    
    # 复制 Agent 记忆协议文档
    kit_docs = [
        ("AGENT_MEMORY_SCHEMA.md", "ai/AGENT_MEMORY_SCHEMA.md"),
        ("MEMORY_PROTOCOL.md", "ai/MEMORY_PROTOCOL.md"),
        ("QUICKSTART.md", "ai/MEMORY_QUICKSTART.md"),
    ]
    for src_name, dst_rel in kit_docs:
        src = DOCS_TEMPLATE_DIR / src_name
        dst = docs_root / dst_rel
        if dst.exists() and quick:
            continue
        if src.exists() and not dst.exists():
            write_utf8(dst, src.read_text(encoding="utf-8"))
            created.append(f"docs/{dst_rel}")
    
    return created


# ═══════════════════════════════════════════════════════
#  3. 生成 AGENTS.md
# ═══════════════════════════════════════════════════════

def scaffold_agents_md(project_root: Path, info: dict, quick: bool):
    """在项目根目录生成 AGENTS.md"""
    target = project_root / "AGENTS.md"
    if target.exists() and quick:
        return None
    if target.exists():
        return None  # 不覆盖已有的
    
    content = gen_agents_md(info)
    write_utf8(target, content)
    return "AGENTS.md"


# ═══════════════════════════════════════════════════════
#  4. 文档生成函数
# ═══════════════════════════════════════════════════════

def gen_features(info):
    now = datetime.now().strftime("%Y-%m-%d")
    return f'''---
type: index
layer: L1
scope: core
updated: "{now}"
---
# 功能注册表

> **本文件是功能状态的唯一真相来源.**

## 统计总表

| 状态 | 数量 | 说明 |
|------|------|------|
| + 已完成 | 0 | 已实现并通过验收 |
| 🔨 进行中 | 0 | 正在开发 |
| 📋 待开发 | 0 | 已规划未开始 |
| x 不做 | 0 | 明确不纳入 |

## 功能清单

<!-- 按模块组织,格式:| ID | 功能名 | 状态 | 前端 | 后端 | 说明 | -->

### 核心功能

| ID | 功能 | 状态 | 前端 | 后端 | 说明 |
|----|------|------|------|------|------|
| F0.1 | 示例功能 | 📋 | - | - | 请替换为实际功能 |
'''

def gen_roadmap(info):
    now = datetime.now().strftime("%Y-%m-%d")
    return f'''---
type: plan
layer: L1
scope: core
updated: "{now}"
---
# 开发路线图

> 项目:{info["name"]}
> 技术栈:{info["tech"]}
> 最后更新:{now}

## 当前进度

**总体进度:0%**

| Phase | 名称 | 状态 | 负责人 | 进度 |
|-------|------|------|--------|------|
| A | 基础搭建 | 📋 | 待定 | 0% |

## 下一步

- [ ] 项目初始化
- [ ] 核心功能开发
'''

def gen_architecture(info):
    now = datetime.now().strftime("%Y-%m-%d")
    return f'''---
type: reference
layer: L1
scope: core
updated: "{now}"
---
# 技术架构

> 项目:{info["name"]}
> 技术栈:{info["tech"]}

## 系统架构

<!-- 用文字或 Mermaid 描述系统架构 -->

## 目录结构

```
{info["name"].lower().replace(" ", "-")}/
├── docs/          # 项目文档(Agent 记忆)
├── AGENTS.md      # Agent 协作规范
└── ...
```

## 技术决策

详见 `docs/ai/DECISIONS.md`.
'''

def gen_handoff(info):
    now = datetime.now().strftime("%Y-%m-%d")
    return f'''---
type: handoff
layer: L1
scope: ai
updated: "{now}"
---
# 交接状态

> **本文件 < 100 行,只记录当前状态.**

## 项目信息

| 项 | 值 |
|----|-----|
| 项目 | {info["name"]} |
| 技术栈 | {info["tech"]} |

## 当前状态

**待开发**

## 待办

- [ ] 项目初始化

## 关键上下文

首次安装,无历史上下文.

## 重要决策

(暂无)
'''

def gen_handoff_log(info):
    now = datetime.now().strftime("%Y-%m-%d")
    return f'''---
type: log
layer: L2
scope: ai
updated: "{now}"
---
# 交接日志

> 按时间倒序记录每次交接.

---

### {now} - 初始化

- 首次安装 agent-memory-kit
- 项目:{info["name"]}
'''

def gen_registry(info):
    now = datetime.now().strftime("%Y-%m-%d")
    return f'''---
type: index
layer: L2
scope: ai
updated: "{now}"
---
# 文档索引

> 最后更新:{now}

## 目录

| 目录 | 用途 | 文件数 |
|------|------|--------|
| CORE/ | 核心文档 | 3 |
| ai/ | AI 交接文件 | 5 |
| guides/ | 专题指南 | 4 |
| api/ | API 文档 | 0 |
| reports/ | 完工报告 | 1 |
| plans/ | 计划文档 | 0 |
'''

def gen_decisions(info):
    now = datetime.now().strftime("%Y-%m-%d")
    return f'''---
type: decision
layer: L2
scope: ai
updated: "{now}"
---
# 架构决策记录

> 记录重要技术决策及其理由.

## 决策模板

### [编号] 决策标题

- **日期**:YYYY-MM-DD
- **背景**:为什么需要这个决策
- **选项**:考虑了哪些方案
- **决策**:选了什么
- **理由**:为什么选这个
- **后果**:预期影响
'''

def gen_prd(info):
    now = datetime.now().strftime("%Y-%m-%d")
    return f'''---
type: guide
layer: L2
scope: guides
updated: "{now}"
---
# 产品需求文档(PRD)

> 项目:{info["name"]}

## 1. 产品概述

{info["desc"]}

## 2. 目标用户

<!-- 描述目标用户画像 -->

## 3. 核心功能

<!-- 列出核心功能及用户故事 -->

## 4. 非功能需求

- 性能:<!-- 待补充 -->
- 安全:<!-- 待补充 -->
- 可用性:<!-- 待补充 -->
'''

def gen_ux_checklist(info):
    now = datetime.now().strftime("%Y-%m-%d")
    return f'''---
type: guide
layer: L2
scope: guides
updated: "{now}"
---
# UX 检查表

> 每个面向用户的功能上线前必须通过以下检查.

## 基础检查

| # | 检查项 | 通过 |
|---|--------|------|
| 1 | 加载状态有提示 | ☐ |
| 2 | 空状态有引导 | ☐ |
| 3 | 错误信息用户友好 | ☐ |
| 4 | 操作有反馈(toast/动画) | ☐ |
| 5 | 移动端适配 | ☐ |

## 交互检查

| # | 检查项 | 通过 |
|---|--------|------|
| 1 | 关键操作有确认弹窗 | ☐ |
| 2 | 表单有验证提示 | ☐ |
| 3 | 返回/撤销路径清晰 | ☐ |
'''

def gen_debug_rules(info):
    now = datetime.now().strftime("%Y-%m-%d")
    return f'''---
type: guide
layer: L2
scope: guides
updated: "{now}"
---
# 调试规则

> **铁律:没有查明根因之前,禁止提出修复方案.**

## 调试流程

1. **复现**:确认问题可以稳定复现
2. **定位**:用日志/断点/二分法找到根因
3. **验证**:确认根因确实能解释问题
4. **修复**:针对根因修复,不做无关改动
5. **回归**:确认修复不引入新问题

## 禁止行为

- 凭感觉猜测根因
- 不看日志就改代码
- "试试这个"式的随机修复
'''

def gen_factuality_rules(info):
    now = datetime.now().strftime("%Y-%m-%d")
    return f'''---
type: guide
layer: L2
scope: guides
updated: "{now}"
---
# 事实性规则

> **每个事实性声明必须有命令输出作为证据.**

## 核心规则

| # | 规则 | 说明 |
|---|------|------|
| 1 | 数字必须实测 | "X 个功能已完成" → 必须有命令输出支撑 |
| 2 | 状态必须验证 | "测试通过" → 必须粘贴测试输出 |
| 3 | 不确定就标注 | "待确认"/"未验证" |
| 4 | 禁止模糊表述 | "应该没问题" → 不算完成 |

## 反模式

- "大概完成了" → 不接受
- "不影响功能" → 需要证据
- "小问题" → 要么修,要么标注
'''

def gen_report_index(info):
    now = datetime.now().strftime("%Y-%m-%d")
    return f'''---
type: index
layer: L2
scope: reports
updated: "{now}"
---
# 完工报告索引

| 报告 ID | 任务名 | 日期 | 状态 |
|---------|--------|------|------|
| RPT-INIT | 项目初始化 | {now} | + |
'''

def gen_agents_md(info):
    now = datetime.now().strftime("%Y-%m-%d")
    return f'''# {info["name"]} - Agent 协作规范

> **本文件是 Agent 的行为准则.新 Agent 接班时必须先读此文件.**

---

## 快速启动

新 Agent 接班时,**只需读 3 份文档即可开工**:
1. `docs/CORE/FEATURES.md` - 功能注册表
2. `docs/CORE/ROADMAP.md` - 开发路线图
3. `docs/ai/HANDOFF.md` - 交接状态

---

## 1. 修改前检查清单

| # | 检查项 | 要求 |
|---|--------|------|
| 1 | 先读后改 | 修改任何文件前,必须先完整阅读该文件 |
| 2 | 不编造信息 | 不确定的内容必须标注待确认 |
| 3 | 测试通过才能提交 | 看到实际输出后才能声称完成 |
| 4 | 文件编码 | 含中文文件必须用 UTF-8 编码 |

---

## 2. 文档体系

| 目录 | 用途 |
|------|------|
| `docs/CORE/` | 核心文档(FEATURES,ROADMAP,ARCHITECTURE) |
| `docs/ai/` | AI 交接文件(HANDOFF,REGISTRY,记忆协议) |
| `docs/guides/` | 专题指南 |
| `docs/api/` | API 文档 |
| `docs/reports/` | 完工报告 |

---

## 3. Agent 记忆协议

本项目采用**分层记忆加载**,详见 `docs/ai/MEMORY_PROTOCOL.md`.

### 人类指令集

| 指令 | 触发词 | Agent 执行 |
|------|--------|-----------|
| 交班 | 交班 | 更新 HANDOFF → 追加 LOG |
| 接班 | 接班 | 读 HANDOFF → 条件读取上下文 → **自动语义检索** |
| 语义检索 | 语义检索,搜记忆 | `python memory_rag.py search "query"` |
| 文档同步 | doc-sync | 检查文档一致性 |
| 项目状态 | 项目状态 | 读取 ROADMAP 汇报进度 |
| 更新项目信息 | 更新项目信息、技术栈变了、依赖更新 | 1）检查实际代码依赖；2）运行 `python agent-memory-kit/scripts/update-meta.py ./docs --tech "新栈"`；3）更新 HANDOFF.md |

---

## 4. 事实性规则

**每个事实性声明必须有命令输出作为证据.** 详见 `docs/guides/FACTUALITY_RULES.md`.

---

## 5. 调试规则

**没有查明根因之前,禁止提出修复方案.** 详见 `docs/guides/DEBUG_RULES.md`.

---

> 本文件由 agent-memory-kit 自动生成于 {now}
'''


# ═══════════════════════════════════════════════════════
#  5. 工具函数
# ═══════════════════════════════════════════════════════

def write_utf8(path: Path, content: str):
    """写入 UTF-8 文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ═══════════════════════════════════════════════════════
#  6. 后处理:frontmatter + 索引 + 验证
# ═══════════════════════════════════════════════════════

def post_process(docs_root: Path):
    """运行 frontmatter 注入,索引构建,链接验证"""
    results = {}
    
    # 1) frontmatter
    add_fm = KIT_DIR / "scripts" / "add_frontmatter.py"
    if add_fm.exists():
        import subprocess
        r = subprocess.run(
            [sys.executable, str(add_fm), str(docs_root)],
            capture_output=True, text=True, timeout=120
        )
        results["frontmatter"] = "OK" if r.returncode == 0 else f"FAIL: {r.stderr[:200]}"
    
    # 2) RAG 索引
    rag = KIT_DIR / "scripts" / "memory_rag.py"
    if rag.exists():
        import subprocess
        r = subprocess.run(
            [sys.executable, str(rag), "build", str(docs_root)],
            capture_output=True, text=True, timeout=300
        )
        results["rag_index"] = "OK" if r.returncode == 0 else f"FAIL: {r.stderr[:200]}"
    
    # 3) 图谱验证
    graph = KIT_DIR / "scripts" / "memory_graph.py"
    if graph.exists():
        import subprocess
        r = subprocess.run(
            [sys.executable, str(graph), "validate", str(docs_root)],
            capture_output=True, text=True, timeout=60
        )
        results["graph"] = "OK" if r.returncode == 0 else f"WARN: {r.stderr[:200]}"
    
    return results


# ═══════════════════════════════════════════════════════
#  7. 主入口
# ═══════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="agent-memory-kit 引导式安装器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python setup.py ./docs                        # 交互式
  python setup.py ./docs --name "MyProject"     # 非交互式
  python setup.py ./docs --quick                # 快速模式(跳过已有)
  python setup.py ./docs --skip-rag             # 不建 RAG 索引
        """
    )
    parser.add_argument("docs_path", help="docs 目录路径")
    parser.add_argument("--name", help="项目名称")
    parser.add_argument("--desc", help="项目简述")
    parser.add_argument("--tech", help="技术栈")
    parser.add_argument("--quick", action="store_true", help="快速模式(跳过已有文件)")
    parser.add_argument("--skip-rag", action="store_true", help="跳过 RAG 索引构建")
    parser.add_argument("--with-rag", action="store_true", help="安装骨架 + 自动安装 sentence-transformers 并构建 RAG 索引")
    parser.add_argument("--skip-agents", action="store_true", help="不生成 AGENTS.md")
    parser.add_argument("--update-meta", action="store_true", help="更新已有文档的项目元数据（配合 --tech/--name/--desc 使用）")
    
    args = parser.parse_args()
    
    docs_root = Path(args.docs_path).resolve()
    project_root = docs_root.parent  # docs/ 的父目录即项目根
    
    print("=" * 50)
    print("  agent-memory-kit 引导式安装器")
    print("=" * 50)
    print(f"\n项目根目录: {project_root}")
    print(f"文档目录:   {docs_root}")
    
    # 1) 收集信息
    info = collect_project_info(args)
    print(f"\n项目名称: {info['name']}")
    print(f"项目简述: {info['desc']}")
    print(f"技术栈:   {info['tech']}")
    
    # 2) 生成 docs/ 骨架
    print("\n--- 生成 docs/ 骨架 ---")
    created_docs = scaffold_docs(docs_root, info, args.quick)
    for f in created_docs:
        print(f"  + {f}")
    if not created_docs:
        print("  (所有文件已存在,跳过)")
    
    # 3) 生成 AGENTS.md
    if not args.skip_agents:
        print("\n--- 生成 AGENTS.md ---")
        agents_result = scaffold_agents_md(project_root, info, args.quick)
        if agents_result:
            print(f"  + {agents_result}")
        else:
            print("  (已存在,跳过)")
    
    # 4) 后处理
    if not args.skip_rag:
        print("\n--- 后处理(frontmatter + 索引 + 验证)---")
        results = post_process(docs_root)
        for k, v in results.items():
            print(f"  {k}: {v}")
    else:
        print("\n--- 跳过后处理(--skip-rag)---")
    
    # 5) 就绪报告
    print("\n" + "=" * 50)
    print("  + 安装完成！")
    print("=" * 50)
    print(f"""
下一步:
  1. 检查 docs/CORE/FEATURES.md - 添加你的功能清单
  2. 检查 docs/CORE/ROADMAP.md - 规划开发路线
  3. 检查 docs/ai/HANDOFF.md - 记录当前状态
  4. 检查 AGENTS.md - 根据项目需要补充协作规范

Agent 记忆协议:
  - L1 文档(每次接班必读):CORE/ + ai/AGENT_MEMORY_SCHEMA.md
  - L2 文档(按需加载):guides/ + api/ + reports/
  - 语义检索:python scripts/memory_rag.py search "你的问题"

更多说明:README.md
""")

if __name__ == "__main__":
    main()

# ═══════════════════════════════════════════════════════
#  8. 更新项目元数据
# ═══════════════════════════════════════════════════════

def update_meta(docs_root: Path, info: dict):
    """更新已有文档中的项目元数据"""
    import re
    updated = []
    
    # 需要更新的文件和替换规则
    updates = [
        ("CORE/ARCHITECTURE.md", [
            (r"(技术栈：).*", f"\\1{info.get('tech', '')}"),
        ]),
        ("CORE/ROADMAP.md", [
            (r"(技术栈：).*", f"\\1{info.get('tech', '')}"),
        ]),
        ("ai/HANDOFF.md", [
            (r"(\| 技术栈 \|).*", f"\\1 {info.get('tech', '')} |"),
        ]),
        ("guides/PRD.md", [
            (r"(技术栈：).*", f"\\1{info.get('tech', '')}"),
        ]),
    ]
    
    for rel_path, patterns in updates:
        target = docs_root / rel_path
        if not target.exists():
            continue
        
        content = target.read_text(encoding="utf-8")
        original = content
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        if content != original:
            write_utf8(target, content)
            updated.append(rel_path)
    
    return updated
