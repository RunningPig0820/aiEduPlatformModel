# AI答疑 模块流水线任务

> **来源**：`openspec/changes/rag-eval-agent/tasks.md`（流水线流程模板，本项目只跑 AI答疑 一条线）
> **语料三类，各自独立对齐**：`1.语雀`（产品意图）｜`2.OpenSpec design 决策`（设计决策）｜`3.代码`（落地真相，**对账的真值源**——从代码分析出的**业务情况**，非源码摘录）
> **流程**：`① 语料下载整理 → ② 文档对齐（三类逐份判断正确性/改动点）→ ③ 完善文档（8节）→ ④ 切片 → ⑤ 索引 → ⑥ 评测`
> **当前进度（2026-08-24）**：
> - ✅ ① 语料下载：`1.语雀`（5篇）+ `2.OpenSpec design 决策`（**22 文件**，已删 8 个低价值前端 UI）+ `3.代码` 业务分析（**10 份，2026-08-24**）
> - ✅ ② 文档对齐（`1.语雀` 33处 + `3.代码` 10 分析 + `坑档案` 26 坑 + `OpenSpec-代码对账` 22 份）→ ✅ ③ 完善文档 8 节（`4.完善文档/01~08`，2026-08-24）→ ⬜ ④ 切片 → ⑤ 索引 → ⑥ 评测

---

## 1. AI答疑 语料与完善文档

### 1.1 语料下载整理
- [x] `1.语雀` 5 篇策展入库（`语雀-AI答疑 / ai回答 / 使用agent还是流程 / 方案设计 / 流程控制会让agent混乱`）
- [x] `2.OpenSpec design 决策` 30 文件入库（15 design + 15 proposal，含归档 `tutoring-agent-protocol`）
- [x] `3.代码` 业务分析 10 份落盘（**2026-08-24**：从代码分析业务情况，非源码摘录；对账的"真值源"，见 1.2）

### 1.2 代码业务分析 → `3.代码/`
**不是写代码/摘源码**——从真实代码里**分析出业务情况**（业务怎么跑、规则数字、数据怎么流），每份分析标注 `文件:路径:行号` 证据引用。
**目的**：对账（1.3c/1.3d）判定"方案是否正确、改动点在哪"的真值源；**不进 RAG 正文切片**——面试官要的是介绍（完善文档），代码只作证据引用。
**跨三端**：每条主题 = 一条 **前端(`aiEduPlatformFront`) → 后端(`aiEduPlatform`) → Python(`aiEduPlatformModel`)** 的链路，证据分别标注三端 `文件:路径:行号`，只看一端就断链。
例：主题① 前端 `AiQa.jsx`/`useTutoringSession.js` → 后端 `TutoringController`/`TutoringAppService` → Python `decide`/`generate` 端点。
分析 10 个主题（覆盖 `ai-tutoring.md` 问题表全部问题点）：
- [x] ① 一次答疑完整流程（学科门→decide→护栏→落库→generate 流式→收尾）
- [x] ② 微服务分工（Java 管认证/护栏/数据，Python 管 decide/generate 纯智能，前端管交互）
- [x] ③ 防作弊机制（答案护栏 reveal 两次 + 轮次护栏 20 + 安全过滤）
- [x] ④ 学科门（subject-classify 判学科，非 math 不建/不续会话、不耗轮次）
- [x] ⑤ 判对逻辑（decide 两分法 + end 收紧三类 + reveal 门禁）
- [x] ⑥ 图片题处理（图片直传 COS→多模态 doubao 看图 + OCR 双通道开关）
- [x] ⑦ 掌握度与数据流（题型 canonical→ScoreMapper 累计 + 题目表 + 错误事件 B3 门控 + 澄清卡 resolve/vote）
- [x] ⑧ 会话与存储（Redis+MySQL+COS 三层、断点恢复、历史会话、删除软删）
- [x] ⑨ 流式与性能（SSE 类型先行 meta/token/done + agent 事件 + thinking + 关思考延迟）
- [x] ⑩ 工程韧性（会话并发锁 45s、创建频率限制、降级兜底 network/degraded）
- [x] 每份分析结尾标注证据 `文件:路径:行号`（供对账/完善文档引用，**不切片**）——落盘 `3.代码/分析-01~10-*.md`

### 1.3 文档对齐（三类逐份判断"是否正确、有没有改动点"）
**不能默认语料是对的。三类分别对齐，逐份判断，最后合成对账汇总。**
- [x] 1.3a **合成 `方案-代码对账.md`**（差异汇总 + 每处"方案写了什么 / 代码实际怎样 / 完善文档怎么写"）
      > **初版已产出**（前端入口→后端代码→对照方案，圈出 3 处口径差异）；1.3b 语雀对齐已并入 1.语雀 各篇。待补：1.3c OpenSpec 逐份 + 1.3d 代码引用后回填对账
