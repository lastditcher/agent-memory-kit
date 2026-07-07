---
type: reference
layer: L1-instruction
tags: [memory, schema, frontmatter, infrastructure]
related: ["[[AGENT_MEMORY_INFRA.md]]", "[[RAG_PRIORITY.md]]"]
scope: ai
updated: 2026-07-06
---

# Agent 记忆 Frontmatter Schema 规范

> **版本**：v1.0 | **日期**：2026-07-06
> **定位**：Agent 记忆基础设施 Phase 1 的核心规范，所有 docs/ 下非 archive 的 md 文件必须遵循。

---

## 一、字段定义

`yaml
---
type: reference | explanation | howto | adr | report | plan | lesson
layer: L1-instruction | L2-reference | L3-background
tags: [tag1, tag2, ...]
related: ["[[filename.md]]", ...]
scope: CORE | ai | api | deploy | design | guides | lessons-learned | plans | reports
updated: YYYY-MM-DD
---
`

### 1.1 type - 文档类型

| 值 | 含义 | 对应 Diataxis | 示例 |
|----|------|---------------|------|
| reference | API/命令/配置速查 | Reference | api/*.md, COMMANDS.md |
| explanation | 概念解释、架构说明 | Explanation | ARCHITECTURE.md, PRD.md |
| howto | 操作指南、步骤说明 | How-to | SETUP.md, ECS_STRATEGY.md |
| adr | 架构决策记录 | (扩展) | DECISIONS.md, DECISIONS-LATE.md |
| report | 完工报告/阶段报告 | (扩展) | RPT-*.md |
| plan | 规划文档 | (扩展) | AGENT_MEMORY_INFRA.md |
| lesson | 经验教训 | (扩展) | LL-LOGIN-FETCH-FIX.md |

### 1.2 layer - Agent 记忆层级

| 值 | 含义 | 加载时机 | 行数指导 |
|----|------|---------|---------|
| L1-instruction | 每次对话必读 | 合计 <600 行 | AGENTS.md, CORE/*.md |
| L2-reference | 任务相关时按需加载 | 单文件 <300 行 | api/*.md, guides/*.md |
| L3-background | 语义检索命中时加载 | 无限制 | reports/*.md, plans/*.md |

### 1.3 tags - 语义标签

标准标签表：

| 分类 | 标签 |
|------|------|
| 模块 | backend, frontend, desktop(tauri), ai, database, api |
| 功能 | auth, billing, marketplace, employees, tasks, knowledge, admin, templates, packages |
| 运维 | deployment, ecs, docker, monitoring, security |
| 流程 | handoff, testing, review, planning, migration |
| 质量 | debugging, encoding, performance, ux, copywriting |
| 基建 | infrastructure, schema, skills, memory |

规则：每个文件至少 2 个标签，最多 6 个。优先复用标准标签，必要时新增。

### 1.4 related - 双向链接

格式：[[filename.md]]（Obsidian 风格双链）。列出 1-3 个最相关的文档。

### 1.5 scope - 文档区域

对应 docs/ 下的一级子目录。

### 1.6 updated - 最后更新日期

格式：YYYY-MM-DD。用于 embedding 增量更新判断。

---

## 二、批量初始化规则

| 目录 | type 默认 | layer 默认 | scope |
|------|-----------|-----------|-------|
| docs/CORE/ | reference | L1-instruction | CORE |
| docs/ai/ | reference | L2-reference | ai |
| docs/ai/HANDOFF.md | reference | L1-instruction | ai |
| docs/ai/DECISIONS*.md | adr | L2-reference | ai |
| docs/api/ | reference | L2-reference | api |
| docs/deploy/ | howto | L2-reference | deploy |
| docs/design/ | explanation | L3-background | design |
| docs/guides/ | howto | L2-reference | guides |
| docs/lessons-learned/ | lesson | L3-background | lessons-learned |
| docs/plans/ | plan | L3-background | plans |
| docs/reports/ | report | L3-background | reports |

---

## 三、与现有体系的接口

| 体系 | 关系 |
|------|------|
| doc-governance | 本 Schema 是 doc-governance 的一部分，新增文件必须加 frontmatter |
| doc-sync | 可扩展 Check 15：验证 frontmatter 完整性 |
| memory-search skill | 读取 frontmatter 做元数据过滤，updated 驱动增量索引 |
| REGISTRY.md | frontmatter tags 可与 REGISTRY 的分类对齐 |

---

*本规范由 Agent 记忆基础设施 Phase 1 创建，由 doc-governance skill 维护。*
---

## 四、当前 Embedding 技术栈

| 项目 | 说明 |
|------|------|
| 模型 | paraphrase-multilingual-MiniLM-L12-v2（sentence-transformers） |
| 维度 | 384 |
| 语言 | 多语言（含中文） |
| 运行 | 本地，零 API 成本 |
| 首次加载 | ~10s（模型缓存在 ~/.cache/huggingface/） |
| 索引速度 | 536 chunk / 23s |
| 索引体积 | 2.2MB（SQLite） |
| 基准测试 | 5 查询中 4/5 Top-5 命中，3/5 Top-2 命中 |