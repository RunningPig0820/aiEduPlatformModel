## Why

`project-intro-rag` 的第一步是**整理知识库**（模块逐个产出完善文档），但"整理得好不好、检索准不准、答案质量如何"目前**无法观测**。需要一个**可观测的评测 agent**：跑评测集、算命中率/答案质量/成本/耗时、输出观测报告，驱动知识库逐个模块迭代——用数据证明效果，而不是凭感觉。

## What Changes

- **知识库整理流程**：列出项目模块清单（知识图谱 / AI答疑 / 题型知识点 / 组织中心 / RAG 问答系统），**逐个**产出完善文档 → 切片 → 嵌入 → 索引，每个模块完成后进入评测，状态可跟踪（待整理/已整理/已评测）。
- **评测 agent**：加载评测集（每模块 5 条 Q&A，共 20+ 条），跑检索 + 生成，用 LLM 判定答案质量，计算指标：`hit@k`（召回命中）、`answer_quality`（答案质量分）、`cost`（成本）、`latency`（耗时）。
- **可观测评测**：每轮 trace（检索路径/得分/引用/token）、指标聚合、评测报告（可对比不同模块/不同版本语料的效果）。
- **每个阶段可测试**：知识库整理、评测 agent、观测输出均配测试。

## Capabilities

### New Capabilities
- `kb-organization`: 知识库整理流程（模块清单、完善文档产出、切片/索引、状态跟踪）
- `eval-agent`: 评测 agent（评测集执行、LLM 答案质量评判、指标计算）
- `eval-observability`: 可观测评测（trace、指标聚合、评测报告展示）

### Modified Capabilities
<!-- 无既有 spec 需求变化。复用 project-intro-rag 的 rag-corpus（切片/嵌入/索引） -->

## Impact

- **新增模块**：`core/rag/eval/`（agent / metrics / observability）+ 完善文档语料目录（`docs/project-intro/corpus/<module>.md`）
- **复用**：`project-intro-rag` 的 rag-corpus（切片器、embedding、COS 索引）
- **配置**：`config/settings.py` 增加完善文档目录、评测集路径、判分模型
- **API**：新增 `/api/rag/eval/*`（评测运行 + 评测报告），`x-internal-token` 鉴权
- **依赖**：无新增（doubao / dashscope / COS / jieba 均就绪）
- **文档**：`docs/project-intro-rag-notes-2026-08-21.md`（总纪要，本变更对齐其"评估集 20 条 Q&A"待定项）
