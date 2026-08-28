# 核心功能与白盒问答
> summary: 核心功能与白盒问答-2（防卡死/引用面板/成本结算）
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-frontend-ui-02-核心功能与白盒问答-2.md
> 类别：操作流程

---

> 检索摘要（业务向）：前端 spec：轮次防卡死（done/error 终止所有分支转圈、45s 超时自关闭）、引用面板 rerank 灰显→done quotedKeys 高亮+filePath 查看原文、成本展示与会话结算（tokensUsage 四字段 + close 返回累计 token/轮数）的 MUST 要求与 scenario 是什么？

### Requirement: 轮次防卡死（分支终止 + 超时自关闭）
> 检索摘要：SSE 三分支（clarify/boundary/switch）任一在 done 或 error 到达时终止所有转圈并定稿；单轮 45s 超时前端主动取消并提示重试。

SSE 非纯线性链路（clarify/boundary/switch 三分支），任一分支的流 SHALL 在 `done` 或 `error` 到达时终止所有"处理中"转圈、阶段区定稿；若单轮超时（默认 45s，后端桥 60s 超时的前端兜底）仍未收到 done/error，前端 SHALL 主动取消本轮、展示超时提示并恢复可输入，绝不无限转圈。

#### Scenario: done 终止所有分支转圈
- **WHEN** 任意分支（正常 / clarify / boundary / switch）收到 done
- **THEN** 本轮所有阶段停止转圈、阶段区定稿；clarify 轮 done 带空 answer 时气泡回显澄清提示（不空白）

#### Scenario: 单轮超时自关闭
- **WHEN** 发起问答后 45s 未收到 done/error
- **THEN** 前端取消本轮流，展示"响应超时，已结束本轮，请重试"，恢复可输入

### Requirement: 引用面板（灰显 → 高亮）
> 检索摘要：rerank 到达渲染精排块卡片灰显折叠，done 的 quotedKeys 命中块高亮展开、未命中保持灰显，filePath 可点查看原文。

面板 SHALL 在 `rerank` 事件到达时渲染精排块卡片（blockId/title/summary/filePath，灰显折叠，filePath 可点"查看原文"）；`done` 的 `quotedKeys` 到达后命中的块高亮展开、未命中保持灰显折叠。

#### Scenario: rerank 先灰显
- **WHEN** rerank 事件到达
- **THEN** 引用面板渲染 Top-K 块（灰显折叠），filePath 可点击查看原文（`GET /api/rag/assistant/source?path=<urlencoded>`，query 传参）

#### Scenario: done 后高亮命中
- **WHEN** done 携带 quotedKeys
- **THEN** 命中的块高亮展开，未命中保持灰显折叠

### Requirement: 成本展示与会话结算
> 检索摘要：每轮 done 展示 tokensUsage 四字段（prompt/completion/cacheHit/total）累计进头部；"结束对话"调 close 返回会话累计 token 与轮数。

面板 SHALL 展示每轮 `done.tokensUsage`（prompt/completion/cacheHit/total）；提供"结束对话"按钮调 `POST /sessions/{sessionId}/close`，返回后展示会话累计 token 与轮数（"本次对话总消耗"）。

#### Scenario: 本轮成本展示
- **WHEN** 每轮 done 到达
- **THEN** 展示本轮 tokensUsage 四字段，累计进头部

#### Scenario: 结束对话结算
- **WHEN** 学生点击"结束对话"
- **THEN** 调 close 接口，展示会话累计 token + 轮数

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-frontend-rag-assistant-frontend-rag-assistant-ui.md`（§Requirement 轮次防卡死 §Requirement 引用面板 §Requirement 成本展示与会话结算）