- [x] 1.3b **对齐 `1.语雀` 5 篇**：逐篇标注 `保留 / 过时(修正为代码真相) / 演进故事(规划未落地)`。
      **已完成（2026-08-24）**：5 篇共 33 处标注。方案设计 16｜流程控制 5｜AI答疑 5｜ai回答 4｜使用agent还是流程 3。
      主要过时点已标：MongoDB→三层存储 ｜ 三级意图→学科门+两分法 ｜ 知识点确认→低置信澄清卡 ｜ 题库/行为风控/画像→🚫规划 ｜ 换题≠开新会话 ｜ 判定权回 Java ｜ Python=L0 两端点非 LangGraph
- [x] 1.3c 前置：**分析文档价值 + 删除不重要设计**（已完成 2026-08-24）——按 README 问题框架评估 30 个设计 → A级7/B级4/C级8，删除 8 个低价值前端 UI 设计（能力已被保留设计覆盖）
- [x] 1.3c **对齐 `2.OpenSpec` 22 文件**（剩 A级7+B级4 变更 × design/proposal）：逐份对照代码，标注 `一致 / 有改动点`。
      **已完成（2026-08-24）**：落盘 `OpenSpec-代码对账.md`——22 份总览表 + 11 变更差异明细。结论：✅一致 9 份｜⚠️有改动点 13 份。
      4 个贯穿差异：掌握度主体=题型(ScoreMapper 累计)非 URI/单调不减 ｜ OCR=兼容双通道(主通道直传看图) ｜ 模型全链路统一 doubao mini ｜ 学科闭集 K12 十值
> 1. 分析文档价值 
   我们先梳理客户想要问什么 /Users/minzhang/Documents/work/ai/aiEduPlatformModel/docs/rag/README.md

  我们在看 /Users/minzhang/Documents/work/ai/aiEduPlatformModel/docs/rag/ai-tutoring/2.OpenSpec design
  决策 并不是所有的设计都是重要的

  可以看一下 这些设计的重要程度 
  2.  删除不重要的设计

- [x] 1.3d **对齐 `3.代码` 业务分析**：业务分析即真相，与 OpenSpec 方案逐项核对，产出差异明细（含代码位置）
- [x] 1.3e **从 git 获取遇到的坑（三段 git 都要看）**：前端 `aiEduPlatformFront` + 后端 `aiEduPlatform` + Python `aiEduPlatformModel` 三个仓库 commit 历史逐条提炼「坑→根因→解决」，落盘 `5.难点/坑档案.md`（**2026-08-24**：P7+J11+F8=26 条，带 git commit + 代码位置双证据，供 1.4 完善文档「坑」节引用——回答"项目有哪些坑"的素材）


### 1.4 合成「AI答疑 完善文档」8 节（对齐后，代码口径为准）
- [x] ① 模块定位与核心价值 ｜ ② 一次完整答疑怎么走 ｜ ③ 架构与微服务分工 ｜ ④ 安全与防作弊（护栏） ｜ ⑤ 数据落库与掌握度 ｜ ⑥ 图片题与 OCR ｜ ⑦ 流式与性能 ｜ ⑧ 演进路线
      **已完成（2026-08-24）**：落盘 `4.完善文档/01~08-*.md`（8 文件，含数据关联全景图 + 26 坑清单 + 演进故事）
- [x] 每节含三层：为什么（语雀）→ 怎么设计（方案）→ 落地真相（对账）；旧方案口径降级"演进故事"
      **已验证**：8 节均含三层 + 证据引用（3.代码/git 坑档案/OpenSpec对账）
- [x] 8 节齐全、非空模板（完整性检查）——**已验证（2026-08-24）**：8 文件全非空（27-63 行/节，共 372 行），0 空模板；内容完整核对待 1.7 统一做
- [x] **6.缺失补充**（2026-08-24 新增）：逻辑闭环缺口 8 个（行为风控/题库/意图分类/掌握度翻转/护栏归属/不用agent/知识点确认/闭环边界）落盘 `6.缺失补充/逻辑闭环缺口-待回答.md` + `-回答口径.md`，**已回填**：01(意图两分法) 02(无题库) 03(裁判选手) 04(防套答案) 05(题型/知识点闭环/数据边界) 08(不用agent) 各加「追问与防御」小节

