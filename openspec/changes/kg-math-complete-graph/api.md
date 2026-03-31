# 数学知识图谱 API 接口文档

> 基础路径: `/api/kg/math`
>
> 更新日期: 2026-03-31

---

## 目录

- [通用响应结构](#通用响应结构)
- [1. 按教材查询知识点](#1-按教材查询知识点)
- [2. 按章节查询知识点](#2-按章节查询知识点)
- [3. 查询知识点学习路径](#3-查询知识点学习路径)
- [4. 查询教材覆盖统计](#4-查询教材覆盖统计)

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

## 1. 按教材查询知识点

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/math/textbook/{textbook_id}/knowledge-points` |
| Content-Type | `application/json` |
| 需要登录 | 否 |

### 请求参数

**Path**

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| textbook_id | String | 是 | 非空 | 教材ID，如 "middle-grade7-shang" |

**Query**

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| status | String | 否 | 枚举值 | 筛选状态：auto_mapped/needs_review/no_match |

### 响应参数

成功时 `data` 返回：

```json
{
  "textbook": {
    "id": "middle-grade7-shang",
    "name": "七年级上册",
    "stage": "middle",
    "grade": "七年级"
  },
  "chapters": [
    {
      "id": "ch-001",
      "name": "有理数",
      "knowledge_points": [
        {
          "id": "tkp-001",
          "name": "正数和负数的概念",
          "status": "auto_mapped",
          "confidence": 0.95,
          "mapped_kp": {
            "id": "statement#1622",
            "name": "正数的定义",
            "type": "数学定义"
          }
        }
      ]
    }
  ],
  "statistics": {
    "total": 45,
    "auto_mapped": 38,
    "needs_review": 5,
    "no_match": 2
  }
}
```

### 请求示例

**cURL:**
```bash
curl -X GET "http://localhost:8000/api/kg/math/textbook/middle-grade7-shang/knowledge-points"
```

**JavaScript (fetch):**
```javascript
const response = await fetch('/api/kg/math/textbook/middle-grade7-shang/knowledge-points');
const result = await response.json();
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 10002 | 教材不存在 | 指定的 textbook_id 不存在 |

---

## 2. 按章节查询知识点

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/math/chapter/{chapter_id}/knowledge-points` |
| Content-Type | `application/json` |
| 需要登录 | 否 |

### 请求参数

**Path**

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| chapter_id | String | 是 | 非空 | 章节ID |

### 响应参数

成功时 `data` 返回：

```json
{
  "chapter": {
    "id": "ch-001",
    "name": "有理数",
    "textbook": {
      "id": "middle-grade7-shang",
      "name": "七年级上册"
    }
  },
  "knowledge_points": [
    {
      "id": "tkp-001",
      "name": "正数和负数的概念",
      "status": "auto_mapped",
      "confidence": 0.95,
      "mapped_kp": {
        "id": "statement#1622",
        "name": "正数的定义",
        "type": "数学定义",
        "related_to": ["正实数", "正数"]
      }
    }
  ]
}
```

---

## 3. 查询知识点学习路径

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/math/knowledge-point/{kp_id}/learning-path` |
| Content-Type | `application/json` |
| 需要登录 | 否 |

### 请求参数

**Path**

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| kp_id | String | 是 | 非空 | 知识点ID |

### 响应参数

成功时 `data` 返回：

```json
{
  "knowledge_point": {
    "id": "statement#1622",
    "name": "正数的定义",
    "type": "数学定义"
  },
  "learning_context": {
    "textbook": {
      "id": "middle-grade7-shang",
      "name": "七年级上册"
    },
    "chapter": {
      "id": "ch-001",
      "name": "有理数"
    },
    "section": {
      "id": "sec-001",
      "name": "1.1 正数和负数"
    }
  },
  "prerequisites": [
    {
      "id": "statement#100",
      "name": "自然数的认识",
      "source": "PREREQUISITE"
    }
  ]
}
```

---

## 4. 查询教材覆盖统计

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/math/textbook/coverage` |
| Content-Type | `application/json` |
| 需要登录 | 否 |

### 响应参数

成功时 `data` 返回：

```json
{
  "summary": {
    "total_textbooks": 24,
    "total_chapters": 312,
    "total_textbook_kps": 3524,
    "auto_mapped": 2980,
    "needs_review": 389,
    "no_match": 155
  },
  "by_stage": [
    {
      "stage": "primary",
      "textbooks": 12,
      "chapters": 156,
      "knowledge_points": 1420,
      "coverage_rate": 0.89
    },
    {
      "stage": "middle",
      "textbooks": 6,
      "chapters": 78,
      "knowledge_points": 1245,
      "coverage_rate": 0.92
    },
    {
      "stage": "high",
      "textbooks": 6,
      "chapters": 78,
      "knowledge_points": 859,
      "coverage_rate": 0.78
    }
  ],
  "unmatched_report": "/api/kg/math/textbook/unmatched/export"
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
| 10002 | 实体不存在 | 请求的资源不存在 |
| 10003 | 参数无效 | 参数校验失败 |

### 知识图谱错误码 (3xxxx)

| code | message | 说明 |
|------|---------|------|
| 30001 | 知识点不存在 | 指定的知识点ID不存在 |
| 30002 | 教材不存在 | 指定的教材ID不存在 |
| 30003 | 章节不存在 | 指定的章节ID不存在 |
| 30004 | 无匹配数据 | 知识点未匹配到教材 |

---

## 前端调用注意事项

### 1. 数据缓存

教材数据更新频率低，前端可缓存教材列表和章节结构：
- 缓存时间：24小时
- 缓存键：`kg_math_textbooks`

### 2. 分页处理

知识点列表接口支持分页，默认每页 20 条：
- 添加 `?page=1&size=20` 参数

---

*文档生成时间: 2026-03-31*