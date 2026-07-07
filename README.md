# Agent Memory Kit

> **一句话**：给任意项目装上"Agent 记忆外挂"——语义检索 + 知识图谱 + 分层加载。
> **适用**：任何有 `docs/` 目录的中大型长期项目（Python 3.10+）。
> **独立性**：不依赖任何业务代码，复制即用。

---

## 快速开始（3 步，约 15 分钟）

```bash
# Step 1: 安装依赖（首次约 5-10 分钟，含模型下载）
pip install sentence-transformers --no-deps
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2'); print('OK')"

# Step 2: 初始化（指定你的 docs/ 路径）
python scripts/setup.py /path/to/your/docs

# Step 3: 使用
python scripts/memory_rag.py search "你的问题" --top_k 5
```

> 如果 `--no-deps` 报错，改用 `pip install sentence-transformers`。

---

## 完整功能

| 命令 | 用途 |
|------|------|
| `python scripts/setup.py <docs_path>` | 一键初始化（加 frontmatter + 建索引） |
| `python scripts/memory_rag.py search "query"` | 语义搜索 |
| `python scripts/memory_rag.py build` | 全量重建索引 |
| `python scripts/memory_rag.py update` | 增量更新索引 |
| `python scripts/memory_rag.py stats` | 索引统计 |
| `python scripts/memory_rag.py benchmark` | 基准测试 |
| `python scripts/memory_graph.py validate` | 链接完整性验证 |
| `python scripts/memory_graph.py export` | 导出 Mermaid 知识图谱 |
| `python scripts/memory_graph.py stats` | 图谱统计 |

---

## 目录结构

```
agent-memory-kit/
├── README.md              ← 你在读的这个文件
├── SKILL.md               ← Codex/Agent Skill 定义
├── scripts/
│   ├── setup.py           ← 一键初始化脚本
│   ├── add_frontmatter.py ← 批量加 YAML 元数据
│   ├── memory_rag.py      ← 语义检索引擎（sentence-transformers）
│   └── memory_graph.py    ← 链接验证 + 图谱导出
└── docs/
    ├── AGENT_MEMORY_SCHEMA.md  ← Frontmatter 规范
    └── MEMORY_PROTOCOL.md      ← L1/L2/L3 加载协议
```

---

## 复制到新项目

```bash
# 1. 复制整个文件夹
cp -r agent-memory-kit /path/to/new-project/tools/memory

# 2. 进入目录
cd /path/to/new-project/tools/memory

# 3. 初始化（自动扫描 docs/ 加 frontmatter + 建索引）
python scripts/setup.py ../../docs    # 指向新项目的 docs 路径

# 4. 用
python scripts/memory_rag.py search "新项目的问题"
```

---

## 高级配置

详见 `SKILL.md`，包含：
- 更换 Embedding 模型（4 种推荐）
- 使用 OpenAI Embedding API（零本地开销）
- 使用国产模型（DeepSeek/Mimo 等）
- 自定义 frontmatter 规则
- Codex AGENTS.md 集成方法

---

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Embedding | paraphrase-multilingual-MiniLM-L12-v2 | 384 维，多语言，~200MB 内存 |
| 向量存储 | SQLite + struct blob | 零外部依赖 |
| 检索 | numpy 余弦相似度 | <1s/query |
| 图谱 | Mermaid + Obsidian 双链 | 可视化 |

---

## 许可

MIT — 复制即用，无需授权。