### 1.5 切片（认真设计，非"按标题切一刀"）
- [x] **切片清单**（2026-08-24）：`切片清单.md` 定稿——**四层全进 + 权威度分层**（完善文档1.0 / 语雀+OpenSpec 0.7 / 代码分析+坑档案 0.8）；OpenSpec 22 文件精选（**design 11 全进，proposal 11 全不进**——design 的 Context 已 100% 覆盖 proposal 的 Why，proposal 无增量信息）；坑档案实际路径 `5.难点/坑档案.md`
- [x] **切片方案（六个文件夹逐个设计，见下）**（1.5A 表定稿：语雀按`##`/OpenSpec按决策/代码按`##`/完善文档整块/坑档案按坑/缺失补充回填后不进）
- [x] 确定切片对象：**完善文档 8 节 + 三类语料中"策展白名单"（保留进索引的）**——过时/规划内容只留"演进故事"表达，不进正文切片
- [x] 切分规则：按 markdown 标题层级切，**保留 `页面(模块) + 章节` 两层锚点**；代码块/表格作为整体不切开；每块长度设上下限（防过短碎片/过长语义混杂）——**超长块按段落拆块不截断**（完善文档整文件块 12000 上限，标题切块超 6000 段落拆块）
- [x] **代码业务分析不进正文切片**——完善文档内的介绍是正文（"为什么/怎么设计/落地真相"口径），代码只作 `文件:行号` 证据引用，供"顺着代码追问"时指路
- [x] 每块打标签：`模块=ai-tutoring`、`节=1~8`、`来源=语雀/方案/代码`、`权威度(section)`——供页面锚定过滤 + 打分加权
- [x] 切片测试（块数量/长度分布/锚点完整/无重复无遗漏）——**234 块、无重复文本、summary 全齐、无截断、md 与 jsonl 对齐校验通过**
- [x] **切片数据 md 落盘**（2026-08-24 新增）：切好的块按 **md 格式**输出到 `docs/rag/ai-tutoring/切片数据/`——每块一个 md 文件（按来源/文件夹组织：完善文档/语雀/OpenSpec/代码/坑档案），文件头带 `summary` + 标签（权威度/来源/锚点），正文随块；供**人可读审查切片质量** + 向量入库前校验——**已落盘 234 块 + README**

#### 1.5A 六个文件夹切片方案（2026-08-24 初稿，待审）

| 文件夹 | 内容 | 权威 | 切法 | 锚点 | 过滤/特殊处理 |
|---|---|---|---|---|---|
| **1.语雀** | 5 篇 | 0.7 | 按 `##` 小节切 | 文件 + `##`标题 | 保留 `> ⚠️/✅/🚫 代码现状` 标注块（修正过时口径）；竞品/方案对比小节标"演进故事"（MongoDB vs ES 等） |
| **2.OpenSpec** | design 11（proposal 全不进） | 0.7 | 按 `### N. 决策` 切（每条决策一块）；Context 合一块；Risks 不切 | 文件 + 决策标题 | 过时决策标"演进故事"（掌握度URI/单调不减/模型配对/OCR主入口） |
| **3.代码** | 10 分析 | 0.8 | 按 `##` 切（业务情况 + 跨三端证据各块） | 文件 + `##`标题 | 证据表并进业务情况块（保持自包含，检索"具体机制"命中） |
| **4.完善文档** | 8 节 | 1.0 | **整文件一块（不细切）**——每节=一个问题的完整答案，文件即块（27-63 行/块，语义完整） | 文件(节) | 正文主答案；页面锚定过滤用"问题表→节"映射（见下） |
| **5.难点** | 坑档案 26 坑 | 0.8 | 按 `###` 每个坑一块 | 文件 + 坑编号(P1/J1/F1) | 每坑=现象→根因→解决→证据，天然自包含 |
| **6.缺失补充** | 2 个（回答口径/待回答） | — | **回填完善文档后不进**；若独立进 → 按缺口切（每条缺口一块） | — | 底稿，倾向回填后不进（答案进完善文档，底稿留档） |

**切块共性**：每块长度 300~1500 字（防碎片/防语义混杂）；标签统一 `{module=ai-tutoring, section, source, authority, file, anchor}`；过时内容一律"演进故事"表达，权威度中，被正文压住。

**切片块摘要（summary，写给向量桶/检索看）**：
- 每块**必带 `summary` 字段** = 一句话"这块**解决什么问题**"——给向量检索看的引导信息，不是给人看的正文
- **用途**：向量 embedding 用 `summary + text` 拼接（摘要引导命中问题，原文供 LLM 生成细节）；页面锚定过滤也看 summary；打分 `相似度(summary+text) × 权威度 × 锚定`
- **生成方式**（六文件夹各自）：
  | 文件夹 | summary 形态 | 例子 |
  |---|---|---|
  | 完善文档 | `回答「{问题表类}」：{文件标题}` | 05 → `回答「数据关联」：数据落库与掌握度（题型累计平均/数据流/图谱联动）` |
  | 语雀 | `{小节标题}：{一句话总结}` | 「技术选型：MongoDB 文档型」→ `对话存储选型：MongoDB 轻量方案（已演进三层存储）` |
  | OpenSpec | `{决策标题}：{一句话}` | 「决策8 知识点key」→ `掌握度 key 设计：TextbookKP URI（已翻转题型，见演进故事）` |
  | 代码分析 | `{小节标题}：{解决什么问题}` | 「答案护栏」→ `防套答案的确定性护栏规则（2次出口/轮次/安全）` |
  | 坑档案 | `{坑编号}：{坑现象一句话}` | 「J1」→ `会话卡死 SENDING 的根因与修复` |
