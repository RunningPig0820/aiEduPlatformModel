# AI 答疑 decide 行为收紧 — API 契约说明

> 基础路径: `/api/tutoring`
>
> 更新日期: 2026-08-13
>
> **本变更零 API 契约变更**:不新增/修改端点,不改变 `ActionMeta` 字段结构,SSE 事件序列不变。以下为受影响的内部端点说明——变化的只是服务端对相同请求返回的 `type` **取值分布**(答错不再返回 `end`/`reveal`,改为 `hint`/`approach`;无关闲聊不再返回 `end`,改为 `concept` 继续会话),请求/响应结构完全一致。

---

## 契约冻结声明

| 维度 | 状态 |
|---|---|
| 端点 | 不变(仅 decide / generate 两个内部端点) |
| 请求结构 | 不变(`DecideRequest` / `GenerateRequest` 字段零变化) |
| 响应结构 | 不变(`ActionMeta` 字段零变化;SSE 事件:decide `agent*→thinking*→meta→done`、generate `meta→token→done`) |
| 鉴权 | 不变(`x-internal-token`) |
| Java↔Python 序列化 | 不变(snake_case,无新增字段) |
| 前端 | 零改动(仅渲染 SSE,不感知服务端分类逻辑变化) |

---

## 1. 决策 decide

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/tutoring/decide` |
| Content-Type | `application/json` |
| 鉴权 | `x-internal-token`(内部调用) |
| 响应 | SSE 流 |

### 行为变化（本变更）

对相同输入,`type` 取值分布收紧：

| 学生输入 | 变更前 | 变更后 |
|---|---|---|
| 作答答错/答偏 | 偶发 `end`(误判无关)/ 偶发 `reveal`(误判要答案) | 恒 `hint` / `approach`,`eval.correct=false`,会话 ACTIVE |
| 明确放弃/结束 | `end(ABANDONED)` | `end(ABANDONED)`(不变) |
| 完全无关(闲聊/非数学/日常表达) | `end` | `concept`(接住+引导回题,会话 ACTIVE) |
| 过简/模糊但相关 | `concept` | `concept`(不变) |
| 明确要答案 | `reveal` | `reveal`(不变;答错不触发) |

请求/响应结构(含 SSE 事件、`ActionMeta` 字段)与 `ai-tutoring` / `tutoring-agent-protocol` 契约**完全一致**,本变更不重复展开。

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 403 | Forbidden | `x-internal-token` 缺失/错误 |
| 500 | decide failed | 流式处理异常(Java 不可重试,提示重发) |

---

## 2. 生成 generate

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/tutoring/generate` |
| Content-Type | `application/json` |
| 鉴权 | `x-internal-token`(内部调用) |
| 响应 | SSE 流 |

### 行为变化（本变更）

`action_type=end` 时的正文生成规约收紧:只说明原因/鼓励(COMPLETED/ABANDONED/ROUND_LIMIT 对齐),**禁止写入完整解答或最终数值**。其余 `action_type`(hint/approach/reveal/concept/switch)生成行为不变。

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 403 | Forbidden | `x-internal-token` 缺失/错误 |
| 500 | 生成失败 | 生成异常(Java 不可重试,提示重发) |

---

## 错误码说明

错误处理沿用 `ai-tutoring` / `tutoring-agent-protocol` 既有约定(403 鉴权、422 校验、SSE `event: error` 流内错误),本变更不新增错误码。

---

## 前端调用注意事项

前端零改动:只渲染 Java 网关转发的 SSE,`toMessage` 读 `m.type` 渲染工作流。变更后历史/实时消息的 `type` 值更稳定(答错恒为 hint/approach、无关恒为 concept 而非 end),前端无需适配;会话不再因闲聊/无关内容被终止,前端按既有 concept 气泡 + ACTIVE 状态展示。

---

*文档生成时间: 2026-08-13*
