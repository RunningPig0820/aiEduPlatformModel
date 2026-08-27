# 知识图谱 模块流水线任务

> **来源**：`docs/rag/question-analysis/模块语料搭建SOP.md`（题型知识点，方法论同源）+ `docs/rag/ai-tutoring/每模块流水线-tasks.md`（流水线流程模板，本项目跑 ai-tutoring/question-analysis/knowledge-graph 三条线）
> **语料多类，各自独立对齐**：`1.语雀`（产品意图）｜`2.OpenSpec design 决策`（设计决策）｜`3.代码`（落地真相，**对账的真值源**——从代码分析出的**业务情况**，非源码摘录）
> **流程**：`① 语料下载整理 → ② 文档对齐 → ③ 完善文档 → ④ 切片 → ⑤ 索引 → ⑥ 评测`
> **当前进度（2026-08-27）**：
> - ✅ 目录骨架 + 全套提示词 + SOP + 本任务文件（本轮已完成）
> - ✅ 语料原料在位：`1.语雀` 35 份 + `2.OpenSpec design 决策` 26 文件（13 design + 13 proposal）+ `knowledge-graph.md` 主文档（5 段）
> - ⏳ ① 语料整理（35 语雀归档 + canonical 6 份）、② 对账、③ 完善文档、④ 切片、⑤ 索引、⑥ 评测

---

## 0. 流水线总览（流程图 + 怎么用）

### 0.1 流程图

```
                     ┌────────────────────────────────────────────────────────────┐
                     │                  知识图谱 RAG 流水线                          │
                     └────────────────────────────────────────────────────────────┘

 ┌─────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
 │ ① 语料下载整理 │──▶│ ② 文档对齐     │──▶│ ③ 完善文档     │──▶│ ④ 切片         │──▶│ ⑤ 索引入 COS   │
 └─────────────┘   └──────────────┘   └──────────────┘   └──────────────┘   └──────┬───────┘
   语雀 35 份        方案 vs 代码       9 节三层口径     提示词+大模型语义分组   │  全量池+切片池
   spec 26 份        → 对账翻转        为什么/怎么设计/   → 代码双切片60        build_index.py
   (13 design        → 坑档案 J-KG#    落地真相            → 语雀按条目           --module
   +13 proposal)                         + 追问与防御        → OpenSpec按###       knowledge-graph
   代码分析 10 份                         + 证据引用          → 坑双切片            不带 --clear
   (edukg+桥+Java+                                                                 ▼
    前端)                                                                            ┌──────────────┐
 ╔══════════════════════════════════════╗                                            │ ⑥ 评测         │
 ║   运行时只走：④→⑤→⑥ + 查询           ║                                            └──────┬───────┘
 ║   查询: rag_query.py / API            ║                                             run_eval.py
 ║   评测: run_eval.py                   ║                                             → 基线报告
 ╚══════════════════════════════════════╝
```

**运行时链路**（语料已建成后，日常只碰这几条）：

```
面试官问题
  → POST /api/rag/query (module=knowledge-graph)
  → [召回] 向量(COS rag-full/rag-slice, module 过滤) + BM25(本地 jsonl)
  → [编排] RRF × 权威 × 锚定 → top-K
  → [生成] doubao 面试口述 + 引用
```

### 0.2 怎么用（端到端命令）

> 全部命令在 `ai-edu-ai-service/` 下执行；**统一用 `venv/bin/python`**（不要用系统 python，见 CLAUDE.md 环境警告）。

**前置**：COS 向量桶 `rag-1318177119/rag-full`、`rag-slice` 已在控制台建好（768 float32 cosine，与 ai-tutoring/question-analysis 共用）。`.env` 配好 `COS_VECTORS_*`、`NEO4J_URI`。