- **实现**：**LLM 推断批量生成**（不手写）——脚本调 doubao，逐块输出"这块解决什么问题"一句话 summary；一次请求带多块省调用；prompt 约束站在"面试问答检索"角度、只输出一句话

**完善文档 8 节 ↔ 问题表映射**（页面锚定过滤 + 1.7 完整性核对依据，2026-08-24）：

| 节 | 文件 | 对应问题表 |
|---|---|---|
| ① | 01-模块定位与核心价值 | 项目介绍 |
| ② | 02-一次完整答疑怎么走 | 操作 |
| ③ | 03-架构与微服务分工 | 项目介绍 |
| ④ | 04-安全与防作弊（护栏） | 难点 |
| ⑤ | 05-数据落库与掌握度 ★ | 数据关联 |
| ⑥ | 06-图片题与 OCR | 操作 |
| ⑦ | 07-流式与性能 | 难点 |
| ⑧ | 08-演进路线 | 最危险问题 |

**锚定过滤规则**：问题命中"项目介绍"→ 锁 01/03；"操作"→ 锁 02/06；"难点"→ 锁 04/07；"数据关联"→ 锁 05；"最危险问题"→ 锁 08。

### 1.6 索引（向量入 COS 桶 + 多路召回 + 打分）
> 2026-08-24 重设计：**纯 COS**（本地 npz 不再用于查询）；独立向量桶 `rag-1318177119`；结构见 1.6A。
- [x] **嵌入**：dashscope `text-embedding-v3` 768d（`vector_store.embed`，维度校验；embed 接口抽象保留，实际只 dashscope）— 2026-08-24 完成
- [x] **向量入桶**：build_index.py 纯 COS——`embed(summary+text)` → 分批 `put_vectors` → `rag-1318177119/rag-index`（独立桶，topic 在 question-bank 不受影响）— 2026-08-24 完成, 234 块入桶验证
- [x] **索引路由**：`vector_store` 按 vector_type 路由桶（rag → `rag-1318177119`；topic → `question-bank-1318177119`）— 2026-08-24 完成, `_resolve_bucket_index` 返回 (bucket, index)
- [x] **版本与幂等**：version 走 metadata（`YYYY-MM-DD-<sha1[:6]>`）；`--clear` = `list_vectors` → `delete_vectors` 清空 → 重写；查询按 version 过滤 — 2026-08-24 完成, version=2026-08-24-e966ac
- [x] **多路召回**：向量（COS `query_vectors`）+ BM25（本地 jsonl jieba）+ 页面锚定过滤（问题提到哪页锁哪页）；每路独立单元，返回「命中+置信度」— 2026-08-24 完成, 实测「怎么防套答案」锁04/07, 向量12hits conf0.65
- [x] **打分**：RRF 融合 × authority 权威度 × 页面锚定加权（向量/BM25 两路 rank 融合）；编排器统一决策 — 2026-08-24 完成, 完善文档1.0排前/锚定×1.5
- [x] **text 反查**：命中块 text 按 key 从 jsonl 反查（metadata 不含 text，20KB 限制）— 2026-08-24 完成, orchestrate 内联 keymap
- [x] 检索代码按 1.6B 接口纪律分层（意图钩子 / 独立召回单元 / 编排器）——为未来 agent 化(熔断/自适应/意图判断)留缝 — 2026-08-24 完成, core/rag/query.py: classify/retrieve_vector/retrieve_bm25/orchestrate/generate
- [x] 语料副本：jsonl 留本地 `scripts/rag/data/rag_slices.jsonl`（BM25/反查运行时读）— 2026-08-24 完成；**不传 COS 普通对象**（向量桶 role mode 拒 put_object, AccessDenied 实测）
- [x] **查询 API 端点**：`POST /api/tutoring/rag/query`（契约见 1.6C；后端/前端页面并行开工的前置条件）— 2026-08-24 完成, api/rag.py, 实测200 + 降级语义
- [x] 索引测试（桶路由正确、幂等重建、召回命中、锚定过滤、打分排序、API 契约返回结构）— 2026-08-24 完成, tests/rag/test_rag_query.py 15 passed（1.7 加 LLM 意图映射/降级回退测试）

#### 1.6A 向量桶数据结构设计（2026-08-24 定稿）

