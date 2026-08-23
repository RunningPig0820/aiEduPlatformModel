## Why

需要一个能**证明 RAG 能力**、又能**给面试官讲清每个项目页面**的问答系统。现有模块（知识图谱 / AI答疑 / 组织中心 / 学生知识点分析）有真实设计与实现，但语雀文档大量是空模板、方案文档多版本矛盾、部分未发布——**无法直接支撑"讲清楚每一页"**。构建一个项目介绍 RAG 问答系统：以自己完善后的方案/设计文档为语料，用一套真实的 RAG 链路（文档准备 → 嵌入 → 向量桶 → 多路召回 → 打分 → 生成 → 展示，外加权限/降级/成本）现场回答面试官关于任意页面的提问。

## What Changes

- **文档准备（语料治理）**：收集语雀文档 + 代码注释 + OpenSpec → 人工完善成每模块一份「完善版设计文档」（产品定位/核心功能/为什么/数据流转含 mermaid/技术实现/关键坑/规模指标/权限边界）→ 按章节切片 + 标注 metadata（页面/问题类型/角色权限/源文档全文）→ embedding（dashscope text-embedding-v3, 768 维）→ 写入 COS 向量桶 `rag-index`。
- **双池检索**：索引层池（每页 5~8 条预写 QA：问题+答案要点+引用）+ 源文档池（完善文档全文，纯 RAG）。**页面锚定**：前端主动传 `page`，页面模式锁页检索 / 全局模式跨页检索。多路召回 = 向量 + BM25（jieba 关键词）。
- **两道门**：**权限门**（进会话时按当前页权限点前置校验）+ **范围门**（检索置信度低于阈值 → 边界回答，不硬编）。
- **生成与引用**：doubao 流式生成；**强制带引用**，跨页时按页面分别标注来源；回答附「召回文档原文」面板。
- **成本展示**：token **真算**（usage，流结束更新），每轮 prompt/completion + 累计 + ¥ 换算，embedding tokens 单列。
- **流程图**：每模块预置 mermaid 数据流图，命中"数据流"类问题直接渲染；未预置才动态生成兜底。
- **会话**：页面锚定会话，追问上限 5 轮，超限提示开新会话。
- **降级**：逐环节降级矩阵（embedding→关键词；COS→关键词兜底；LLM→展示召回原文/预写答案；全挂→边界话术）。
- **测试**：每个关键阶段配测试（文档切片 / embedding 维度 / 双池召回 / 页面锚定 / 范围门 / 权限门 / 引用生成 / usage 解析 / 降级）。
- **RAG 本身作为项目功能点**：在项目介绍中 RAG 能力本身也是一个可介绍的模块。

## Capabilities

### New Capabilities
- `rag-corpus`: 语料治理（完善文档）、切片与 metadata、embedding、COS 向量索引构建
- `rag-retrieval`: 双池多路召回、页面锚定、打分、范围门
- `rag-permission`: 权限门前置校验（页面权限点 vs 角色）
- `rag-generation`: doubao 生成、强制引用（按页标注）、token usage 真算与成本展示
- `rag-resilience`: 重试与降级矩阵、会话追问限制、边界话术

### Modified Capabilities
<!-- 无既有 spec 需求变化：cost-tracker / llm-gateway 需求与本变更不冲突 -->

## Impact

- **新增模块**：`core/rag/`（corpus / retrieval / permission / generation / resilience）
- **修改**：
  - `core/tutoring/ark_stream.py`：请求体加 `stream_options: {"include_usage": true}` + 解析结尾 usage chunk
  - `core/tutoring/vector_store.py`：`embed()` 抓 `resp.usage.total_tokens`；`COS_VECTORS_INDEXES` 启用 `rag: "rag-index"`
- **配置**：`config/settings.py` 增加完善文档目录、RAG 索引路由、RAG 生成模型/温度
- **API**：新增 `/api/rag/*` 内部端点（Java↔Python，需 `x-internal-token`）
- **依赖**：无新增（dashscope / COS SDK / doubao / jieba 均已就绪）
- **文档**：`docs/project-intro-rag-notes-2026-08-21.md`（设计纪要，本变更的依据）
