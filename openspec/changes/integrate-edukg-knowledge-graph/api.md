# 知识图谱 API 接口文档

> 基础路径: `/api/kg`
>
> 更新日期: 2026-03-26

---

## 目录

- [通用响应结构](#通用响应结构)
- [1. 搜索知识点实体](#1-搜索知识点实体)
- [2. 获取实体详情](#2-获取实体详情)
- [3. 文本实体链接](#3-文本实体链接)
- [4. 获取学科知识树](#4-获取学科知识树)
- [5. 获取学科分类列表](#5-获取学科分类列表)
- [6. 获取学生知识点进度](#6-获取学生知识点进度)
- [7. 更新学生知识点进度](#7-更新学生知识点进度)
- [8. 获取学生进度统计](#8-获取学生进度统计)
- [9. 获取知识点推荐](#9-获取知识点推荐)
- [10. 获取学习路径](#10-获取学习路径)
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

## 1. 搜索知识点实体

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/entities` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 请求参数

**Query Parameters**

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| label | String | 是 | 最大100字符 | 知识点名称（支持模糊匹配） |
| subject | String | 否 | 枚举值 | 学科：chinese, math, english, physics, chemistry, biology, history, geo, politics |
| limit | Integer | 否 | 1-100，默认20 | 返回数量限制 |

### 响应参数

成功时 `data` 返回：

```json
{
  "total": 2,
  "entities": [
    {
      "uri": "http://edukg.org/knowledge/3.0/instance/math#quadratic-equation-001",
      "label": "一元二次方程",
      "subject": "math",
      "classLabel": "方程与不等式"
    },
    {
      "uri": "http://edukg.org/knowledge/3.0/instance/math#quadratic-function-001",
      "label": "二次函数",
      "subject": "math",
      "classLabel": "函数"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| total | Integer | 匹配总数 |
| entities | Array | 实体列表 |
| entities[].uri | String | 实体唯一标识 |
| entities[].label | String | 实体名称 |
| entities[].subject | String | 所属学科 |
| entities[].classLabel | String | 所属分类名称 |

### 请求示例

**cURL:**
```bash
curl -X GET "http://localhost:8000/api/kg/entities?label=方程&subject=math&limit=10" \
  -H "Authorization: Bearer <token>"
```

**JavaScript (fetch):**
```javascript
const response = await fetch('/api/kg/entities?label=方程&subject=math&limit=10', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const result = await response.json();
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 10001 | 参数错误 | label 参数缺失或格式错误 |
| 20001 | 学科不存在 | subject 不是有效的学科枚举值 |

---

## 2. 获取实体详情

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/entity/{uri}` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 请求参数

**Path Parameters**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uri | String | 是 | URL编码后的实体URI |

### 响应参数

成功时 `data` 返回：

```json
{
  "uri": "http://edukg.org/knowledge/3.0/instance/math#quadratic-equation-001",
  "label": "一元二次方程",
  "subject": "math",
  "description": "只含有一个未知数，且未知数的最高次数为2的整式方程",
  "properties": [
    {
      "key": "定义",
      "value": "形如ax²+bx+c=0的方程"
    }
  ],
  "relationships": {
    "prerequisites": [
      {
        "uri": "http://edukg.org/knowledge/3.0/instance/math#equation-001",
        "label": "方程"
      }
    ],
    "relatedTo": [
      {
        "uri": "http://edukg.org/knowledge/3.0/instance/math#quadratic-function-001",
        "label": "二次函数",
        "relation": "关联"
      }
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| uri | String | 实体唯一标识 |
| label | String | 实体名称 |
| subject | String | 所属学科 |
| description | String | 实体描述 |
| properties | Array | 属性列表 |
| relationships | Object | 关系信息 |
| relationships.prerequisites | Array | 前置知识点 |
| relationships.relatedTo | Array | 相关知识点 |

### 请求示例

**cURL:**
```bash
curl -X GET "http://localhost:8000/api/kg/entity/http%3A%2F%2Fedukg.org%2Fknowledge%2F3.0%2Finstance%2Fmath%23quadratic-equation-001" \
  -H "Authorization: Bearer <token>"
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 10002 | 实体不存在 | URI 对应的实体不存在 |

---

## 3. 文本实体链接

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/kg/link` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 请求参数

**RequestBody**

```json
{
  "text": "一元二次方程的解法包括配方法、公式法和因式分解法",
  "subject": "math",
  "enrichContext": true
}
```

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| text | String | 是 | 最大10000字符 | 待识别的文本内容 |
| subject | String | 否 | 枚举值 | 学科上下文，用于消歧 |
| enrichContext | Boolean | 否 | 默认false | 是否返回实体的图谱上下文 |

### 响应参数

成功时 `data` 返回：

```json
{
  "entities": [
    {
      "label": "一元二次方程",
      "uri": "http://edukg.org/knowledge/3.0/instance/math#quadratic-equation-001",
      "positions": [
        {"start": 0, "end": 6}
      ],
      "context": "只含有一个未知数，且未知数的最高次数为2的整式方程"
    },
    {
      "label": "配方法",
      "uri": "http://edukg.org/knowledge/3.0/instance/math#completing-square-001",
      "positions": [
        {"start": 10, "end": 13}
      ]
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| entities | Array | 识别到的实体列表 |
| entities[].label | String | 实体名称 |
| entities[].uri | String | 实体URI |
| entities[].positions | Array | 在文本中的位置 |
| entities[].context | String | 实体上下文（仅enrichContext=true时返回） |

### 请求示例

**cURL:**
```bash
curl -X POST http://localhost:8000/api/kg/link \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"text": "一元二次方程的解法包括配方法", "subject": "math"}'
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 10001 | 参数错误 | text 参数缺失或为空 |

---

## 4. 获取学科知识树

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/subject/{subject}/tree` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 请求参数

**Path Parameters**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| subject | String | 是 | 学科标识 |

**Query Parameters**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| depth | Integer | 否 | 树深度，默认3，最大5 |
| studentId | String | 否 | 学生ID，返回时包含学习进度 |

### 响应参数

成功时 `data` 返回：

```json
{
  "subject": "math",
  "tree": {
    "id": "root",
    "label": "数学",
    "type": "class",
    "progress": "mastered",
    "children": [
      {
        "id": "http://edukg.org/knowledge/3.0/class/math#main-C10",
        "label": "方程与不等式",
        "type": "class",
        "progress": "in_progress",
        "children": [
          {
            "id": "http://edukg.org/knowledge/3.0/instance/math#equation-001",
            "label": "方程",
            "type": "entity",
            "progress": "mastered"
          }
        ]
      }
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| subject | String | 学科标识 |
| tree | Object | 知识树根节点 |
| tree.id | String | 节点ID |
| tree.label | String | 节点名称 |
| tree.type | String | 节点类型：class(分类) / entity(实体) |
| tree.progress | String | 学习进度：mastered / in_progress / not_started (仅studentId存在时返回) |
| tree.children | Array | 子节点列表 |

### 请求示例

**cURL:**
```bash
curl -X GET "http://localhost:8000/api/kg/subject/math/tree?depth=3&studentId=student_001" \
  -H "Authorization: Bearer <token>"
```

---

## 5. 获取学科分类列表

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/subject/{subject}/classes` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 请求参数

**Path Parameters**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| subject | String | 是 | 学科标识 |

### 响应参数

```json
{
  "classes": [
    {
      "uri": "http://edukg.org/knowledge/3.0/class/math#main-C10",
      "label": "方程与不等式",
      "entityCount": 156
    }
  ]
}
```

---

## 6. 获取学生知识点进度

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/student/{studentId}/progress` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| studentId | String | 是 | 学生ID (Path) |
| subject | String | 否 | 学科过滤 (Query) |

### 响应参数

```json
{
  "studentId": "student_001",
  "progress": [
    {
      "entityUri": "http://edukg.org/knowledge/3.0/instance/math#equation-001",
      "entityLabel": "方程",
      "subject": "math",
      "status": "mastered",
      "score": 95,
      "updatedAt": "2026-03-20T10:30:00Z"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| status | String | 状态：mastered / in_progress / not_started |
| score | Integer | 掌握分数 (0-100) |

---

## 7. 更新学生知识点进度

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/kg/student/{studentId}/progress` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 请求参数

```json
{
  "entityUri": "http://edukg.org/knowledge/3.0/instance/math#equation-001",
  "status": "mastered",
  "score": 95
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| entityUri | String | 是 | 知识点URI |
| status | String | 是 | 状态：mastered / in_progress / not_started |
| score | Integer | 否 | 分数 (0-100) |

### 响应参数

```json
{
  "success": true,
  "progress": {
    "entityUri": "http://edukg.org/knowledge/3.0/instance/math#equation-001",
    "status": "mastered",
    "score": 95,
    "updatedAt": "2026-03-26T15:00:00Z"
  }
}
```

---

## 8. 获取学生进度统计

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/student/{studentId}/statistics` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 响应参数

```json
{
  "studentId": "student_001",
  "overall": {
    "total": 1250,
    "mastered": 320,
    "inProgress": 150,
    "notStarted": 780
  },
  "bySubject": [
    {
      "subject": "math",
      "total": 200,
      "mastered": 80,
      "inProgress": 30,
      "notStarted": 90
    }
  ]
}
```

---

## 9. 获取知识点推荐

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/recommend` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| entityUri | String | 否 | 基于该知识点推荐相关内容 |
| subject | String | 否 | 学科过滤 |
| studentId | String | 否 | 学生ID，基于学习进度推荐 |

### 响应参数

```json
{
  "recommendations": [
    {
      "entityUri": "http://edukg.org/knowledge/3.0/instance/math#quadratic-function-001",
      "label": "二次函数",
      "reason": "与当前知识点强相关",
      "difficulty": "medium",
      "mastered": false
    }
  ]
}
```

---

## 10. 获取学习路径

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/learning-path` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| targetEntityUri | String | 是 | 目标知识点URI |
| studentId | String | 是 | 学生ID |

### 响应参数

```json
{
  "path": [
    {
      "order": 1,
      "entityUri": "http://edukg.org/knowledge/3.0/instance/math#equation-001",
      "label": "方程",
      "status": "mastered"
    },
    {
      "order": 2,
      "entityUri": "http://edukg.org/knowledge/3.0/instance/math#linear-equation-001",
      "label": "一元一次方程",
      "status": "in_progress"
    },
    {
      "order": 3,
      "entityUri": "http://edukg.org/knowledge/3.0/instance/math#quadratic-equation-001",
      "label": "一元二次方程",
      "status": "not_started"
    }
  ]
}
```

---

## 错误码说明

### 通用错误码 (1xxxx)

| code | message | 说明 |
|------|---------|------|
| 00000 | success | 成功 |
| 10000 | 系统错误 | 服务器内部错误 |
| 10001 | 参数错误 | 请求参数格式不正确 |
| 10002 | 资源不存在 | 请求的资源不存在 |
| 10003 | 参数无效 | 参数校验失败 |
| 10004 | 未登录 | 用户未登录或 Token 过期 |

### 知识图谱错误码 (2xxxx)

| code | message | 说明 |
|------|---------|------|
| 20001 | 学科不存在 | subject 不是有效枚举值 |
| 20002 | 实体不存在 | 指定的 URI 不存在 |
| 20003 | 图谱服务不可用 | Neo4j 连接失败 |
| 20004 | 学生不存在 | 指定的学生ID不存在 |

---

## 前端调用注意事项

### 1. 认证管理

本系统使用 JWT Token 进行认证，前端需要：

- **携带 Token**: 所有接口请求时必须携带 `Authorization: Bearer <token>` 头
- **内部服务调用**: 如果从 Java 后端调用，使用 `x-internal-token` 头

```javascript
// fetch 请求示例
const token = localStorage.getItem('token');
fetch('/api/kg/entities?label=方程', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### 2. URI 编码

实体 URI 包含特殊字符，前端需要正确编码：

```javascript
const uri = 'http://edukg.org/knowledge/3.0/instance/math#equation-001';
const encodedUri = encodeURIComponent(uri);
fetch(`/api/kg/entity/${encodedUri}`);
```

### 3. 知识树渲染

知识树数据为嵌套结构，建议使用：
- **D3.js**: 使用 `d3.hierarchy()` 处理
- **ECharts**: 使用 `tree` 或 `graph` 系列

### 4. 性能优化

- 使用 `depth` 参数控制知识树深度
- 使用 `limit` 参数限制返回数量
- 大文本实体链接建议分批处理

---

*文档生成时间: 2026-03-26*