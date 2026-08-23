# RAG 评测 agent API 接口文档

> 基础路径: `/api/rag/eval`
>
> 更新日期: 2026-08-21
>
> 调用方: Java 后端 / 前端评测观测页（内部调用，需 `x-internal-token`）

---

## 目录

- [通用响应结构](#通用响应结构)
- [1. 触发评测](#1-触发评测)
- [2. 查询评测报告](#2-查询评测报告)
- [错误码说明](#错误码说明)
- [前端调用注意事项](#前端调用注意事项)

---

## 通用响应结构

所有接口均返回统一的 JSON 格式：

```json
{
  "code": "00000",
  "message": "success",
  "data": { ... }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | String | 状态码，`00000` 表示成功，其他为错误码 |
| message | String | 提示信息 |
| data | Object | 业务数据，可能为 null |

---

## 1. 触发评测

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/rag/eval/run` |
| Content-Type | `application/json` |
| 需要鉴权 | 是（`x-internal-token`） |

### 请求参数

**RequestBody**

```json
{
  "module": "knowledge-graph",
  "version": "2026-08-21-1"
}
```

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| module | String | 否 | 覆盖模块 id；缺省=全量 | 只评测指定模块 |
| version | String | 否 | 语料版本标识 | 用于报告对比；缺省用时间戳 |

### 响应参数

成功时 `data` 返回：

```json
{
  "run_id": "eval-20260821-1530-001",
  "module": "knowledge-graph",
  "status": "running"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| run_id | String | 评测运行 id（查询报告用） |
| module | String\|null | 评测范围（null=全量） |
| status | String | `running`/`done`/`failed` |

### 请求示例

**cURL:**
```bash
curl -X POST http://localhost:8000/api/rag/eval/run \
  -H "Content-Type: application/json" \
  -H "x-internal-token: $INTERNAL_TOKEN" \
  -d '{"module": "knowledge-graph", "version": "2026-08-21-1"}'
```

**JavaScript (fetch):**
```javascript
const response = await fetch('/api/rag/eval/run', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'x-internal-token': token },
  body: JSON.stringify({ module: 'knowledge-graph', version: '2026-08-21-1' })
});
const result = await response.json();
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 10000 | 系统错误 | 评测集缺失/检索不可用 |
| 10001 | 参数错误 | module 非法 |
| 10004 | 未登录 | token 无效 |

---

## 2. 查询评测报告

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/rag/eval/report` |
| Content-Type | `application/json` |
| 需要鉴权 | 是（`x-internal-token`） |

### 请求参数

**Query**

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| run_id | String | 是 | 评测运行 id | 目标评测 |
| compare_with | String | 否 | 另一个 run_id | 版本对比（新旧 hit@k/质量分） |

### 响应参数

成功时 `data` 返回：

```json
{
  "run_id": "eval-20260821-1530-001",
  "version": "2026-08-21-1",
  "status": "done",
  "summary": {
    "hit_at_3": 0.8,
    "avg_quality": 4.2,
    "total_cost_yuan": 0.15,
    "avg_latency_ms": 850
  },
  "by_module": [
    {
      "module": "knowledge-graph",
      "hit_at_3": 0.8,
      "avg_quality": 4.2,
      "total_cost_yuan": 0.15,
      "avg_latency_ms": 850
    }
  ],
  "compare": {
    "prev_run_id": "eval-20260820-1000-001",
    "hit_at_3_delta": 0.15,
    "avg_quality_delta": 0.3
  },
  "trace_url": "/api/rag/eval/trace?run_id=eval-20260821-1530-001"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| run_id | String | 评测运行 id |
| version | String | 语料版本标识 |
| status | String | `running`/`done`/`failed` |
| summary | Object | 全量指标：hit@3 / 平均质量分 / 总成本 / 平均耗时 |
| by_module | Array | 按模块指标明细 |
| compare | Object\|null | 与历史版本对比（delta），未传 compare_with 时为 null |
| trace_url | String | trace 查看路径 |

### 请求示例

**cURL:**
```bash
curl -X GET "http://localhost:8000/api/rag/eval/report?run_id=eval-20260821-1530-001&compare_with=eval-20260820-1000-001" \
  -H "x-internal-token: $INTERNAL_TOKEN"
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 10000 | 系统错误 | run_id 不存在 |
| 10001 | 参数错误 | run_id 缺失 |
| 10004 | 未登录 | token 无效 |

---

## 错误码说明

### 通用错误码 (1xxxx)

| code | message | 说明 |
|------|---------|------|
| 00000 | success | 成功 |
| 10000 | 系统错误 | 服务器内部错误 |
| 10001 | 参数错误 | 请求参数格式不正确 |
| 10004 | 未登录 | `x-internal-token` 缺失或无效 |

---

## 前端调用注意事项

### 1. 认证

内部调用须携带 `x-internal-token` 头（与 `/api/rag/ask` 一致）。

### 2. 评测是异步的

`/eval/run` 立即返回 `run_id` + `status=running`；前端轮询 `/eval/report` 直到 `status=done`。

### 3. 版本对比

- 整理语料后重新评测时传 `version`（如日期-序号）；查询时 `compare_with` 上一次 run_id，前端展示 delta（📈/📉）。

### 4. 观测页建议

- 展示 summary 指标卡 + 按模块柱状图 + 版本对比折线 + trace 明细表（点开看单条 query 的召回/得分/判分）。
- 目标：面试时直接亮"hit@3 80%、平均质量 4.2/5、单次评测成本 ¥0.15"这类数字。

---

*文档生成时间: 2026-08-21*
