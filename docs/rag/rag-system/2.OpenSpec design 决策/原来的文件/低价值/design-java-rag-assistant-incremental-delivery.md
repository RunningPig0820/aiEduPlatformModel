## Context

`rag-project-intro-assistant`（已校验、设计完整）定义了一张完整的白盒 RAG 链路：角色门 → intent → clarify/switch → rewrite → recall → rerank → boundary → generate → done，含 tokens_usage / trace_id / close / is_quoted / suggestions / 评估。该方案按**功能维度**设计，交付时是整条链一起做、做完才联调。

本变更解决交付方式问题：**按依赖序切成 7 个纵向切片，每完成一个切片立即做前后端对接测试**。功能需求、SSE 事件契约、错误码、测试用例语义全部沿用 `rag-project-intro-assistant`，本变更只增加"哪个里程碑交付什么、怎么验收"的编排层。

可复用资产：
- 既有变更的 D1-D12 决策（角色门 D1 / intent D2 / 切换 D3 / 模块放行+范围门 D4 / clarify D5 / is_quoted D6 / 分层超时 D7 / tokens D8 / 数据驱动 D9 / 评估 D10 / suggestions D11 / close D12）
- 既有测试用例编号 RAG-GATE/SSE/CONTRACT/QUOTE/COST/CLOSE/BRIDGE/ABORT（36 条）
- Python 侧 `core/rag/query.py` 现有单模块 RAG 链路（可逐步泛化，不一次性重构）

## Goals / Non-Goals

**Goals:**
- 7 个里程碑各自**可独立完成、独立对接测试**，不依赖下游能力
- 每完成一个里程碑，前端立即拿到一项**可见物**并可验收（403 页 / 意图标签 / 召回块 / 边界话术 / 成本面板 / 引用高亮 / 引导 chips / 结算面板）
- 全程保持 RAG 功能完整可用，**不因切片而丢功能**（7 项清单缺口全补齐）
- 后端、Python、前端三侧可按里程碑并行推进，但依赖序以里程碑为准

**Non-Goals:**
- 不改变 `rag-project-intro-assistant` 的任何功能需求 / 设计决策 / SSE 事件契约 / 错误码
- 不做新的系统行为，只编排"何时交付什么"
- 不定义前端页面交互细节（前端另立变更），只定义每步对接的前端可见物与契约

## Decisions

### D-A. 7 里程碑 = 纵向切片链，依赖序单向，M 编号即构建顺序

```
M1 权限判断 ──► M2 意图+改写+骨架 ──► M3 召回+remark+边界 ──► M4 生成+token
                                                   │
                                                   ▼
M7 会话收尾（close/累计/补查） ◄── M6 问题提示 ◄── M5 自我检查
```

- **依赖原则**：M(n) 只依赖 ≤M(n-1) 的产出；每步不触达下游能力。
- **为什么**：原 7 项清单把 `token 展示`(M4) 和 `问题提示`(M6) 放最前，属依赖倒挂——token 需生成完才有，suggestions 在 done 之后。按依赖序重排后，每步都"能跑通、有可见物"。
- **备选**：按原清单顺序交付 → 前两步无可测后端行为，联调无从下手，弃。

### D-B. SSE 事件契约在 M2 冻结，下游里程碑只补字段不重排

M2 搭建白盒骨架时即定稿事件时序 `permission → intent → (clarify|switch) → rewrite → rerank → (boundary) → token* → done` 与每事件的字段集合。M3-M7 只向既有事件**追加字段**（如 rerank 增加 score、done 增加 quotedKeys/suggestions），**不得重排、不得删除**已发布字段。**开始引导（M6 的 guide 池）走非 SSE 接口 `GET /api/rag/assistant/guide`，不占冻结时序**——会话开始无问答轮，属页面级一次拉取，不进 SSE 事件序列。

- **为什么**：契约冻结是切片交付的根——前端每步对接的是同一份时序，M2 后前端渲染层一次写定，后续只是"字段变多"，不返工。
- **备选**：每里程碑自由演进事件 → 前端反复返工，切片意义归零，弃。

### D-C. 桩替（Stub）策略：上游未完成的阶段先返回固定占位

- M2 阶段：generate 未实现，Python 桩替返回固定占位答案（如"（生成阶段待实现）这是桩替回答"），使 `permission→intent→rewrite→done` 整轮可通，前端可对"阶段展示区 + 时序"做对接。
- M3 阶段：generate 仍桩替，前端可对"召回块面板"对接（块灰显、点击查看原文走 file_path）。
- M4 起移除桩替，换真实 doubao 流式。
- **为什么**：每步必须有可联调的完整往返，桩替让前端不被下游阻塞；桩替话术固定、0 token，测试期成本可控。
- **备选**：每步只做后端不起前端 → 违背"完成即对接"目标，弃。

### D-D. 每里程碑的完成标准 = 前端可见物 + 对接测试用例通过

