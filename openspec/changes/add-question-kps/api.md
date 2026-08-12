# decide 契约扩展 — question_kps 字段 API 文档

> 基础路径: `/api/tutoring`(内部调用,需 `x-internal-token`)
>
> 更新日期: 2026-08-12
>
> 本文档只描述本 change 的增量字段。decide 完整 SSE 契约见归档 `2026-08-12-tutoring-agent-protocol/api.md`。

---

## 1. POST /api/tutoring/decide — meta 事件新增字段

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/tutoring/decide` |
| Content-Type | `application/json` |
| 需要登录 | 否(内部调用,校验 `x-internal-token` header) |
| 响应 | SSE 流(`text/event-stream`) |

### 响应参数(增量)

SSE `meta` 事件的数据(`ActionMeta`)**新增**一个可选字段:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question_kps | Array\<String\> | 否 | 题目涉及知识点列表(如 `["二元一次方程组"]`);可空 `null`。前端「知识点分析」阶段数据源 |

其余字段(`type` / `reason` / `eval` / `mastery_signals` / `new_question` / `end_reason` / `summary` / `safety_flag` / `degraded`)不变。

### 响应示例(meta 事件)

```
event: meta
data: {"type": "hint", "reason": "学生已列方程", "question_kps": ["二元一次方程组"], "eval": {...}, "mastery_signals": [...], "safety_flag": false, "degraded": false}
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 403 | - | `x-internal-token` 缺失/错误 |
| 422 | - | 请求体 Pydantic 校验失败 |
| 500 | decide failed | decide 异常(error 事件) |

---

## 前端调用注意事项

### 1. 字段可空处理

`question_kps` 可能为 `null` 或缺失 —— 前端「知识点分析」阶段显示占位"—",不得因空字段报错。

### 2. 向后兼容

新增字段为 additive:旧前端/旧 Java 解析时忽略该字段;新前端在旧后端上该字段恒缺失 → 同样按占位处理。

### 3. 消费位置

前端从 `meta` 事件(而非 `meta.eval`)读取 `questionKps`,与 `reason` / `masterySignals` 同级。
