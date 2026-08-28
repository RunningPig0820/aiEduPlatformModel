# milestone-03-recall-rerank Specification

## Purpose

M3 交付"多路召回 + remark 打分 + 边界拒答"切片——向量 + BM25 双路召回（单路 2s 超时降级）、RRF 融合 Top-K 精排、范围门低置信度过滤（唯一拒答路径）。三者共享同一次 `orchestrate()` 的 rerank 产物，作为"检索质量"一个完整纵向切片交付；generate 仍以桩替占位，前端可对召回块面板与边界拒答话术做对接。

## ADDED Requirements

### Requirement: 多路召回与超时降级

M3 SHALL 交付双路召回：向量（COS）+ BM25（本地 jsonl），单路 2s 硬超时 → 降级为纯另一路（`{hits:[], confidence:0}` 捕获，degraded 标记），链路不中断。四模块全放行无禁区，语料有无由数据驱动。**按 anchor 选语料池**：模块级 anchor 决定召回目录（多模块语料），orchestrate 入参加 corpus 参数，节级 authority × lockedSections 锚定加权逻辑保留不改。

#### Scenario: 双路召回

- **WHEN** 学生提问命中 AI答疑语料
- **THEN** 向量 + BM25 两路均召回，前端可见召回块

#### Scenario: 单路超时降级

- **WHEN** 向量路超时（>2s）
- **THEN** 降级纯 BM25，degraded 标记，链路继续不报错

#### Scenario: 四模块全放行

- **WHEN** 学生提问指向任意模块（AI答疑/知识图谱/题型分析/RAG）
- **THEN** 正常路由进入召回，无意图层禁区硬拒答

### Requirement: RRF 精排 Top-K 与 remark 打分

M3 SHALL 交付 remark 打分：RRF 融合（RRF_K=60）精排，默认 Top-K=3，仅回传精排后块（blockId/title/summary/filePath/score），不吐全量召回。前端按 rerank 事件渲染召回块面板，块支持点击查看原文（file_path）。

#### Scenario: 精排块展示

- **WHEN** 召回完成并 RRF 精排
- **THEN** rerank 事件携带 Top-3 精排块（标题/摘要/file_path/score），前端面板展示

#### Scenario: 全量召回不外泄

- **WHEN** 召回原始结果 >Top-K
- **THEN** 前端仅收到精排后 Top-K 块，原始召回列表不暴露

### Requirement: 查看原文 Java 代理

M3 SHALL 交付查看原文代理：`GET /api/rag/assistant/source?path=<urlencoded>`（STUDENT 角色门）转发 Python `/api/rag/source/{file_path}` 返回原文；file_path 走 **query 传参**（不走 path，避免特殊字符被容器拒）；原文不存在 → 10002。前端**不直连 Python**（Python 保留挂载作 Java 转发目标）。

#### Scenario: 查看原文

- **WHEN** 前端点击 rerank 块 filePath
- **THEN** 调 `GET /api/rag/assistant/source?path=<encoded>`，Java 转发 Python 返回原文

#### Scenario: 原文不存在

- **WHEN** file_path 无对应源文件
- **THEN** 返回 10002 原文不存在

### Requirement: 范围门低置信度过滤（边界拒答）

M3 SHALL 交付边界拒答：RRF 精排综合分低于阈值（索引层 0.75 / 源文档池 0.5）→ `boundary` 事件（reason=low_confidence），固定话术"未找到关联文档，我尚未掌握"，0 生成 token。这是唯一拒答路径。

#### Scenario: 无语料模块低置信过滤

- **WHEN** 学生提问指向无语料模块（如知识图谱，语料缺失）
- **THEN** 正常召回但命中为空 → boundary（reason=low_confidence）固定话术，无生成 token

#### Scenario: 语料未覆盖低置信过滤

- **WHEN** 问题为语料未覆盖的边角内容，综合分低于阈值
- **THEN** boundary（reason=low_confidence）固定话术，无生成 token

### Requirement: 里程碑对接测试验收

M3 SHALL 以召回块展示 + 边界拒答 + 桥实现用例作为完成标准：RAG-SSE-002/003（低置信过滤时序）、RAG-BRIDGE-001~003（SSE 消费/异常冒泡/degraded 200）、RAG-COST-002（边界路径 0 生成 token）。generate 桩替在 M3 仍保留。

#### Scenario: 对接测试全绿

- **WHEN** 前端完成召回块面板与边界话术对接，后端桥 mock 召回/边界流
- **THEN** RAG-SSE-002/003、RAG-BRIDGE-001~003、RAG-COST-002 通过，M3 视为完成

#### Scenario: 前端可见物

- **WHEN** 学生提问命中语料
- **THEN** 前端召回块面板展示精排块（可点击查看原文）；未命中 → 边界拒答话术