#### A. 首次建链（一次性，①~⑤）
```bash
cd ai-edu-ai-service

# ① 语料整理：35 语雀 → 原来的文件/ 归档 → canonical 6 份（用 1.语雀/处理方案/提示词/）
# ② 对账：方案-代码对账.md（翻转项）
# ③ 代码深读：edukg + ai-service + Java + 前端 → 3.代码/分析-01~10.md（用 3.代码/处理方案/提示词/代码深读-分析文档-提示词.md）
# ④ 完善文档 9 节：4.完善文档/01~09.md（用 4.完善文档/处理方案/提示词/完善文档-生成-提示词.md）
# ⑤ 切片：提示词 + 大模型语义分组 → 切片数据/ 各来源切片/（代码双切片/坑双切片/引导逐问/语雀条目/OpenSpec ###）
# ⑥ 引导问题：7. 引导问题/问题列表.md → guide_pool.py GUIDE_POOL["knowledge-graph"] 同步

# ⑦ 入库（四步）：
venv/bin/python scripts/rag/knowledge-graph/01_slice_jsonl.py      # 分库 → rag_slices-knowledge-graph.jsonl
venv/bin/python scripts/rag/knowledge-graph/02_full_jsonl.py       # 全量库 → rag_slices_full-knowledge-graph.jsonl
venv/bin/python scripts/rag/upload_cos.py --root docs/rag/knowledge-graph   # 内容上传 COS 普通桶
venv/bin/python scripts/rag/build_index.py --module knowledge-graph --pool full   # 不带 --clear
venv/bin/python scripts/rag/build_index.py --module knowledge-graph --pool slice  # 不带 --clear

# ⑧ 评测：
venv/bin/python scripts/rag/eval_dataset.py        # 评测集校验
venv/bin/python scripts/rag/run_eval.py --compare  # 真实检索 + 生成/判分 → 报告
```

#### B. 日常（语料已建成后）
```bash
venv/bin/python scripts/rag/rag_query.py "知识点怎么匹配进图谱" --no-gen   # 查询验证（module=knowledge-graph）
venv/bin/python -m pytest tests/rag/ -q                                   # 回归
```

---

## 1. 语料下载整理（当前进行中 ⏳）

### 1.1 现状

| 语料类 | 目录 | 现状 |
|---|---|---|
| 产品意图 | `1.语雀/` | ✅ 35 份原始（未归档）；⏳ canonical 6 份待产出 |
| 设计决策 | `2.OpenSpec design 决策/` | ✅ 13 design + 13 proposal 在位；⏳ 评估归档 + design-*.md 成文 |
| 落地真相 | `3.代码/` | ⏳ 分析-01~10 待代码深读产出 |
| 模块主文档 | `knowledge-graph.md` | ✅ 5 段面试问题；⏳ 扩 9 视角 |

### 1.2 第①步执行清单（35 语雀 → 原来的文件/ + canonical）

- [ ] `1.语雀/原来的文件/` 下归档 35 份原始语雀（`mv 1.语雀/语雀-*.md 1.语雀/原来的文件/`，注意保留 canonical 6 份）
- [ ] 汇总 `语雀-方案总揽.md`（正式综述，去问答口吻，13 节，权威 0.8）
- [ ] 用 `1.语雀/处理方案/提示词/` 8 个独立单任务生成：决策记录（D#）/ 方案选型对比（选型#）/ 演进时间线（阶段#）/ 边界场景清单（场景#）/ 术语对照表
- [ ] 跑 `语雀-文档校验器-提示词.md` 独立校验（可选质量门）

### 1.3 第①步 spec 评估清单（26 文件）

- [ ] 看 13 design → 找每个 spec 解决什么问题（问题地图）
- [ ] 评估价值 → 13 proposal 全归档（同源精简版，Why 被 design Context 覆盖）
- [ ] 13 design 归档 `原来的文件/` → 双轨：①`spec信息补充提示题.md` 收敛事实折入语雀 canonical（决策/选型/场景/演进增量）②`spec文件整理.md` 每份 design 各自成文 `design-*.md` 进池（权威 0.7）
- [ ] `design-python-2026-04-10-knowledge-graph-data-research.md`（90KB）按 ### 切子块

## 2. 文档对齐（✅ 2026-08-27 完成）

- [x] 代码深读（4 agent 并行，多端一起读）→ `3.代码/分析-01~11.md`（11 份，落地真相 + 文件:行号 + 业务描述与业务场景先行）
- [x] 方案 vs 代码 → `方案-代码对账.md`（24 项对账：匹配评审系统方案有/代码无、状态存储翻转、前置融合未接入、年级倒置惩罚不存在、匹配率批次差异等）
- [x] `5.难点/坑档案.md`（J-KG1~12，12 条真坑，真挖三端 git log + git commit + 文件:行号 双证据；剔除 4 条无证据候选）

## 3. 完善文档 9 节（✅ 2026-08-27 完成）

- [x] `4.完善文档/01~09.md`（权威 1.0 前置校验：方案素材 + 代码真值缺一降 0.8；整篇禁切；文件头 5 行标准）——9 agent 并行,五段结构齐全,翻转标注到位
- [x] 差异区厚写：05 推断匹配（阈值/投票权重）、06 前置依赖（三来源权重）、09 业务闭环（端到端全景 + GraphRAG 落地）

## 4. 切片（✅ 2026-08-28 完成）

