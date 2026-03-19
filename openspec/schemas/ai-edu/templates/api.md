# {模块名称} API 接口文档

> 基础路径: `/api/{module}`
>
> 更新日期: {YYYY-MM-DD}

---

## 目录

- [通用响应结构](#通用响应结构)
<!-- 根据接口数量动态生成目录 -->

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

## 1. {接口名称}

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `{GET/POST/PUT/DELETE}` |
| 接口路径 | `/api/{module}/{path}` |
| Content-Type | `application/json` |
| 需要登录 | {是/否} |

### 请求参数

**{RequestBody / Path / Query}**

```json
{
  "field1": "value1",
  "field2": "value2"
}
```

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| field1 | String | 是 | {校验规则} | {说明} |
| field2 | String | 否 | {校验规则} | {说明} |

### 响应参数

成功时 `data` 返回：

```json
{
  "id": 1,
  "name": "示例"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | ID |
| name | String | 名称 |

### 请求示例

**cURL:**
```bash
curl -X POST http://localhost:8000/api/{module}/{path} \
  -H "Content-Type: application/json" \
  -d '{"field1": "value1"}'
```

**JavaScript (fetch):**
```javascript
const response = await fetch('/api/{module}/{path}', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include', // 如需携带 Cookie
  body: JSON.stringify({ field1: 'value1' })
});
const result = await response.json();
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| {code} | {message} | {说明} |

---

## 错误码说明

### 通用错误码 (1xxxx)

| code | message | 说明 |
|------|---------|------|
| 00000 | success | 成功 |
| 10000 | 系统错误 | 服务器内部错误 |
| 10001 | 参数错误 | 请求参数格式不正确 |
| 10002 | 实体不存在 | 请求的资源不存在 |
| 10003 | 参数无效 | 参数校验失败 |
| 10004 | 未登录 | 用户未登录或 Token 过期 |

### {模块名称}错误码 ({prefix}xxxx)

| code | message | 说明 |
|------|---------|------|
| {code} | {message} | {说明} |

---

## 前端调用注意事项

### 1. 认证管理

本系统使用 JWT Token 进行认证，前端需要：

- **携带 Token**: 所有需要登录的接口，请求时必须携带 `Authorization: Bearer <token>` 头
- **Token 刷新**: Token 过期后需调用刷新接口获取新 Token
- **跨域配置**: 开发环境需配置 CORS

```javascript
// fetch 请求示例
const token = localStorage.getItem('token');
fetch('/api/xxx', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### 2. 参数校验

后端使用 Pydantic 进行参数校验，校验失败会返回 `code: 10001` 或 `code: 10003`。

---

*文档生成时间: {YYYY-MM-DD}*