**物理结构**（COS 向量桶 + 普通对象存储双用）：

| 项 | 值 |
|---|---|
| RAG 向量桶 | `rag-1318177119`（独立；topic 在 `question-bank-1318177119`，互不影响） |
| 物理索引 | `rag-index`（float32 / 768 维 / cosine，控制台建，同 topic-index 先例） |
| 逻辑→物理路由 | `vector_type="rag"` → `(rag-1318177119, rag-index)`；`"topic"` → `(question-bank-1318177119, topic-index)` |
| 配置 | `COS_VECTORS_RAG_BUCKET`（新）+ `COS_VECTORS_INDEXES={"topic": "topic-index", "rag": "rag-index"}` |

**一条块记录（写入单元）**：

```
key      = ai-tutoring/{file}/{anchor}#{chunk_idx}      # 文件+锚点+组内块序号, 不带版本
data     = {"float32": [768 维向量]}                     # embed(summary + "\n" + text)
metadata = {
  version:   "2026-08-24-a1b2c3"    # 语料 sha1[:6] 派生, 语料变 → 版本变 → 可回退
  doc_type:  "ai-tutoring"          # 多模块预留(知识图谱/组织中心将来同写 rag-index 区分)
  source:    "完善文档|语雀|OpenSpec|代码|坑档案"
  authority: 1.0                    # 权威度(打分用: 相似度 × 权威 × 锚定)
  section:   "05"                   # 完善文档节号(锚定过滤锁页用)
  file:      "05-数据落库与掌握度"            # 文件名(引用展示/key 用, 不带路径)
  file_path: "4.完善文档/05-数据落库与掌握度.md"  # 相对语料根 docs/rag/ai-tutoring/(前端定位源文件展示内容)
  anchor:    "05-数据落库与掌握度"    # 页面锚点
  summary:   "..."                  # 一句话"解决什么问题"(检索引导)
}
# text 全文【不进 metadata】——COS 向量索引 metadata ~20KB/条限制, 块最大~6000字超限
# text 留在 rag_slices.jsonl, 检索命中后按 key 反查
# file_path 相对基准 = docs/rag/ai-tutoring/; 切片时由源文件实际路径产生(1.5 已保留目录结构)
```

**版本与幂等**（对齐 project-intro-rag）：
- 索引名固定 `rag-index`（**版本不走索引名**，走 metadata.version）
- 重建：`--clear` = `list_vectors` 枚举全部 key → `delete_vectors` 清空 → 重写（幂等，同 key upsert）
- 查询：按 `metadata.version` 过滤（多数版本），旧残留不污染新版本

**语料副本**（BM25/反查用，非向量）：
- 本地文件：`scripts/rag/data/rag_slices.jsonl`（build 输入即副本，version 由 build 打印对应）
- 【调整 2026-08-24】不传 COS 普通对象——向量桶 role mode 拒 put_object（AccessDenied 实测）；运行时读本地 jsonl

**查询数据流**：

```
问题
 → 向量路: query_vectors(rag-1318177119/rag-index, TopK) → {key, metadata, distance}
 → BM25路: 本地 jsonl 全文(jieba 分词)
 → 融合: RRF × authority × 锚定加权 → top-K
 → text 按 key 反查 jsonl → doubao 生成(面试口述 + 引用)
```

**对齐**：`openspec/changes/project-intro-rag/`（rag-index / `--clear` 幂等 / doc_type / 版本走 metadata 约定）；topic-index 同桶先例（spike 实测 768 cosine、put 后 ~10s 异步生效、cosine distance 越小越相似）。

#### 1.6B 代码架构纪律（2026-08-24 定稿）——为未来 agent 化留缝

> 当前是技术验证阶段（不做熔断/重试/监控），但检索代码必须**长得出来** agent 化。
> 生产级 RAG agent = 意图判断(先分类再答) + 异常熔断降级(每路能挂整体不挂) + 可观测/评测。
> 意图钩子已落地：**LLM 语义判断(闭集6类→锁节) + ANCHOR_RULES 关键词降级保底**(1.7 完成)。
> 接口纪律 = **分层是免费的, 拆函数是贵的**。写成单元, 未来熔断就是包一层; 写成大函数, 未来要拆。

**检索编排架构**（rag_query.py 按此分层, 禁止一路到底）：

```
问题
 → [意图钩子]  classify(question) → 锁策略{锚定节, 是否需检索, 阈值}
        现在:  LLM 语义判断意图类别(闭集6类映射锁节) + ANCHOR_RULES 关键词降级保底(1.7 落地)
        未来:  换更强意图模型 / 加拒答阈值 —— 换实现, 接口不变
 → [召回单元]  retrieve_vector(question) → hits + 置信度     # 独立, 可单独熔断/跳过
 → [召回单元]  retrieve_bm25(question)   → hits + 置信度     # 独立
 → [编排器]    orchestrate(hits...) → RRF × authority × 锚定 → top-K   # 未来在这插降级/拒答
 → [生成]      text 按 key 反查 jsonl → doubao 生成(自规划: 先提炼要点自检再答, 见 3 节任务)
```