| 里程碑 | 前端可见物 | 对接测试（复用 RAG-* 编号） |
|--------|-----------|------------------------------|
| M1 权限判断 | 非学生 403 页 / 学生放行 | RAG-GATE-001~004 |
| M2 意图+改写+骨架 | 阶段展示区（权限✓/意图标签/改写后问题）、trace 展示 | RAG-SSE-001（桩）、RAG-CONTRACT-002/003、RAG-COST-003 |
| M3 召回+remark+边界 | 召回块面板（标题/摘要/file_path，点击查看原文）、边界拒答话术 | RAG-SSE-002/003、RAG-BRIDGE-001~003、RAG-COST-002 |
| M4 生成+token | 流式回答、成本面板（prompt/completion/cache_hit/total） | RAG-SSE-001（全量）、RAG-COST-001/007、RAG-ABORT-001 |
| M5 自我检查 | 引用块高亮/灰显折叠、评估报告一屏 | RAG-QUOTE-001~005、RAG-CONTRACT-001、评估扩展 |
| M6 问题提示 | 开始引导 chips（定向 RAG）+ 结束引导 chips（含 RAG）+ clarify 澄清追问 UI | RAG-SSE-004/005（switch）、SUGG-001~003 |
| M7 会话收尾 | 关闭对话按钮 + 结算面板、断线重连补查 | RAG-CLOSE-001~006、RAG-COST-004~006 |

- **为什么**：把"完成"从口头定义为**可验收**，切片交付才有纪律。
- **备选**：以"后端接口写完"为完成 → 前端没对接，等于没完成，弃。

### D-E. 原 7 项清单的归属与缺口补齐映射

| 原清单项 | 归属里程碑 | 处理 |
|----------|-----------|------|
| 1. token 展示 | M4（生成+token）+ M7（会话累计） | 移到生成之后 |
| 2. 问题提示 | M6（suggestions + clarify） | 移到 done 之后，补 clarify |
| 3. 权限判断 | M1 | 保持首位（最独立） |
| 4. 意图分析 | M2 | 补 rewrite/switch/SSE 骨架 |
| 5. 多路召回 | M3 | 与 rerank 合并（同一产物） |
| 6. remark 打分 | M3 | 含 RRF Top-K + 范围门边界拒答 |
| 7. 自我检查 | M5 | is_quoted + 评估 |

缺口补齐：Query 改写（M2）、clarify 澄清（M6）、范围门边界拒答（M3）、switch（M2）、close+累计 token（M7）、trace 补查（M7）、分层超时/断连取消（M3/M4）、SSE 骨架（M2）、评估（M5）。

### D-F. 复用什么、变更什么

- **原样复用**：`rag-project-intro-assistant` 的 proposal/design/specs（D1-D12、5 capability）、错误码表、RAG-* 测试语义、Python 契约任务（tasks 3.x/4.x）。
- **本变更新增**：里程碑编排（M1-M7 顺序 + 桩替 + 完成标准）、按里程碑分组的 tasks/api/test。
- **两变更关系**：功能设计变更（`rag-project-intro-assistant`）定义"做什么"；本变更定义"按什么顺序做完并验收"。实现时以本变更的 tasks 为准执行，spec 语义查原变更。

### D-G. 前后端对接节奏

每个里程碑完成后：后端（本仓库）+ Python（Model 仓库）合并该切片 → 前端对接该切片的可见物 → 跑该里程碑的对接测试用例 → 全绿后才进入下一里程碑。任一切片验收失败不阻塞其它切片（可并行开发），但**对接验收通过是进入下一步的前置条件**。

## Risks / Trade-offs

- [切片粒度过细（如 M3 含召回+打分+边界三步）导致单步变重] → M3 是"检索质量"一个完整纵向切片，三件套共享同一 rerank 产物，不可再拆（拆则无前端可见物）；若实测仍重，可拆"边界拒答"为 M3.5。
- [桩替期前端习惯了占位答案，M4 换真实流式有观感跳跃] → 桩替话术标注"（桩替）"，前端按契约渲染即可无缝切换。
- [契约冻结后想改事件字段] → 冻结只针对字段增删与时序；需改则走变更评审，评估对已验收里程碑的回归影响。
- [三侧并行导致里程碑验收依赖 Python 先行] → Python 契约任务清单（原 tasks 3.x）按里程碑拆分归属，Java 桩替可先行联调，Python 完成即替换桩替。
- [原变更 `rag-project-intro-assistant` 尚未归档 specs] → 本变更引用其 specs 路径；两变更先后落地，specs 语义不重复维护。

## Migration Plan

1. 先落地本变更（交付编排），`rag-project-intro-assistant` 作为功能设计基线保持不动。
2. 按 M1→M7 顺序逐切片实现 + 对接测试（M1 纯 Java 先行，M2 起 Python 契约按里程碑拆分）。
3. 每切片合入 = 一个可独立回归的提交；SSE 契约冻结保证切片间不破坏。
4. 回滚：任一切片合入失败可单独回退该切片，不影响已完成里程碑。

## Open Questions

- M3 是否需拆"边界拒答"为独立小步（取决于真实联调量）——暂并入 M3，实测超重再拆。
- M2 桩替占位答案的具体文案——固定话术即可，前端按契约渲染，不阻塞。
- 里程碑验收的自动化程度（对接测试是否要接前端 e2e）——先以"后端对接测试 + 前端手工验收"为门槛，e2e 后续补。
