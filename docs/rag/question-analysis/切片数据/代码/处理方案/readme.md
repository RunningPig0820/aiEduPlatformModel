# 切片数据 / 代码 / 处理方案

> 本来源（3.代码 分析文档）从源文档到切片数据的完整处理路径，按数据整理步骤记录。
> 脚本统一用 `../脚本代码/`（顶层，切割通用脚本留档；运行时源在 `ai-edu-ai-service/scripts/rag/`）。

## 步骤一：源头（语料就绪）

- 源文档：`3.代码/分析-01~10.md`（10 份，权威 0.8，代码证据层，8 节改良结构）
- 生成提示词：`3.代码/处理方案/提示词/代码深读-分析文档-提示词.md`（真读代码/三端核对/业务场景先行/元数据锚点）
- 前提：分析文档已按 Phase 6 规范化（业务描述与业务场景先行 + 8 节固定结构 + 文件头 5 行标准）

## 步骤二：切片（md → jsonl）

```bash
cd ai-edu-ai-service && venv/bin/python scripts/rag/slice_corpus.py --module question-analysis --sources 代码
```

- 脚本：`切片数据/脚本代码/slice_corpus.py`（已 `--module` 参数化，`--sources 代码` 只切代码层）
- 切法：**split_level=2 按 h2 切**，一节一块 → 每份文档 9 块（标题 + 8 个 h2 节）
- 本次结果：10 份 → **90 块**（全切不删；若后续删低价值块，从「已读代码清单」等索引块开始）
- 输出：`ai-edu-ai-service/scripts/rag/data/rag_slices-question-analysis.jsonl`
- 规则约束（SOP 第④步·切片注意事项）：≤6000 字符按段落拆不丢尾部；表格/代码块/mermaid 不切破；块元数据 `doc_type=code_analysis + authority=0.8 + source=代码`

## 步骤三：块级 summary（可选，检索质量提升）

```bash
cd ai-edu-ai-service && venv/bin/python scripts/rag/gen_summaries.py
```

- 脚本：`切片数据/脚本代码/gen_summaries.py`（通用，无模块硬编码）
- 用途：为每块自动生成"解决什么问题"一句话 summary（当前视图 `(无 summary)`）
- 约定：代码层**不强制**每 `###` 手写检索摘要，summary 由本脚本生成，不手工回写 md 头

## 步骤四：导出视图（jsonl → 人读 md）

```bash
cd ai-edu-ai-service && venv/bin/python scripts/rag/export_slices_md.py --module question-analysis
```

- 脚本：`切片数据/脚本代码/export_slices_md.py`（已 `--module` 参数化）
- 输出：本目录 `../` 下 `代码/` 90 个块文件（每块带 summary/权威度/来源/锚点/模块/节 头）
- 幂等：只清旧切片块文件，**保留 readme.md / README.md / 处理方案/ 骨架**

## 步骤五：检索侧规则（入桶/查询时生效）

- code_analysis 只答**接口/参数/降级/对账翻转/代码真实行为**；不答"为什么这么设计/选型权衡"（canonical 决策职责）——RAG 系统 prompt 按 doc_type 做来源过滤
- 全量池：完善文档 1.0 整篇（`slice_full.py`，待参数化）| 切片池：本层 90 块 + 语雀/坑档案/引导问题

## 其它脚本（旁路工具，暂未用）

| 脚本 | 用途 | 通用性 |
|---|---|---|
| `md_to_jsonl.py` | 切片数据 md → jsonl（"切归切、改归改"） | ⚠️ CORPUS 写死 ai-tutoring，解析逻辑通用 |
| `recover_slices.py` | 切片恢复 | ⚠️ MD_DIR 写死 ai-tutoring |
| `slice_full.py` | 全量池 jsonl（完善文档 1.0） | ⚠️ CORPUS/module 写死 ai-tutoring，QT⑦ 前置需参数化 |