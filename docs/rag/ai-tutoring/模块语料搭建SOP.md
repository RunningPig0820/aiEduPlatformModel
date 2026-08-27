# 模块语料搭建 SOP（通用）

> 用途：**新模块/新功能从零搭建 RAG 语料的可复用步骤清单**。参考 AI答疑模块完整流水线（`每模块流水线-tasks.md`）+ 双池架构（`双池检索方案.md`）+ 目录结构（`docs/rag/ai-tutoring/`），提炼为通用流程。
> 适用：knowledge-graph / question-analysis / rag-system 等已有雏形模块，以及任何新功能。
> 状态：2026-08-26 沉淀。

---

## 一、产出物总览（一个模块最终要有这些）

以 AI答疑为例，最终目录形态：

```
docs/rag/<模块>/
├── <模块>.md                     # 模块主文档（问题清单/定位）
├── 1.语雀/                       # 语料①：产品意图（原始文档）
├── 2.OpenSpec design 决策/       # 语料②：设计决策（design，proposal 不入）
├── 3.代码/                       # 语料③：落地真相（代码业务分析，对账真值源）
├── 4.完善文档/                   # 合成：8节三层口径（为什么/怎么设计/落地真相 + 追问防御）
├── 5.难点/                       # 坑档案（26坑6段复盘）
├── 6.缺失补充/                   # 逻辑闭环缺口（可选）
├── 7. 引导问题/                  # 面试引导问题清单（可选）
├── 切片数据/                     # ④ 导出的人读视图（含 9 类标签）
├── 切片清单.md                   # 切片方案（哪层进/不进/权威度/切法）
├── 每模块流水线-tasks.md         # 本模块的流水线任务记录
├── 向量桶入桶清单.md             # 入桶来源/字段/分布/边界
├── 双池检索方案.md               # 全量池+切片池双索引设计
└── RAG执行计划.md                # 当前执行顺序（可选）
```

---

## 二、六步流水线（核心）

```
① 语料下载整理 → ② 文档对齐 → ③ 完善文档 → ④ 切片 → ⑤ 索引入COS → ⑥ 评测
```

### 第 ① 步：语料下载整理

**目标**：三类原始语料齐备，各自独立对齐。

| 语料类 | 目录 | 内容 | 权威度 |
|---|---|---|---|
| 产品意图 | `1.语雀/` | 产品文档/业务目标/方案讨论 | 0.7 |
| 设计决策 | `2.OpenSpec design 决策/` | 各端 OpenSpec 的 design（**proposal 不入**） | 0.7 |
| 落地真相 | `3.代码/` | 代码业务分析（**真值源**，非源码摘录） | 0.8 |

**要点**：
- `3.代码/` 是对账真值源——从代码分析出的**业务情况**，每份标 `文件:行号` 证据
- OpenSpec 只收 design（Context 已覆盖 proposal 的 Why）
- 本步产出：三目录文件齐 + `<模块>.md` 主文档

### 第 ② 步：文档对齐

**目标**：三类逐份判断"是否正确、有没有改动点"，沉淀对账。

- 语雀 vs 代码：标注 `⚠️/✅/🚫` 代码现状标记
- 产出：`OpenSpec-代码对账.md` / `方案-代码对账.md` + `5.难点/坑档案.md`（26 坑 6 段：问题现象→触发流程→根因→排查→解决→口述要点）

### 第 ③ 步：合成完善文档

**目标**：`4.完善文档/` 按"一个问题一节"合成，每节三层口径。

```
每节结构：
## 为什么（语雀）      ← 产品动机/痛点/价值
## 怎么设计（方案）    ← 技术方案/选型
## 落地真相（代码）    ← 实际实现/证据 file:line
## 追问与防御          ← 面试预期追问 + 回答要点
## 证据引用            ← 关联 3.代码 分析
```

**要点**：8 节左右（01 模块定位 / 02 完整答疑 / 03 架构 / 04 安全 / 05 数据 / 06 图片 / 07 流式 / 08 演进），每节是**一个问题的完整答案**。

### 第 ④ 步：切片

**目标**：语料 → `rag_slices.jsonl`（块）+ `切片数据/`（人读视图）。

**命令**（`cd ai-edu-ai-service`，统一 `venv/bin/python`）：
```bash
# ④ 切片：语料 → jsonl（每块 {text, summary, tags}）
venv/bin/python scripts/rag/slice_corpus.py
# ④b 生成 summary：LLM 为每块写"解决什么问题"一句话
venv/bin/python scripts/rag/gen_summaries.py
# ④c 切片审查视图：md 落盘 docs/rag/<模块>/切片数据/
venv/bin/python scripts/rag/export_slices_md.py
```

