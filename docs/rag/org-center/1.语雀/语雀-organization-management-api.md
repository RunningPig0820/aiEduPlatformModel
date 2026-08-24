# api（语雀原稿）

> 来源：https://www.yuque.com/zhangmin-jrrer/iu9s4m/org-mgmt-api
> 字数：1521 ｜ 下载：2026-08-24

# 组织管理 API 接口文档

> 基础路径: `/api`
>
> 更新日期: 2026-05-05

---

## 目录

+ [通用响应结构](#通用响应结构)
+ [1. 创建学校](#1-创建学校)
+ [2. 更新学校](#2-更新学校)
+ [3. 获取学校详情](#3-获取学校详情)
+ [4. 获取学校列表](#4-获取学校列表)
+ [5. 关联用户与学校](#5-关联用户与学校)
+ [6. 获取用户的学校列表](#6-获取用户的学校列表)
+ [错误码说明](#错误码说明)
+ [前端调用注意事项](#前端调用注意事项)

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
| --- | --- | --- |
| code | String | 状态码，`00000` 表示成功，其他为错误码 |
| message | String | 提示信息 |
| data | Object | 业务数据，可能为 null |

---

## 1. 创建学校

### 基本信息

| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `POST` |
| 接口路径 | `/api/schools` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 请求参数

**RequestBody**

```json
{
  "name": "示例学校",
  "iconUrl": "https://example.com/icon.png",
  "type": "PUBLIC",
  "stages": ["PRIMARY", "JUNIOR_HIGH"]
}
```

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
| --- | --- | --- | --- | --- |
| name | String | 是 | 非空，最长 100 字符 | 学校名称 |
| iconUrl | String | 否 | 有效 URL 格式 | 学校图标 URL |
| type | String | 是 | 枚举: PUBLIC, PRIVATE, TRAINING_INSTITUTE | 学校类型 |
| stages | String[] | 是 | 非空数组，元素为枚举值 | 包含学段 |

### 响应参数

成功时 `data` 返回：

```json
{
  "id": 1,
  "name": "示例学校",
  "iconUrl": "https://example.com/icon.png",
  "type": "PUBLIC",
  "stages": ["PRIMARY", "JUNIOR_HIGH"],
  "createdAt": "2026-05-05T10:00:00"
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | Long | 学校 ID |
| name | String | 学校名称 |
| iconUrl | String | 学校图标 URL |
| type | String | 学校类型 |
| stages | String[] | 包含学段 |
| createdAt | String | 创建时间 (ISO 8601) |

### 请求示例

**cURL:**

```bash
curl -X POST http://localhost:8080/api/schools \
  -H "Content-Type: application/json" \
  -H "Cookie: SESSION=your-session-id" \
  -d '{"name":"示例学校","type":"PUBLIC","stages":["PRIMARY","JUNIOR_HIGH"]}'
```

**JavaScript (fetch):**

```javascript
const response = await fetch('/api/schools', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    name: '示例学校',
    type: 'PUBLIC',
    stages: ['PRIMARY', 'JUNIOR_HIGH']
  })
});
const result = await response.json();
```

### 常见错误

| code | message | 说明 |
| --- | --- | --- |
| 20001 | 学校名称已存在 | 名称重复 |
| 10003 | 参数无效 | 类型或学段枚举值不合法 |
| 10004 | 未登录 | 用户未登录 |

---

## 2. 更新学校

### 基本信息

| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `PUT` |
| 接口路径 | `/api/schools/{id}` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 请求参数

**Path 参数:** `id` (Long, 必填) - 学校 ID

**RequestBody**

```json
{
  "name": "更新后的学校名称",
  "iconUrl": "https://example.com/new-icon.png",
  "type": "PRIVATE",
  "stages": ["PRIMARY", "JUNIOR_HIGH", "SENIOR_HIGH"]
}
```

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
| --- | --- | --- | --- | --- |
| name | String | 是 | 非空，最长 100 字符 | 学校名称 |
| iconUrl | String | 否 | 有效 URL 格式 | 学校图标 URL |
| type | String | 是 | 枚举值 | 学校类型 |
| stages | String[] | 是 | 非空数组 | 包含学段 |

### 响应参数

与创建学校响应结构相同。

### 请求示例

**cURL:**

```bash
curl -X PUT http://localhost:8080/api/schools/1 \
  -H "Content-Type: application/json" \
  -H "Cookie: SESSION=your-session-id" \
  -d '{"name":"更新后的名称","type":"PUBLIC","stages":["PRIMARY"]}'
```

### 常见错误

| code | message | 说明 |
| --- | --- | --- |
| 10002 | 学校不存在 | ID 对应的学校不存在 |
| 20001 | 学校名称已存在 | 新名称与其他学校重复 |

---

## 3. 获取学校详情

### 基本信息

| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `GET` |
| 接口路径 | `/api/schools/{id}` |
| 需要登录 | 是 |

### 请求参数

**Path 参数:** `id` (Long, 必填) - 学校 ID

### 响应参数

与创建学校响应结构相同。

### 请求示例

**cURL:**

```bash
curl http://localhost:8080/api/schools/1 \
  -H "Cookie: SESSION=your-session-id"
```

### 常见错误

| code | message | 说明 |
| --- | --- | --- |
| 10002 | 学校不存在 | ID 对应的学校不存在 |

---

## 4. 获取学校列表

### 基本信息

| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `GET` |
| 接口路径 | `/api/schools` |
| 需要登录 | 是 |

### 请求参数

**Query 参数**

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| page | Integer | 否 | 页码，默认 1 |
| size | Integer | 否 | 每页大小，默认 20 |
| type | String | 否 | 按学校类型筛选 |

### 响应参数

```json
{
  "total": 100,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": 1,
      "name": "示例学校",
      "iconUrl": "https://example.com/icon.png",
      "type": "PUBLIC",
      "stages": ["PRIMARY", "JUNIOR_HIGH"]
    }
  ]
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| total | Long | 总记录数 |
| page | Integer | 当前页码 |
| size | Integer | 每页大小 |
| items | Array | 学校列表 |

### 请求示例

**cURL:**

```bash
curl "http://localhost:8080/api/schools?page=1&size=20" \
  -H "Cookie: SESSION=your-session-id"
```

---

## 5. 关联用户与学校

### 基本信息

| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `POST` |
| 接口路径 | `/api/schools/{schoolId}/users` |
| Content-Type | `application/json` |
| 需要登录 | 是（管理员权限） |

### 请求参数

**Path 参数:** `schoolId` (Long, 必填) - 学校 ID

**RequestBody**

```json
{
  "userId": 100,
  "role": "TEACHER"
}
```

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
| --- | --- | --- | --- | --- |
| userId | Long | 是 | 正整数 | 用户 ID |
| role | String | 是 | 枚举: ADMIN, TEACHER, STUDENT, PARENT | 用户在学校的角色 |

### 响应参数

```json
{
  "id": 1,
  "schoolId": 1,
  "userId": 100,
  "role": "TEACHER",
  "createdAt": "2026-05-05T10:00:00"
}
```

### 常见错误

| code | message | 说明 |
| --- | --- | --- |
| 10002 | 学校或用户不存在 | 关联的实体不存在 |
| 20002 | 用户已关联该学校 | 重复关联 |

---

## 6. 获取用户的学校列表

### 基本信息

| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `GET` |
| 接口路径 | `/api/users/{userId}/schools` |
| 需要登录 | 是 |

### 请求参数

**Path 参数:** `userId` (Long, 必填) - 用户 ID

### 响应参数

```json
[
  {
    "schoolId": 1,
    "schoolName": "示例学校",
    "role": "TEACHER"
  }
]
```

### 常见错误

| code | message | 说明 |
| --- | --- | --- |
| 10002 | 用户不存在 | 用户 ID 无效 |

---

## 错误码说明

### 通用错误码 (1xxxx)

| code | message | 说明 |
| --- | --- | --- |
| 00000 | success | 成功 |
| 10000 | 系统错误 | 服务器内部错误 |
| 10001 | 参数错误 | 请求参数格式不正确 |
| 10002 | 实体不存在 | 请求的资源不存在 |
| 10003 | 参数无效 | 参数校验失败 |
| 10004 | 未登录 | 用户未登录或 Session 过期 |

### 组织管理错误码 (2xxxx)

| code | message | 说明 |
| --- | --- | --- |
| 20001 | 学校名称已存在 | 名称重复冲突 |
| 20002 | 用户已关联该学校 | 重复关联 |
| 20003 | 无学校访问权限 | 用户未关联目标学校 |

---

## 前端调用注意事项

### 1. Session 管理

本系统使用 Spring Session + Redis 管理 Session，前端需要：

+ **携带 Cookie**: 所有需要登录的接口，请求时必须携带 `credentials: 'include'`

```javascript
fetch('/api/schools', {
  credentials: 'include'
});
```

### 2. 参数校验

后端使用 Spring Validation 进行参数校验，校验失败会返回 `code: 10001` 或 `code: 10003`。

### 3. 枚举值

+ `type`: `PUBLIC` | `PRIVATE` | `TRAINING_INSTITUTE`
+ `stages`: `PRIMARY` | `JUNIOR_HIGH` | `SENIOR_HIGH` | `UNIVERSITY`
+ `role`: `ADMIN` | `TEACHER` | `STUDENT` | `PARENT`

---

*文档生成时间: 2026-05-05*
