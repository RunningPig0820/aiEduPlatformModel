# 切片数据 / 代码 / 处理方案

> 本来源（3.代码 分析文档）从源文档到**切片数据**的完整处理路径，按数据整理步骤记录。
> **本次范围 = 分片（切片 jsonl + 人读视图 + 质量查询），不做入桶**（QT⑦ 入桶/检索规则另行处理）。
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

## 步骤五：分片质量查询（切片后验证可检索性）

> 分片后**查询分片质量**——用 `rag_query.py` 跑代表性问题，验证切片块能被命中、命中块语义是否对题。质量差则回头改切片/补 summary，不急于入桶。

```bash
cd ai-edu-ai-service && venv/bin/python scripts/rag/rag_query.py --module question-analysis "题型识别错了怎么办" --pool slice
```

- 脚本：`切片数据/脚本代码/rag_query.py`（检索 CLI，需先有索引；**无索引时用目录内 jsonl 直接核对**，见下）
- 无索引时的替代质量检查（分片阶段，未入桶）：
  1. **命中度粗查**：用关键词 `grep -n "关键词" docs/rag/question-analysis/切片数据/代码/*.md` 看该主题是否落在应有块（如"题型识别错了"→ 分析-04 业务场景/隐性坑块）——检验"问题的答案块存在"
  2. **块语义抽读**：抽 3~5 块人读，确认 ①正文与锚点标题一致 ②表格/代码块没被切破 ③mermaid 链路在正文有文字复述（embedding 可读）
  3. **长度检查**：块长度 300~1500 字为宜；过短（<100）无检索价值、过长（>6000）需段落拆（切片器已自动处理）
- 质量达标标准：代表性问题（业务/接口/降级各 1 条）能定位到对应块，且块内容自包含可回答

## 步骤六：入桶（QT⑦，本次不做）

> 本次范围停在**分片**（上述步骤一到五产出切片 jsonl + 视图 + 质量核验）。入桶是 QT⑦ 的职责，此处仅留规则备忘，不执行：

- **切片池（rag-slice）**：本层 60 块（doc_type=code_analysis，0.8，删低价值块后）→ `build_index.py --module question-analysis --pool slice`
- **全量池（rag-full）**：完善文档 1.0 整篇（`slice_full.py`，待参数化）→ `--pool full`
- **检索规则**：code_analysis 只答接口/参数/降级/对账翻转/代码真实行为；不答"为什么这么设计/选型权衡"（canonical 决策职责）——RAG 系统 prompt 按 doc_type 做来源过滤

## 其它脚本（旁路工具，暂未用）

| 脚本 | 用途 | 通用性 |
|---|---|---|
| `md_to_jsonl.py` | 切片数据 md → jsonl（"切归切、改归改"） | ⚠️ CORPUS 写死 ai-tutoring，解析逻辑通用 |
| `recover_slices.py` | 切片恢复 | ⚠️ MD_DIR 写死 ai-tutoring |
| `slice_full.py` | 全量池 jsonl（完善文档 1.0） | ⚠️ CORPUS/module 写死 ai-tutoring，QT⑦ 前置需参数化 |