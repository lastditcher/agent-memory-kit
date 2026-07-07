# agent-memory-kit

**AI Agent 记忆基础设施工具包**

> 将"docs治理体系 + Agent外挂记忆"整套方法论快速部署到任意项目。
> 从 AIruzhi 项目实战中提炼，让每个项目都能拥有结构化的 Agent 记忆。

---

## 核心理念

传统方式：每个项目从零摸索 → 文档散乱 → Agent 接班靠运气 → 知识随人员流失

agent-memory-kit：一键引导 → 结构化 docs → 分层记忆协议 → 语义检索 → 知识永驻

---

## 快速开始（30 秒）

```bash
# 复制到你的项目
cp -r agent-memory-kit /path/to/your-project/

# 引导式安装（交互式）
python agent-memory-kit/scripts/setup.py ./docs

# 或者一行命令
python agent-memory-kit/scripts/setup.py ./docs --name "MyProject" --tech "Python/FastAPI"
```

安装器会自动：
1. 创建 `docs/` 目录骨架（CORE/ai/guides/api/reports/plans）
2. 生成 6 个核心文档（FEATURES/ROADMAP/HANDOFF/REGISTRY/DECISIONS/ARCHITECTURE）
3. 生成 `AGENTS.md`（Agent 协作规范 + 人类指令集）
4. 注入 Agent 记忆协议（Schema + Protocol + Quickstart）
5. 为所有 md 文件添加 YAML frontmatter
6. 构建 RAG 向量索引
7. 验证文档链接

---

## 产出物

安装完成后，你的项目会拥有：

### docs/ 目录结构

```
docs/
├── CORE/
│   ├── FEATURES.md      ← 功能注册表（L1，每次必读）
│   ├── ROADMAP.md       ← 开发路线图（L1）
│   └── ARCHITECTURE.md  ← 技术架构（L1）
├── ai/
│   ├── HANDOFF.md       ← 当前交接状态（L1，<100行）
│   ├── HANDOFF_LOG.md   ← 交接历史（L2）
│   ├── REGISTRY.md      ← 文档索引（L2）
│   ├── DECISIONS.md     ← 架构决策记录（L2）
│   ├── AGENT_MEMORY_SCHEMA.md  ← 记忆 Schema
│   ├── MEMORY_PROTOCOL.md      ← 分层加载协议
│   └── MEMORY_QUICKSTART.md    ← 快速指南
├── guides/
│   ├── PRD.md           ← 产品需求文档
│   ├── UX_CHECKLIST.md  ← UX 检查表
│   ├── DEBUG_RULES.md   ← 调试规则
│   └── FACTUALITY_RULES.md ← 事实性规则
├── api/                 ← API 文档
├── reports/             ← 完工报告
└── plans/               ← 计划文档
```

### AGENTS.md（项目根目录）

- Agent 协作规范
- 人类指令集（交班/接班/语义检索/doc-sync）
- 记忆协议引用

### RAG 索引

- SQLite 向量数据库（`memory_index.db`）
- 支持语义搜索（`python memory_rag.py search "问题"`）

---

## Agent 记忆协议

### 分层加载

| 层级 | 文件数 | 加载时机 | 目的 |
|------|--------|----------|------|
| **L1** | 6 | 每次接班必读 | 当前真相 |
| **L2** | ~40 | 按需加载 | 操作手册 |
| **L3** | ~180 | 语义检索 | 完整知识库 |

### 人类指令集

| 指令 | 触发词 | Agent 执行 |
|------|--------|-----------|
| 交班 | 交班 | 更新 HANDOFF → 追加 LOG |
| 接班 | 接班 | 读 HANDOFF → 条件读取 → **自动语义检索** |
| 语义检索 | 语义检索、搜记忆 | `python memory_rag.py search "query"` |
| 文档同步 | doc-sync | 检查文档一致性 |
| 项目状态 | 项目状态 | 读取 ROADMAP 汇报进度 |

---

## 工具包内容

```
agent-memory-kit/
├── README.md              ← 本文件
├── SKILL.md               ← Codex Skill 定义
├── templates/
│   └── docs/              ← 文档模板
│       ├── AGENT_MEMORY_SCHEMA.md
│       ├── MEMORY_PROTOCOL.md
│       └── QUICKSTART.md
└── scripts/
    ├── setup.py           ← 引导式安装器（主入口）
    ├── add_frontmatter.py ← frontmatter 注入
    ├── memory_rag.py      ← 语义搜索引擎
    └── memory_graph.py    ← 知识图谱工具
```

---

## 使用场景

### 场景 1：新项目从零开始

```bash
# 1. 安装
python setup.py ./docs --name "电商平台" --tech "Next.js/PostgreSQL"

# 2. 编辑核心文档
vim docs/CORE/FEATURES.md  # 添加功能清单
vim docs/CORE/ROADMAP.md   # 规划开发路线

# 3. 开始开发，Agent 自动遵循记忆协议
```

### 场景 2：已有项目升级

```bash
# 1. 安装（快速模式，跳过已有文件）
python setup.py ./docs --quick

# 2. 为已有文件添加 frontmatter
python add_frontmatter.py ./docs

# 3. 构建 RAG 索引
python memory_rag.py build ./docs
```

### 场景 3：日常使用

```bash
# Agent 接班时（自动）
# → 读 HANDOFF.md
# → 条件加载上下文
# → 自动语义检索 Top-3

# 人类手动检索
python memory_rag.py search "如何部署到生产环境"

# 查看知识图谱
python memory_graph.py stats ./docs
```

---

## 适用范围

- ✅ 任何有 `docs/` 目录的项目
- ✅ 任何使用 AI Agent 辅助开发的团队
- ✅ 任何需要知识传承的长期项目
- ✅ Codex / Cursor / Claude 等 AI 编程助手

---

## 与 AIruzhi 的关系

agent-memory-kit 从 AIruzhi 项目中提炼，但**完全独立**：

- 无 AIruzhi 特定代码
- 无硬编码路径
- 环境变量可配（`AGENT_MEMORY_DOCS_ROOT`）
- 可直接复制到任何项目使用

---

## License

MIT — 自由使用、修改、分发。

---

> 打包时间：2026-07-07
> 来源：AIruzhi 项目 Agent 记忆基础设施实战