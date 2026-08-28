## Why

现有 `rag-project-intro-assistant` 变更按**功能维度**完成设计（一次交付整条白盒 RAG 链路），前后端只能等全部做完才联调，联调风险集中、中间无可见产出。现在需要**按小功能切片**：每完成一个里程碑，立即做前后端对接测试（功能可用、契约正确、缺陷早暴露），降低交付风险并让每步都有可验收成果。

本变更不改变 `rag-project-intro-assistant` 的功能设计（D1-D12 决策与 5 个 capability 原样保留），只新增**按依赖序的里程碑交付计划**：把原方案拆成 7 个纵向切片，补齐原功能清单缺失的功能点，并为每个切片定义前端可见物与对接测试验收标准。

## What Changes

- **新增 7 里程碑交付计划**（M1-M7），每个里程碑 = 一个纵向切片，具备：
  - 明确的**前端可见物**（403 页 / 意图标签 / 改写后问题 / 召回块面板 / 边界拒答话术 / 成本面板 / 引用高亮 / 引导 chips / 结算面板）
  - 明确的**对接测试验收**（复用既有 RAG-* 测试编号，按里程碑分组执行）
  - 不依赖下游能力即可独立完成与联调
- **里程碑依赖序重排**（修正原清单顺序倒挂）：
  - 权限判断放第一位（纯 Java、0 依赖）；token 展示移到 M4 生成阶段之后（token 需生成完才有）；问题提示移到 M6（在 done 之后）
  - 多路召回 + remark 打分 + 边界拒答合并为 M3（同一次 RRF orchestrate 的产物，拆开无前端可见物）
- **补齐原 7 项清单缺失的功能点**：Query 改写（rewrite）、clarify 澄清追问、范围门边界拒答、switch 切换、close 关闭对话 + 会话累计 token、trace_id 断线补查、分层超时 + 断连取消、SSE 白盒事件骨架、评估（is_quoted 校验 + precision_at_k + 边界拒答类型）、开始引导（RAG 定向静态池，非 SSE）
- **SSE 事件契约全程冻结**：`permission → intent → (clarify|switch) → rewrite → rerank → (boundary) → token* → done` 时序在 M2 骨架定稿后不变，下游里程碑只补充字段不重排
- **复用既有工件**：功能需求/设计决策/错误码/测试用例全部沿用 `rag-project-intro-assistant`（D1-D12、RAG-GATE/SSE/CONTRACT/QUOTE/COST/CLOSE/BRIDGE/ABORT），本变更只增加"哪个里程碑交付什么、怎么验收"的编排层

## Capabilities

### New Capabilities

- `milestone-01-role-gate`: M1 权限判断——角色硬门（仅 STUDENT，非学生/缺失→固定 403，不进 RAG 流程、0 token），纯 Java 零依赖，首个可对接切片
- `milestone-02-intent-sse`: M2 白盒骨架 + 意图分析 + Query 改写——SSE 事件通道与时序冻结、trace_id 生成、intent LLM 结构化输出、rewrite 透传、switch 判定；generate 先桩替（占位答案）保证整轮可通
- `milestone-03-recall-rerank`: M3 多路召回 + remark 打分 + 边界拒答——向量+BM25 双路召回（单路 2s 超时降级）、RRF 融合 Top-K 精排、范围门低置信度过滤（唯一拒答路径）；generate 仍桩替
- `milestone-04-generate-token`: M4 生成 + token 展示——doubao 流式、8s 超时降级话术、断连取消、tokens_usage 四字段 + trace_id、done 事件重建；成本面板落地（原 #1）
- `milestone-05-self-check`: M5 自我检查——is_quoted LCS 硬匹配（8 中/12 英，done 后补发）+ 评估扩展（边界拒答类型、precision_at_k、is_quoted 入评估、baseline 白盒展示）（原 #7）
- `milestone-06-suggestions`: M6 问题提示——开始引导（会话入口，静态池定向 RAG）+ 结束建议（done 后 1~3 条，**必含 RAG 方向**，RAG 始终带上非并列模块）+ clarify 澄清轮（歧义才问、默认当前功能、最多一轮）（原 #2）
- `milestone-07-session-close`: M7 会话收尾——close 关闭对话（中止在途流 + 置 closed + 返回会话累计 token）+ Redis 会话累计 + trace_id 断线补查

### Modified Capabilities

<!-- 无既有 spec 需求变化：rag-project-intro-assistant 的功能设计原样保留，本变更只编排交付顺序与验收 -->

## Impact

- **本仓库（ai-edu-backend）**：无新功能代码需求变化；`tasks.md` 按 M1-M7 里程碑重组，每个里程碑是独立可合入的切片
- **aiEduPlatformModel 仓库**：契约任务清单（原 tasks 3.x/4.x）按里程碑拆分归属，Python 侧可并行推进但依赖序以里程碑为准
- **前端（aiEduPlatformFront）**：按里程碑逐项对接，每完成一个里程碑即验收一项前端可见物，不必等全量
- **依赖**：无新增
- **验收方式变化**：由"整条链路跑通"改为"每个里程碑有独立验收标准（前端可见物 + 对接测试用例）"，SSE 契约冻结保证切片间不破坏既有完成项
