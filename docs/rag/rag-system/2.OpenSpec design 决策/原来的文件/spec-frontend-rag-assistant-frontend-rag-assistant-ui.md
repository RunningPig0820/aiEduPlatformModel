> summary: 本规格定义学生 RAG 项目介绍助手前端的 ADDED 需求：把现有 AI 助手改为默认展开面板，白盒展示 RAG 链路（权限/意图/改写/召回/重排/生成），并覆盖引用面板灰显高亮、成本展示与会话结算、引导 chips、澄清点选、当前页面锚点携带、非学生占位与断线补查。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-source/rag-system/OpenSpec设计决策/spec-frontend-rag-assistant-frontend-rag-assistant-ui.md
> 类别：操作流程

# rag-assistant-ui Specification

## 文档说明
> 本文件为原始spec文档的RAG结构化重构版本。
> ⚠️重要提示：本文属于**设计阶段素材**，同时包含✅已落地、⚠️构想未实现、❓待决策内容；业务真实实现请以权威度0.8的canonical真相源文档为准。本文件独立完整，内容不拆分到外部canonical文档。

### 规格概述
> 状态：⚠️
> 检索摘要：学生 RAG 项目介绍助手前端规格：默认展开面板、白盒展示 RAG 链路、引用可点、成本透明、引导完整、澄清点选、非学生占位、会话结算与断线补查。

学生 RAG 项目介绍助手前端：改造现有 AI 助手为默认展开面板，白盒展示 RAG 链路（权限/意图/改写/召回/重排/生成），引用可点、成本透明、引导完整、澄清可点选、非学生占位、会话结算与断线补查。

### Requirement: 助手默认展开与收起留提示
> 状态：⚠️
> 检索摘要：RAG 助手面板进入页面默认展开（非隐藏 FAB），收起变为固定悬浮细条，始终显示当前建议"建议问问"可点发送、可点展开恢复。

学生进入页面 SHALL 默认展开 RAG 助手面板（非隐藏 FAB）；收起 SHALL 变为固定悬浮细条，始终显示一条当前建议（"建议问问: …"，可点发送、可点展开恢复）。

#### Scenario: 进入页面默认展开
- **WHEN** 学生进入学生端页面
- **THEN** RAG 助手面板默认展开显示，不隐藏于 FAB 后

#### Scenario: 收起留提示条
- **WHEN** 学生点击收起按钮
- **THEN** 面板收起为固定悬浮细条，显示当前建议，点击可发送、点击可展开

### Requirement: 置顶头部
> 状态：⚠️
> 检索摘要：面板置顶固定头部展示当前页面（pageMeta 名+intro）、当前用户角色、本场累计消耗 token，头部不随对话滚动。

面板 SHALL 在置顶固定位置展示：当前页面（pageMeta 名 + intro）、当前用户角色、本场累计消耗 token。头部不随对话滚动。

#### Scenario: 头部展示页面与角色
- **WHEN** 学生打开面板
- **THEN** 头部显示当前页面名（+intro）与当前用户角色

#### Scenario: 头部展示累计 token
- **WHEN** 每轮 `done.tokensUsage` 到达
- **THEN** 头部本场累计 token 更新（cacheHit 为估算值时标注"估算"）

### Requirement: 白盒流水线阶段展示
> 状态：⚠️
> 检索摘要：面板按 SSE 事件顺序渲染 RAG 链路阶段行 permission→intent→(clarify|switch)→rewrite→rerank→(boundary)→token→done，每事件点亮对应阶段。

面板 SHALL 按 SSE 事件顺序渲染 RAG 链路阶段行：`permission → intent → (clarify|switch) → rewrite → rerank → (boundary) → token → done`，每事件到达点亮对应阶段（✓/脉动/灰）。

#### Scenario: 正常流阶段点亮
- **WHEN** 一轮问答产生 permission/intent/rewrite/rerank/token/done
- **THEN** 阶段行依次点亮：权限控制/意图识别/Query 改写/多路召回+重排/生成