**切片方案**（`切片清单.md`）：
| 层 | 权威度 | 切法 |
|---|---|---|
| 完善文档 | 1.0 | 整文件一块 |
| 语雀 | 0.7 | 按 H2 |
| OpenSpec design | 0.7 | 按 H3 决策 |
| 代码 | 0.8 | 按 H2（**只留「业务情况」，跨三端证据/文件头不切**） |
| 坑档案 | 0.8 | 按 H3 每坑一块 |

**每块 tags 字段**：`module / category / source / authority / section / file / file_path / anchor`
- `module` = 模块闭集 id（ai-tutoring / knowledge-graph / question-analysis / rag-system）
- `category` = 9 类闭集标签（项目介绍/操作流程/数据关联/开发难点/业务流程/架构设计/业务视角/数据存储/未来演进）
- 低价值块原则：空壳（只有标题）、纯证据引用表、重复内容 → 不切

### 第 ⑤ 步：索引入 COS（双池）

**目标**：全量池 + 切片池两个独立索引，入向量桶。

**命令**：
```bash
# 全量池（语雀5+完善文档8+代码10 = 23 块整篇）
venv/bin/python scripts/rag/slice_full.py          # → rag_slices_full.jsonl
venv/bin/python scripts/rag/build_index.py --pool full --clear
# 切片池（切片数据/ 全部）
venv/bin/python scripts/rag/build_index.py --pool slice --clear
```

**前置**：COS 控制台先建 `rag-full` / `rag-slice` 索引（768 float32 cosine）；`.env` 配 `COS_VECTORS_*`。

**入桶字段**（每块）：
- key：`rag-full|rag-slice/{file}/{anchor}#{idx}`（池命名空间防冲突）
- metadata：`version / doc_type / module / category / source / authority / section / file / file_path / anchor / summary`
- **text 不进 metadata**（20KB 限制），留在 jsonl，命中后按 key 反查

### 第 ⑥ 步：评测

**目标**：定基线，验证检索质量。

```bash
venv/bin/python scripts/rag/eval_dataset.py        # 评测集校验
venv/bin/python scripts/rag/run_eval.py            # 真实检索 + doubao 生成/判分 → 报告
venv/bin/python scripts/rag/run_eval.py --compare  # 与上份对比
```

**指标**：hit@3 / 质量分 / 成本 / 耗时。

---

## 三、双池召回设计（每模块都要做）

参考 `双池检索方案.md`：

- **全量池**（完整文档）：管整体/全局问题（"是什么""架构怎么分工"）
- **切片池**（切片块）：管细节/步骤问题（"某一步怎么走""某个坑根因"）
- 查询：全量池召一次 + 切片池召一次 → RRF 融合取 Top-K；切片池可按 category 筛选
- 模块间隔离：`rag-full` / `rag-slice` 索引内按 `module` / `doc_type` 区分多模块

---

## 四、常用命令汇总

| 场景 | 命令 |
|---|---|
| 切片 | `venv/bin/python scripts/rag/slice_corpus.py` |
| summary | `venv/bin/python scripts/rag/gen_summaries.py` |
| 视图 | `venv/bin/python scripts/rag/export_slices_md.py` |
| 全量池切片 | `venv/bin/python scripts/rag/slice_full.py` |
| 建索引 | `venv/bin/python scripts/rag/build_index.py --pool full/slice --clear` |
| 查询 | `venv/bin/python scripts/rag/rag_query.py "问题" --no-gen` |
| 评测 | `venv/bin/python scripts/rag/run_eval.py` |
| 测试 | `venv/bin/python -m pytest tests/rag/ -q` |

---

## 五、数据安全提醒

- **重跑 slice_corpus 会丢手工增强段**（用源文件当前内容覆盖 jsonl）——重跑前**先备份 jsonl**，手工增强内容**先补回源文件再切**
- 新增模块 → `slice_corpus.py` LAYERS 加一层（按模块闭集 id），`build_index.py` 多池写入
- 重建索引前备份；`--clear` 幂等

---

## 六、新模块落地检查清单

- [ ] `docs/rag/<模块>/` 目录建齐（1.语雀/2.OpenSpec/3.代码/4.完善文档/5.难点/[6.缺失补充]/[7.引导问题]）
- [ ] `3.代码/` 业务分析完成（文件:行号 证据）
- [ ] `5.难点/坑档案.md` 完成（6 段复盘）
- [ ] `4.完善文档/` 每节三层口径完成
- [ ] `切片清单.md` 定稿（哪层进/不进/权威度/切法）
- [ ] `slice_corpus.py` LAYERS 加模块层 → 切片 → summary → 视图
- [ ] jsonl 每块含 `module` + `category`（9 类）
- [ ] `slice_full.py` 全量池 → `build_index --pool full/slice` → 入桶
- [ ] `rag_query.py` 查询验证（整体命中全量池、细节命中切片池）
- [ ] `run_eval.py` 评测定基线
- [ ] `向量桶入桶清单.md` + `每模块流水线-tasks.md` 归档