**每路召回单元契约**：入参 `question`，出参 `{hits, confidence}`（hit 含 key/metadata/score）。
- 单元内异常**自己兜底**（返回低置信度空结果或抛可被编排器捕获的异常），由编排器决定跳过/降级
- 编排器最终裁决：按 RRF×权威×锚定排序；未来加「最低置信度阈值 → 拒答不编造」

**意图钩子**：`classify(question) → {locked_sections, strategy}` 独立成函数（1.7 落地：
LLM 语义判断意图类别 → 闭集映射锁节；LLM 失败/非闭集 → ANCHOR_RULES 关键词降级保底），
检索/生成只消费结果，不关心实现。

#### 1.6C 查询 API 契约（2026-08-24 定稿）——后端/前端页面并行开工的前置条件

> 目的：入库+查询跑通后，后端/前端基于本契约写页面（问答案 + 展示引用/源文件）。
> 后端/前端设计时会考虑 RAG 健壮性——本契约把「返回结构 / 超时 / 降级 / 鉴权」先定死，两端可并行不阻塞。

**端点**：`POST /api/tutoring/rag/query`（鉴权复用 `x-internal-token`，同 api/vector.py）

**请求**：

```json
{ "question": "怎么防学生套答案？", "top_k": 6 }
```

**响应**（稳定返回结构，前端渲染页面全靠它）：

```json
{
  "answer": "……面试口述风格答案……",
  "references": [
    { "file": "04-安全与防作弊",
      "file_path": "4.完善文档/04-安全与防作弊.md",
      "anchor": "04-安全与防作弊",
      "authority": 1.0,
      "summary": "……" }
  ],
  "intent": { "locked_sections": ["04", "07"], "strategy": "retrieve" },
  "version": "2026-08-24-e966ac"
}
```

- `references[].file_path` = 前端"点开源文件展示内容"（相对语料根 docs/rag/ai-tutoring/）
- `intent.locked_sections` = 意图钩子锁定的节（1.6B），前端可展示"命中了哪些页"
- `version` = 命中的语料版本，前端可标注数据时效

**超时**：查询链路长（embed + COS query + doubao 生成），接口定超时（如 30s）→ 超时返回 504/降级结果，前端不无限转圈。

**降级语义**（RAG 健壮性核心，按序降级）：
1. COS 向量挂了 → 降级纯 BM25（本地 jsonl），references 仍返回
2. doubao 挂了 → 降级返回召回块清单（references 当答案，answer 置为"生成服务不可用，以下为检索到的语料"）
3. 检索置信度过低 → 拒答 `answer="该问题语料未覆盖，建议问项目相关话题"`，**不编造**
4. 所有降级路径 response 结构不变（前端只按同一结构渲染）

**契约对齐**：references 结构 = 1.6A metadata（file/file_path/anchor/authority/summary）；intent = 1.6B 意图钩子输出。

### 1.7 完整性检查
- [x] **覆盖核对（2026-08-24）**：问题表 5 类各取代表问题逐个跑 RAG（`core/rag/query.py` classify + orchestrate），锁定节匹配期望 **10/10**（项目介绍→01/03、操作→02/06、难点→04/07、数据关联→05、最危险→08）
      > **发现并修复**：原始 `ANCHOR_RULES` 关键词太粗——"怎么/如何"万能词把所有问题锁到 02/06，稀释 05/08（覆盖核对 6/10）。→ **加 LLM 意图识别**（`_llm_category`，doubao mini 关思考+20s 超时，闭集 6 类映射锁节），关键词降级保底。覆盖核对升到 10/10，且语义理解更准（"知识图谱联动"→05、"讲讲天气"→其他）
- [x] **溯源抽查（2026-08-24）**：完善文档 8 节抽查（每节含"为什么/怎么设计/落地真相"三层 + `文件:行号` 证据引用，对齐对账），语雀/代码块抽样可溯源（summary 头带来源/锚点/权威度）
- [x] **检索质量自动化** → 交 2+3 评测集 + 评测 agent（1.7 覆盖核对已确认语料完备，质量验收在评测）

---

## 2. AI答疑 评测集（5 条）

> **2A 评测设计（2026-08-24 定稿）**——对齐 `openspec/changes/rag-eval-agent/design.md`（D2~D7），
> 本流水线只跑 AI答疑 一条线（rag-eval-agent 的模块清单里 AI答疑 是首批）。