#### Scenario: 澄清/切换分支展示
- **WHEN** intent 触发 clarify 或 switch
- **THEN** 对应分支卡片展示（澄清候选 / 切换 from→to），无 rewrite/rerank/token 流

#### Scenario: 边界拒答展示
- **WHEN** rerank 后触发 boundary（reason=low_confidence）
- **THEN** 展示固定话术"未找到关联文档，我尚未掌握"，非错误弹窗，无 token 流

### Requirement: 轮次防卡死（分支终止 + 超时自关闭）
> 状态：⚠️
> 检索摘要：SSE 三分支（clarify/boundary/switch）任一在 done 或 error 到达时终止所有转圈并定稿；单轮 45s 超时前端主动取消并提示重试。

SSE 非纯线性链路（clarify/boundary/switch 三分支），任一分支的流 SHALL 在 `done` 或 `error` 到达时终止所有"处理中"转圈、阶段区定稿；若单轮超时（默认 45s，后端桥 60s 超时的前端兜底）仍未收到 done/error，前端 SHALL 主动取消本轮、展示超时提示并恢复可输入，绝不无限转圈。

#### Scenario: done 终止所有分支转圈
- **WHEN** 任意分支（正常 / clarify / boundary / switch）收到 done
- **THEN** 本轮所有阶段停止转圈、阶段区定稿；clarify 轮 done 带空 answer 时气泡回显澄清提示（不空白）

#### Scenario: 单轮超时自关闭
- **WHEN** 发起问答后 45s 未收到 done/error
- **THEN** 前端取消本轮流，展示"响应超时，已结束本轮，请重试"，恢复可输入

### Requirement: 引用面板（灰显 → 高亮）
> 状态：⚠️
> 检索摘要：rerank 到达渲染精排块卡片灰显折叠，done 的 quotedKeys 命中块高亮展开、未命中保持灰显，filePath 可点查看原文。

面板 SHALL 在 `rerank` 事件到达时渲染精排块卡片（blockId/title/summary/filePath，灰显折叠，filePath 可点"查看原文"）；`done` 的 `quotedKeys` 到达后命中的块高亮展开、未命中保持灰显折叠。

#### Scenario: rerank 先灰显
- **WHEN** rerank 事件到达
- **THEN** 引用面板渲染 Top-K 块（灰显折叠），filePath 可点击查看原文（`GET /api/rag/assistant/source?path=<urlencoded>`，query 传参）

#### Scenario: done 后高亮命中
- **WHEN** done 携带 quotedKeys
- **THEN** 命中的块高亮展开，未命中保持灰显折叠

### Requirement: 成本展示与会话结算
> 状态：⚠️
> 检索摘要：每轮 done 展示 tokensUsage 四字段（prompt/completion/cacheHit/total）累计进头部；"结束对话"调 close 返回会话累计 token 与轮数。

面板 SHALL 展示每轮 `done.tokensUsage`（prompt/completion/cacheHit/total）；提供"结束对话"按钮调 `POST /sessions/{sessionId}/close`，返回后展示会话累计 token 与轮数（"本次对话总消耗"）。

#### Scenario: 本轮成本展示
- **WHEN** 每轮 done 到达
- **THEN** 展示本轮 tokensUsage 四字段，累计进头部

#### Scenario: 结束对话结算
- **WHEN** 学生点击"结束对话"
- **THEN** 调 close 接口，展示会话累计 token + 轮数

### Requirement: 引导完整（开始引导 + 结束建议）
> 状态：⚠️
> 检索摘要：进入时拉取 GET /guide 展示 RAG 定向开始引导 chips；每轮 done.suggestions 渲染结束建议 chips 可点再问重走链路。

面板 SHALL 在进入时拉取 `GET /guide` 展示 RAG 定向开始引导 chips；每轮 `done.suggestions` 渲染结束建议 chips，点击后作为新问题重发重走链路。

#### Scenario: 开始引导展示
- **WHEN** 学生进入面板且尚无会话
- **THEN** 展示 RAG 定向开始引导 chips（定位/架构/数据流/评测/坑）

