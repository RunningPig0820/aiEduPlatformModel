# milestone-01-role-gate Specification

## Purpose

M1 交付"权限判断"切片——RAG 助手的角色硬门。本切片是整条链最独立的环节（纯 Java、零 Python 依赖、不进 RAG 流程、0 token），是第一个可前后端对接测试的里程碑，为后续所有切片提供"学生才能进入"的前置保障。

## ADDED Requirements

### Requirement: 角色硬门切片可独立交付

M1 SHALL 交付可独立对接测试的权限判断切片：从可信 session 取角色（`HttpSession.getAttribute("role")`），仅 STUDENT 放行；非学生/角色缺失 → 固定 403 响应体；不进 RAG 流程、不调 LLM、不产生 trace。前端 body 传 role 一律忽略。

#### Scenario: 学生放行

- **WHEN** session 角色 = STUDENT，发起问答请求
- **THEN** 进入 RAG 流程，SSE 首个事件为 `permission{allowed:true}`

#### Scenario: 非学生拒绝

- **WHEN** session 角色 = TEACHER，发起问答请求
- **THEN** 返回固定 403"仅学生可访问此助手"，不产生 trace、不调 LLM

#### Scenario: 角色缺失拒绝

- **WHEN** 无有效 session 或角色缺失，发起问答请求
- **THEN** 返回固定 403，不进入 RAG 流程

#### Scenario: body 传 role 被忽略

- **WHEN** session 角色 = TEACHER，body 携带 role=STUDENT，发起问答请求
- **THEN** 仍按 session 角色拒绝（403），证明不信任前端传参

### Requirement: 里程碑对接测试验收

M1 SHALL 以 RAG-GATE-001~004 四条约谈用例作为完成标准：学生放行 / 教师 403 / 角色缺失 403 / body role 忽略，全部通过才进入 M2。

#### Scenario: 对接测试全绿

- **WHEN** 前后端完成 M1 对接（非学生见固定 403 页，学生放行进入占位流程）
- **THEN** RAG-GATE-001~004 全部通过，M1 视为完成

#### Scenario: 前端可见物

- **WHEN** 非学生访问助手入口
- **THEN** 前端展示固定 403 提示页，不发起任何 RAG 请求