**评测集格式**（D2，每条）：
```json
{ "module": "ai-tutoring", "question": "……", "question_type": "……",
  "expected_references": ["ai-tutoring/04-安全与防作弊"],   // 预期命中页/节(键前缀)
  "expected_points": ["reveal 两次出口", "count 计数", "Java 硬拦"] }  // 答案应覆盖要点
```
- `question_type`：AI答疑 用**问题表分类**（项目介绍/操作/数据关联/难点/最危险问题，各抽 1 条 = 5 条），
  对齐 1.5A 的「完善文档 8 节 ↔ 问题表映射」——每类问题指向对应节（01/03, 02/06, 05, 04/07, 08）
- `expected_references`：指向完善文档节（锚定目标），供 hit@k 判定"检索是否捞得对"

**评测流程**（D3，先测检索再测答案，分层定位）：
```
每条: 意图钩子(classify) → 双路召回 → orchestrate 记录 top-K
 → hit@k: expected_references 是否命中召回集(k=3)
 → generate(doubao) 记录答案/引用/usage
 → LLM 判分 answer_quality(答案, 预期要点, 预期引用) → 0~5 + rationale
聚合: 5 条 → 模块 hit@k / 平均质量分 / 总成本 / 平均耗时
```

**判分口径**（D4/D5）：
- `hit@k`：expected_references 命中召回 top-k 的比例，k=3（纯函数，可单测）
- `answer_quality`：LLM（doubao，复用现有 doubao 链路）按 **准确性 / 引用正确性 / 覆盖要点** 三方面给 0~5 分，
  严格 JSON `{score, rationale}`；解析失败重试 1 次，仍失败记 0 并标记
- `cost`：prompt+completion × doubao 单价，复用 usage 真算；无 usage 降级估算
- `latency`：检索/生成/总耗时（超时按降级计）

**trace 结构**（D6，每轮落 JSONL，可回溯到具体一条）：
```json
{ "question", "intent", "recall": [top-K {key,score,authority}], "hit": true/false,
  "answer", "references", "usage": {prompt_tokens, completion_tokens},
  "latency": {retrieve_ms, generate_ms, total_ms}, "score", "rationale", "version" }
```

**对齐**：模块清单/状态机见 rag-eval-agent D1；AI答疑 是 `organized → chunked → indexed` 已完成、评测进行中。

- [x] 2.1 编写评测集（来源 = `ai-tutoring.md` 面试问题表，从「项目介绍 / 操作 / 数据关联 / 难点 / 最危险问题」各抽 1 条）— 2026-08-24 完成, `scripts/rag/data/eval/ai-tutoring.jsonl` 5 条
- [x] 2.2 每条含 expected_references / expected_points（指向完善文档对应节）— 2026-08-24 完成, refs 指向 01/03/02/05/04/07/08, points 取自各节核心
- [x] 2.3 评测集加载器（格式校验）— 2026-08-24 完成, `scripts/rag/eval_dataset.py`(校验失败 ValueError, 条数下限), tests 11 passed

## 3. 评测 agent 核心（rag-eval-agent 工具底座，AI答疑 评测依赖）

- [x] 3.1 单条评测执行（页面锚定检索 → 记录召回 → 生成 → 判分）— 2026-08-24 完成, core/rag/eval_agent.py run_eval_case; 走真实检索原语(不降级, 暴露真实质量)
- [x] 3.2 hit@k 计算（k=3，纯函数）— 2026-08-24 完成, hit_at_k(recall, expected_refs, k=3), 按节号判定
- [x] 3.3 LLM 判分（doubao，严格 JSON {score, rationale}；解析失败重试1次，仍失败记0并标记）— 2026-08-24 完成, judge_quality
- [x] 3.4 按模块/全量聚合 — 2026-08-24 完成, aggregate(hit@k均值/质量分均值/judged比例/耗时)
- [x] 3.5 评测执行测试（单条输出齐全、hit 计算正确、判分解析 mock）— 2026-08-24 完成, test_eval_agent 14 passed
- [x] 3.6 聚合测试（模块/全量指标正确）— 2026-08-24 完成
- [x] **评测执行（2026-08-24 首跑）**：`run_eval.py` 5 条 → hit@3=0.80 / 质量分均 2.60 / 判分 100% / 均耗时 5.8s
      > **首跑信号**：检索层 OK(hit@3 0.8)，但 2/5 条"检索全对但答案漏要点/编造"——初判生成层问题，trace 已落盘 `data/eval/trace_latest.jsonl`
