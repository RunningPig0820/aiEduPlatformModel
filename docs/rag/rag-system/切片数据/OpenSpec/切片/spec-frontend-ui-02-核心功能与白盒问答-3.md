# 核心功能与白盒问答
> summary: 核心功能与白盒问答-3（澄清点选/非学生占位/断线补查）
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-frontend-ui-02-核心功能与白盒问答-3.md
> 类别：操作流程

---

> 检索摘要（业务向）：前端 spec：clarify 候选 chips 点选（candidates 字符串 id 数组、id→label 映射、点选=重发原问+currentProject、switch 提示）、非学生占位（非 STUDENT 不发起 ask 不硬报错）、断线补查（permission.traceId 调 turns、done 回显校验、trace 过期 10002 提示重发）的 MUST 要求与 scenario 是什么？

### Requirement: 澄清点选交互
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

### Requirement: 非学生占位
> 检索摘要：面板读取当前用户角色并在头部展示，角色非 STUDENT 展示"当前非学生无法使用"占位、不发起 ask，不硬报错。

面板 SHALL 读取当前用户角色并在头部展示；角色非 STUDENT SHALL 展示"当前非学生无法使用"占位，不发起 ask。

#### Scenario: 非学生占位
- **WHEN** 当前登录角色为 TEACHER/ADMIN 或缺失
- **THEN** 面板展示"当前非学生无法使用"，不发起 ask，不硬报错

### Requirement: 断线补查
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

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-frontend-rag-assistant-frontend-rag-assistant-ui.md`（§Requirement 澄清点选交互 §Requirement 非学生占位 §Requirement 断线补查）
