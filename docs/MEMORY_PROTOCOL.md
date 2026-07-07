---
type: reference
layer: L1-instruction
tags: [memory, infrastructure, schema]
related: ["[[AGENT_MEMORY_SCHEMA.md]]", "[[AGENT_MEMORY_INFRA.md]]"]
scope: ai
updated: 2026-07-06
---

# Agent 记忆加载协议（Memory Loading Protocol）

> **版本**：v1.1 | **日期**：2026-07-06
> **定位**：Phase 2 产出。所有 Agent 对话启动时必须遵循本协议。

---

## 一、三层记忆模型

| 层级 | 名称 | 加载时机 | 内容 | 体积限制 |
|------|------|---------|------|---------|
| **L1 热记忆** | 每次对话必加载 | 对话启动时自动加载 | AGENTS.md + CORE/三件套 + HANDOFF.md + QUICKSTART.md | 合计 <800 行 |
| **L2 温记忆** | 任务相关时加载 | Agent 判断需要时加载 | guides/、api/、deploy/、ai/ 中按需读取 | 单文件 <300 行 |
| **L3 冷记忆** | 语义检索命中时加载 | memory-search 搜索命中后加载 | reports/、lessons-learned/、plans/、design/ 中的背景知识 | 无限制 |

---

## 二、Agent 启动流程（3 步快速恢复）

```
Step 1: 读取 L1（<3 秒）
  → AGENTS.md（项目协作规范，根目录）
  → docs/CORE/FEATURES.md（功能注册表）
  → docs/CORE/ROADMAP.md（开发路线图）
  → docs/ai/HANDOFF.md（交接状态，<100行）
  → docs/CORE/ARCHITECTURE.md（技术决策参考，非必读但可快速浏览）

Step 2: 判断任务方向
  → 读 HANDOFF.md 的"下一步"字段
  → 确认是否需要额外上下文

Step 3: 按需加载 L2/L3
  → 任务涉及 ECS 部署 → 读 docs/deploy/ECS_STRATEGY.md（L2）
  → 任务涉及 API 开发 → 读 docs/api/overview.md（L2）
  → 排障/查历史教训 → memory-search 语义检索（L3）
  → 任务涉及产品定义 → 读 docs/guides/PRD.md（L2）
```

---

## 三、语义检索使用规则

### 何时触发 memory-search

| 场景 | 命令示例 |
|------|---------|
| 不确定信息在哪份文档 | `python memory_rag.py search "ECS 端口配置"` |
| 排障需要查历史教训 | `python memory_rag.py search "fetch failed" --scope lessons-learned` |
| 查找特定功能的历史决策 | `python memory_rag.py search "模板管理 状态机" --layer L2-reference` |
| 快速了解某个模块 | `python memory_rag.py search "管理后台" --top_k 5` |

### 何时不触发

- 已知文件路径 → 直接 `[System.IO.File]::ReadAllText()` 读取
- L1 文件已加载 → 无需检索
- 简单操作（git status、npm run build）→ 不需要记忆

---

## 四、记忆更新规则

| 事件 | 更新内容 | 触发 |
|------|---------|------|
| 任务完成 | HANDOFF.md + HANDOFF_LOG.md | 步骤⑤收尾时 |
| 功能状态变更 | FEATURES.md | 步骤⑤收尾时 |
| Phase 进度变更 | ROADMAP.md + HANDOFF.md | 步骤⑤收尾时 |
| 新增文档 | REGISTRY.md + frontmatter | doc-maintain 时 |
| 索引更新 | `python memory_rag.py update` | 文件 frontmatter 的 updated 字段变更后 |

---

## 五、与现有 Skills 的边界

| Skill | 职责 | 区别 |
|-------|------|------|
| **docs** | 已知路径，直接读文件 | 不做搜索，直读 |
| **memory-search** | 未知路径，语义检索 | TF-IDF 检索，返回 Top-K |
| **handoff** | 交接班流程 | 更新 HANDOFF 文档 |
| **doc-sync** | 文档一致性检查 | 不做检索，做校验 |
| **doc-maintain** | 文档与代码同步 | 前端/后端代码变更后同步文档 |

---

*本协议是 Phase 2 核心产出，所有 Agent 必须遵循。*