- [x] **生成质量修复（2026-08-24）**：诊断 trace 发现**真问题在判分侧非生成侧**——
      ① 判分 prompt 太弱：认不出同义表述("ScoreMapper 累计"= "题型掌握度回流")、误判语料有支撑的表述为"编造"
      ② 评测集 expected_points 混入不适用该问题的细节(B3门控/澄清卡 是"掌握度怎么算"的要点，非"怎么联动")
      → 修判分 prompt(同义覆盖即算覆盖 + 传语料块供"编造"判定 + 评分锚定 0~5) + 收窄数据关联 expected_points
      → **质量分 2.60 → 4.60/5**(操作 2→5, 数据关联 0→4, 难点 3→5, 最危险 4→5), hit@3 保持 0.80
      > **教训**：评测"分数低"先查判分/评测集，再怀疑检索/生成——分层定位要分层修
- [x] **判分确定性硬化（2026-08-24）**：判分 prompt 融入 DeepSeek 建议（硬百分比锚定 + 编造封顶 3 分 + 截断容错），
      并进一步**把分数计算从 LLM 移到代码**——模型只报 `covered_count`(覆盖几条) + `fabricated`(是否编造)，
      `_score_from_covered` 按覆盖比例(100%→5, ≥80%→4, ≥60%→3, ≥40%→2, >0%→1, 0%→0) + 编造封顶 3 分硬算。
      → 消除 LLM 百分比计算波动（之前"覆盖4/4却给4分"），**分数可复现、可解释**
      → 质量分 3.80（更严格更可信，操作类准确 5 分），`_score_from_covered` 纯函数测试 6 个
- [ ] **生成前自规划（self-critique，2026-08-24 设计待开发）**：把判分标准反向注入生成侧，让答案**天然贴近评分标准**——
      > 设计（先设计后开发，勿直接写码）：
      > - **理念**：评测是"打分"，生成前自规划是"自我评分"——同一套价值观（覆盖要点 + 不编造 + 语料支撑），两处统一
      > - **要点来源**：生成时**不喂 expected_points**（评测集预写标准答案，面试官随机问，生成时不存在）——要点**从检索到的语料块提炼**（3~5 条关键事实清单）
      > - **流程**：`generate` prompt 引导——① 从语料块提炼关键事实清单 ② 自检每条有语料支撑（无支撑的不写，防编造）③ 按清单组织答案（先结论、分层覆盖、引用出处）
      > - **成本**：不加 LLM 调用（一次生成内完成，prompt 引导先思考再答）
      > - **架构**：落 `core/rag/query.py generate` 层，orchestrate 以上不动，1.6C API 契约不变
      > - **验证**：改完跑 `run_eval.py` 对比质量分（预期上升：答案更覆盖要点），hit@3 应不变（检索未动）

## 4. 指标与成本

- [x] 4.1 cost 统计（prompt+completion × doubao 单价，复用 usage 真算；无 usage 降级估算）— 2026-08-24 完成, `calc_cost` 纯函数, generate/judge 捕获 `usage_metadata`(langchain 1.2.20)
- [x] 4.2 latency 统计（检索/生成/总耗时，超时按降级计）— 2026-08-24 完成, latency_ms 三段已捕获
- [x] 4.3 成本与耗时测试 — 2026-08-24 完成, TestCost(calc_cost 已知价/零) + aggregate cost/tokens

## 5. 可观测评测

- [x] 5.1 trace 落盘（JSONL：query/召回/得分/hit/答案/引用/usage/耗时/判分）— 2026-08-24 完成, `data/eval/trace_latest.jsonl`(含 usage/cost)
- [x] 5.2 评测报告生成（按模块 + 全量汇总，含语料版本标识）— 2026-08-24 完成, `data/eval/reports/<version>.json`
- [x] 5.3 报告版本对比（新旧两次 hit@k/质量分变化）— 2026-08-24 完成, `run_eval.py --compare`
- [x] 5.4 trace 测试（落盘完整性、单条回溯）— 2026-08-24 完成, test_run_eval TestTrace
- [x] 5.5 报告测试（黄金文件对比、版本对比正确）— 2026-08-24 完成, TestReport(报告落盘/对比/无历史跳过)
- [x] **实测（2026-08-24）**：5 条评测 → hit@3=0.80 / 质量分均 3.60 / 判分 100% / 均耗时 5.7s / **总成本 ¥0.0803(均 ¥0.0161, 均 4686 tokens)**

## 6. API 端点

- [x] 6.1 `POST /api/rag/eval/run`（触发评测，返回运行 id）— 2026-08-24 完成, 同步执行(离线工具 ~30s, run_in_threadpool 不阻塞), 返回 {ok, version, aggregate, report_path}
- [x] 6.2 `GET /api/rag/eval/report`（查询报告，支持版本对比）— 2026-08-24 完成, 最新聚合 + 历史版本列表
- [x] 6.3 鉴权（`x-internal-token`）— 2026-08-24 完成, verify_internal_token
- [x] 6.4 API 测试（运行、报告、鉴权失败）— 2026-08-24 完成, test_eval_api 6 passed