#### Scenario: 结束建议可点再问
- **WHEN** 一轮 done 返回 suggestions
- **THEN** 渲染建议 chips，点击后作为新问题发起新一轮问答

### Requirement: 澄清点选交互
> 状态：⚠️
> 检索摘要：clarify 候选 chips 为字符串 id 数组，前端经 pageModuleMap 映射中文 label、未知 id 显示原文兜底；点选=重发原问+currentProject=点选模块 id。

`clarify` 事件到达 SHALL 渲染候选 chips（`candidates` 为**字符串 id 数组**，前端用 `pageModuleMap` 的 id→中文 label 渲染，未知 id 显示原文兜底）；点选候选 SHALL **重发原问题 + `currentProject`=点选模块 id**（非发裸功能名）。点选模块与会话锚点不同 → `switch` 事件照常处理（前端提示"已切换至 X"）。

#### Scenario: 澄清候选点选
- **WHEN** 学生点击 clarify 候选 chip（如 [RAG项目]，label 经 id→label 映射）
- **THEN** 前端重发原问题 + `currentProject=rag-system`（id），后端以 currentProject 权威锚定

#### Scenario: 未知候选兜底
- **WHEN** candidates 含 pageModuleMap 未覆盖的 id
- **THEN** 前端以原文 id 显示该 chip（不崩溃），点选仍以其 id 作为 currentProject 重发

#### Scenario: 点选后切换提示
- **WHEN** 点选模块与会话锚点不同
- **THEN** 后端发 switch 事件，前端提示"已切换至 X"

### Requirement: 当前页面锚点携带
> 状态：⚠️
> 检索摘要：每次 ask 携带 currentProject（camelCase，由页面 pageCode 映射、缺省 rag-system），模块 id 闭集 ai-tutoring/knowledge-graph/question-analysis/rag-system。

每次 ask SHALL 携带 `currentProject`（camelCase，由当前页面 pageCode 经映射得出，缺省 rag-system），告知后端语料池。模块 id 闭集：`ai-tutoring / knowledge-graph / question-analysis / rag-system`。

#### Scenario: 携带页面锚点
- **WHEN** 学生在 AI答疑页发起提问
- **THEN** ask 请求携带 `currentProject=ai-tutoring`

#### Scenario: 映射缺省
- **WHEN** 页面不在映射表
- **THEN** 携带缺省 `rag-system`（全局模式）

### Requirement: 非学生占位
> 状态：⚠️
> 检索摘要：面板读取当前用户角色并在头部展示，角色非 STUDENT 展示"当前非学生无法使用"占位、不发起 ask，不硬报错。

面板 SHALL 读取当前用户角色并在头部展示；角色非 STUDENT SHALL 展示"当前非学生无法使用"占位，不发起 ask。

#### Scenario: 非学生占位
- **WHEN** 当前登录角色为 TEACHER/ADMIN 或缺失
- **THEN** 面板展示"当前非学生无法使用"，不发起 ask，不硬报错

### Requirement: 断线补查
> 状态：⚠️
> 检索摘要：SSE 中断用 permission 携带的 traceId（流开始即存）调 turns 接口补查；done 回显 traceId 一致性校验；trace 过期 10002 提示重发。

SSE 中断 SHALL 用 `permission` 事件携带的 `traceId`（流开始即存，任意阶段断连可用）调 `GET /api/rag/assistant/turns/{traceId}` 补查该轮完整结果；`done` 回显 traceId 做一致性校验；trace 过期（10002）SHALL 提示重发问题。

#### Scenario: 断线补查
- **WHEN** 流式中断（permission 已到、done 未到）
- **THEN** 用已存的 permission.traceId 调 turns 接口补查，渲染该轮完整结果

#### Scenario: done 回显校验
- **WHEN** done 到达
- **THEN** done.traceId 与 permission.traceId 比对，不一致告警但不阻断渲染

#### Scenario: trace 过期
- **WHEN** 补查返回 10002
- **THEN** 提示用户重发问题
