---
name: memory-setup
description: 为任意项目安装"Agent 记忆外挂"。当用户提到"安装记忆外挂""设置记忆系统""初始化语义检索""给项目加记忆"时触发。
---

# memory-setup: Agent 记忆外挂安装向导

> **定位**：引导式 Skill，为任意项目一键安装 Agent 记忆基础设施。
> **独立性**：不依赖 airuzhi 业务代码，只读取目标项目的 docs/ 目录。
> **版本**：v1.0

---

## 前置条件

| 条件 | 要求 |
|------|------|
| Python | 3.10+ |
| 项目结构 | 有 `docs/` 目录，里面有 md 文件 |
| 依赖库 | numpy（通常已有），sentence-transformers（安装向导会装） |

## 安装流程（引导式，共 5 步）

### Step 1：环境检查

```bash
python --version          # 确认 3.10+
pip list | findstr numpy  # 确认 numpy 已装
pip list | findstr torch  # 确认 torch 已装（通常 Python 科学计算环境已有）
```

如果 torch 未安装：`pip install torch`（约 2-5 分钟）

### Step 2：安装 sentence-transformers

```bash
pip install sentence-transformers --no-deps
```

> `--no-deps` 跳过重复安装已有依赖。如果报错，改用 `pip install sentence-transformers`。

### Step 3：复制脚本到目标项目

将以下 3 个脚本复制到目标项目的任意位置（建议 `{project}/tools/memory/`）：

| 脚本 | 用途 | 来源 |
|------|------|------|
| `add_frontmatter.py` | 批量给 md 文件加 YAML 元数据 | `airuzhi/skills/memory-search/scripts/` |
| `memory_rag.py` | 语义检索引擎 | `airuzhi/skills/memory-search/scripts/` |
| `memory_graph.py` | 链接验证 + 图谱导出 | `airuzhi/skills/memory-search/scripts/` |

**复制后需要修改**：
- 打开 `add_frontmatter.py`，修改 `DOCS_ROOT` 为新项目的 docs 路径
- 打开 `memory_rag.py`，修改 `DOCS_ROOT` 为新项目的 docs 路径
- 打开 `memory_graph.py`，修改 `DOCS_ROOT` 为新项目的 docs 路径

### Step 4：初始化

```bash
# 4a. 批量加 frontmatter（只运行一次）
python add_frontmatter.py            # 实际执行
python add_frontmatter.py --dry-run  # 先预览

# 4b. 下载模型（首次约 5-10 分钟，之后不需要）
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2'); print('OK')"

# 4c. 构建索引
python memory_rag.py build
```

### Step 5：验证

```bash
# 语义检索测试
python memory_rag.py search "你的测试问题" --top_k 3

# 链接验证
python memory_graph.py validate

# 图谱导出
python memory_graph.py export
```

输出 `Done. X chunks indexed from Y files.` 即安装成功。

---

## 自定义 frontmatter 规则

安装脚本内置了通用的 frontmatter 规则（按目录推断 type/layer/scope），但每个项目可能需要调整。

打开 `add_frontmatter.py`，修改以下映射：

```python
# 目录 -> 默认值映射
DIR_DEFAULTS = {
    "docs":  {"type": "reference", "layer": "L2-reference", "scope": "docs"},
    "api":   {"type": "reference", "layer": "L2-reference", "scope": "api"},
    "guides": {"type": "howto",    "layer": "L2-reference", "scope": "guides"},
    # ... 按项目结构添加
}

# 文件名 -> 标签推断
TAG_KEYWORDS = {
    "auth": ["auth", "api"],
    "deploy": ["deployment"],
    # ... 按项目关键词添加
}
```

---

## 高级配置

### 更换 Embedding 模型

默认模型 `paraphrase-multilingual-MiniLM-L12-v2`（384 维，多语言，~200MB 内存）。

如需更强的模型，修改 `memory_rag.py` 里的 `MODEL_NAME`：

| 模型 | 维度 | 内存 | 效果 | 适用 |
|------|------|------|------|------|
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | ~200MB | 好 | 默认推荐 |
| `all-MiniLM-L6-v2` | 384 | ~100MB | 中 | 内存受限 |
| `all-mpnet-base-v2` | 768 | ~500MB | 最好 | 内存充裕 |
| `BAAI/bge-small-zh-v1.5` | 512 | ~150MB | 中文最优 | 纯中文项目 |

### 使用 OpenAI Embedding API（零本地开销）

修改 `memory_rag.py`，将 `embed_texts()` 和 `embed_single()` 替换为 OpenAI API 调用：

```python
from openai import OpenAI
client = OpenAI(api_key="your-key")

def embed_texts(texts):
    resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in resp.data]
```

适合服务器/云端环境（内存 <2GB）。

### 使用 Mimo/DeepSeek 等国产模型

如果目标平台提供 OpenAI 兼容的 Embedding API，只需改 `base_url`：

```python
client = OpenAI(api_key="your-key", base_url="https://your-api.com/v1")
```

---

## 后续维护

| 操作 | 命令 |
|------|------|
| 新增文档后更新索引 | `python memory_rag.py update` |
| 全量重建索引 | `python memory_rag.py build` |
| 检查链接完整性 | `python memory_graph.py validate` |
| 导出 Mermaid 图谱 | `python memory_graph.py export` |

---

## 与 Codex AGENTS.md 集成

如果目标项目使用 Codex 开发，在 AGENTS.md 中添加：

```markdown
### Skills 系统
| Skill | 触发关键词 | 说明 |
|-------|------------|------|
| memory-search | 语义检索、查找项目知识 | Agent 记忆语义检索（sentence-transformers） |
| memory-setup | 安装记忆外挂 | 为项目初始化记忆基础设施 |
```

---

*本 Skill 适用于任何有 docs/ 目录的中大型长期项目。安装耗时约 15-20 分钟（含模型下载）。*