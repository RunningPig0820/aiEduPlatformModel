# 核心功能与白盒问答
> summary: 核心功能与白盒问答（面板形态与白盒链路）
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-frontend-ui-02-核心功能与白盒问答.md
> 类别：操作流程

---

> 检索摘要（业务向）：前端 RAG 助手 spec 的 MUST 要求：助手默认展开、收起留提示条、置顶头部（页面+角色+累计 token）、白盒流水线阶段按 SSE 事件顺序点亮（permission→intent→rewrite→rerank→token→done）各 scenario 是什么？

### 规格概述
> 检索摘要：学生 RAG 项目介绍助手前端规格：默认展开面板、白盒展示 RAG 链路、引用可点、成本透明、引导完整、澄清点选、非学生占位、会话结算与断线补查。

学生 RAG 项目介绍助手前端：改造现有 AI 助手为默认展开面板，白盒展示 RAG 链路（权限/意图/改写/召回/重排/生成），引用可点、成本透明、引导完整、澄清可点选、非学生占位、会话结算与断线补查。

### Requirement: 助手默认展开与收起留提示
> 检索摘要：RAG 助手面板进入页面默认展开（非隐藏 FAB），收起变为固定悬浮细条，始终显示当前建议"建议问问"可点发送、可点展开恢复。

学生进入页面 SHALL 默认展开 RAG 助手面板（非隐藏 FAB）；收起 SHALL 变为固定悬浮细条，始终显示一条当前建议（"建议问问: …"，可点发送、可点展开恢复）。

#### Scenario: 进入页面默认展开
- **WHEN** 学生进入学生端页面
- **THEN** RAG 助手面板默认展开显示，不隐藏于 FAB 后

#### Scenario: 收起留提示条
- **WHEN** 学生点击收起按钮
- **THEN** 面板收起为固定悬浮细条，显示当前建议，点击可发送、点击可展开

### Requirement: 置顶头部
> 检索摘要：面板置顶固定头部展示当前页面（pageMeta 名+intro）、当前用户角色、本场累计消耗 token，头部不随对话滚动。

面板 SHALL 在置顶固定位置展示：当前页面（pageMeta 名 + intro）、当前用户角色、本场累计消耗 token。头部不随对话滚动。

#### Scenario: 头部展示页面与角色
- **WHEN** 学生打开面板
- **THEN** 头部显示当前页面名（+intro）与当前用户角色

#### Scenario: 头部展示累计 token
- **WHEN** 每轮 `done.tokensUsage` 到达
- **THEN** 头部本场累计 token 更新（cacheHit 为估算值时标注"估算"）

### Requirement: 白盒流水线阶段展示
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

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-frontend-rag-assistant-frontend-rag-assistant-ui.md`（§规格概述 §Requirement 助手默认展开与收起留提示 §Requirement 置顶头部 §Requirement 白盒流水线阶段展示）