- [x] 代码层双切片：`切片-开发向-提示词.md` + `切片-分组-提示词.md` → 11 份分析 71 文件（开发向+面试向，target 区分，超长拆 -2/-3）
- [x] 坑档案双切片：`坑档案-切片-提示词.md` → 12 坑 24 文件（开发向+面试向）
- [x] 引导问题问答切片：`引导问题-切片-提示词.md` → 64 问 64 文件（权威 1.0 合成问答，翻转如实标注）
- [x] 语雀按条目切：`语雀-切片-提示词.md` → 9 canonical 98 块（D#/选型#/场景#/阶段#/总揽 h2/术语整表 + 数据源/课标/匹配优化）
- [x] OpenSpec 按 ### 切：`OpenSpec-切片-提示词.md` → 12 design 242 块（0.7，data-research 拆 #### 子块）
- [x] 切片清单核对块数（代码 71/坑 24/语雀 98/OpenSpec 242/引导 64）、类别闭集、头部精简 5 行 + 各切片目录 readme 落位

## 5. 引导问题（✅ 2026-08-28 完成）

- [x] `7. 引导问题/问题列表.md`（9 视角 64 问，纯问题，带 `<!--tag:{视角}-->`）+ `引导问题.md`（问答表）
- [x] 同步 `guide_pool.py` 的 `GUIDE_POOL["knowledge-graph"]`（视角→组映射 intro=项目介绍7/operation=操作流程+业务流程14/data_relation=数据关联+数据存储15/difficulty=开发难点+架构设计+业务视角+未来演进28/rag=GraphRAG+向量+query.py 桥接5；scope 去重 64 问对齐问题列表）→ 引导单测 14 passed

## 6. 索引入 COS（⏳）

- [ ] summary 分级：语雀 6 详细版 / 代码 10 + 完善 9 锚点版
- [ ] `scripts/rag/knowledge-graph/01_slice_jsonl.py` + `02_full_jsonl.py`
- [ ] `upload_cos.py --root docs/rag/knowledge-graph` → 内容上传普通桶
- [ ] `build_index.py --module knowledge-graph --pool full|slice`（**不带 --clear**，共用索引增量并入）
- [ ] `query.py` MODULE_DATA 确认加 `knowledge-graph` 映射
- [ ] 元数据审计（module=knowledge-graph / ≤2048B / 键唯一性）+ `向量桶入桶清单.md` 归档

## 7. 评测（⏳）

- [ ] `scripts/rag/data/eval/knowledge-graph.jsonl`（≥5 条，expected_references 按 file 对齐）
- [ ] `run_eval.py --compare` 跑基线（hit@k / 质量分 / 成本 / 耗时）
- [ ] `向量桶入桶清单.md` + `每模块流水线-tasks.md` 归档

---

## 附：执行顺序实录（首轮，2026-08-27 起，逐项打勾）

| 步骤 | 状态 | 做了什么 | 关键经验 |
|---|---|---|---|
| 目录骨架+提示词+SOP+任务 | ✅ | 与 question-analysis 同构建齐 | 参考 question-analysis 全套提示词适配知识图谱 |
| ① 语雀归档 + canonical 6 份 | ⏳ | 35 份 → 原来的文件/ + 总揽 + 5 canonical | 先汇总成综述再进语料；决策/选型迁出独立文档 |
| ② spec 评估 + 双轨 | ⏳ | proposal 归档 + design-*.md 成文 | spec 先价值评估再处置 |
| ③ 代码深读 10 份 | ⏳ | edukg+桥+Java+前端 → 分析-01~10 | 多端一起读，业务场景先行 |
| ④ 对账 + 坑档案 | ⏳ | 方案-代码对账.md + J-KG# | 落地真相先行 |
| ⑤ 完善文档 9 节 | ✅ | 为什么→方案→落地真相→追问→证据（9 agent 并行） | 1.0 前置校验，整篇禁切 |
| ⑥ 引导问题 + guide_pool | ✅ | 问题列表 9 视角 64 问 + GUIDE_POOL 同步（scope 去重 64） | 只放问题不写答案 |
| ⑦ 切片 5 来源 | ✅ | 代码双切 71/坑双切 24/引导逐问 64/语雀条目 98/OpenSpec### 242 | 提示词 + 大模型语义分组（30 agent 并行） |
| ⑧ 入库 + 建向量 | ⏳ | jsonl → upload_cos → build_index --module | 共用索引不带 --clear |
| ⑨ 评测 | ⏳ | eval 集 + run_eval 基线 | 定基线验证检索质量 |
