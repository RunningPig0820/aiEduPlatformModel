# 教材知识点关联 API 接口文档

> 基础路径: `/api/kg`
>
> 更新日期: 2026-04-07

---

## 目录

- [通用响应结构](#通用响应结构)
- [1. 导入教材章节](#1-导入教材章节)
- [2. 查询章节列表](#2-查询章节列表)
- [3. 知识点匹配](#3-知识点匹配)
- [4. 确认关联关系](#4-确认关联关系)
- [5. PDF OCR 识别](#5-pdf-ocr-识别)
- [6. 课标知识点提取](#6-课标知识点提取)

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

## 1. 导入教材章节

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/kg/textbook/import` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 请求参数

**RequestBody**

```json
{
  "stage": "middle",
  "grade": "七年级",
  "semester": "上册"
}
```

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| stage | String | 否 | primary/middle/high | 学段，不传则导入全部 |
| grade | String | 否 | - | 年级，如"七年级" |
| semester | String | 否 | 上册/下册 | 学期 |

### 响应参数

成功时 `data` 返回：

```json
{
  "imported_count": 29,
  "chapters": [
    {
      "name": "人教版_数学_七年级_上册_第一章_有理数",
      "grade": "七年级",
      "semester": "上册"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| imported_count | Integer | 导入章节数量 |
| chapters | Array | 导入的章节列表 |

### 请求示例

**cURL:**
```bash
curl -X POST http://localhost:8000/api/kg/textbook/import \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"stage": "middle", "grade": "七年级", "semester": "上册"}'
```

**JavaScript (fetch):**
```javascript
const response = await fetch('/api/kg/textbook/import', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ stage: 'middle', grade: '七年级', semester: '上册' })
});
const result = await response.json();
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 20001 | 教材文件不存在 | 指定的教材文件未找到 |
| 20002 | Neo4j 连接失败 | 数据库连接异常 |

---

## 2. 查询章节列表

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/textbook/chapters` |
| Content-Type | `application/json` |
| 需要登录 | 否 |

### 请求参数

**Query**

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| grade | String | 否 | - | 年级 |
| semester | String | 否 | 上册/下册 | 学期 |
| chapter_name | String | 否 | - | 章节名称（模糊匹配） |

### 响应参数

成功时 `data` 返回：

```json
{
  "total": 29,
  "chapters": [
    {
      "name": "人教版_数学_七年级_上册_第一章_有理数",
      "publisher": "人教版",
      "subject": "数学",
      "grade": "七年级",
      "semester": "上册",
      "chapter": "第一章有理数",
      "order": 1,
      "knowledge_points": ["有理数", "数轴", "相反数"]
    }
  ]
}
```

### 请求示例

**cURL:**
```bash
curl "http://localhost:8000/api/kg/textbook/chapters?grade=七年级&semester=上册"
```

---

## 3. 知识点匹配

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/kg/textbook/link/match` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 请求参数

**RequestBody**

```json
{
  "stage": "middle",
  "use_llm": true
}
```

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| stage | String | 否 | primary/middle/high | 学段 |
| use_llm | Boolean | 否 | - | 是否使用 LLM 模糊匹配，默认 false |

### 响应参数

成功时 `data` 返回：

```json
{
  "total_textbook_kps": 346,
  "matched_count": 24,
  "unmatched_count": 322,
  "match_rate": "6%",
  "matches": [
    {
      "textbook_kp": "一元一次方程",
      "concept_label": "一元一次方程",
      "match_type": "exact",
      "confidence": 1.0
    },
    {
      "textbook_kp": "正数和负数的概念",
      "concept_label": "正数",
      "match_type": "fuzzy",
      "confidence": 0.8
    }
  ]
}
```

---

## 4. 确认关联关系

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/kg/textbook/link/confirm` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 请求参数

**RequestBody**

```json
{
  "chapter_name": "人教版_数学_七年级_上册_第一章_有理数",
  "concept_labels": ["有理数", "数轴", "相反数"],
  "create_missing": [
    {
      "label": "凑十法",
      "types": ["代数概念"]
    }
  ]
}
```

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| chapter_name | String | 是 | - | 章节名称 |
| concept_labels | Array | 是 | - | 已匹配的 Concept 标签列表 |
| create_missing | Array | 否 | - | 需要新创建的知识点 |

### 响应参数

成功时 `data` 返回：

```json
{
  "created_relations": 3,
  "created_concepts": 1,
  "chapter_name": "人教版_数学_七年级_上册_第一章_有理数"
}
```

---

## 5. PDF OCR 识别

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/ocr/pdf` |
| Content-Type | `multipart/form-data` |
| 需要登录 | 是 |

### 请求参数

**FormData**

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| file | File | 是 | PDF 文件 | PDF 文件 |
| pages | String | 否 | 如 "1-10" | 指定识别页码范围 |

### 响应参数

成功时 `data` 返回：

```json
{
  "total_pages": 189,
  "extracted_pages": 10,
  "pages": [
    {
      "page_num": 1,
      "text": "义务教育数学课程标准..."
    }
  ]
}
```

---

## 6. 课标知识点提取

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/ocr/curriculum` |
| Content-Type | `multipart/form-data` |
| 需要登录 | 是 |

### 请求参数

**FormData**

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| file | File | 是 | PDF 文件 | 课标 PDF 文件 |
| subject | String | 是 | math/physics/chemistry | 学科 |

### 响应参数

成功时 `data` 返回：

```json
{
  "subject": "math",
  "stages": [
    {
      "stage": "第一学段",
      "grades": "1-2年级",
      "domains": [
        {
          "domain": "数与代数",
          "knowledge_points": ["20以内数的认识", "加减法"]
        }
      ]
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
| 10002 | 实体不存在 | 请求的资源不存在 |
| 10003 | 参数无效 | 参数校验失败 |
| 10004 | 未登录 | 用户未登录或 Token 过期 |

### 知识图谱错误码 (2xxxx)

| code | message | 说明 |
|------|---------|------|
| 20001 | 教材文件不存在 | 指定的教材文件未找到 |
| 20002 | Neo4j 连接失败 | 数据库连接异常 |
| 20003 | Concept 不存在 | 知识点不存在 |
| 20004 | 章节不存在 | 指定章节不存在 |

### OCR 错误码 (3xxxx)

| code | message | 说明 |
|------|---------|------|
| 30001 | 文件格式错误 | 不是有效的 PDF 文件 |
| 30002 | OCR 引擎初始化失败 | PaddleOCR 初始化异常 |
| 30003 | 页码范围无效 | 指定的页码超出范围 |

---

## 前端调用注意事项

### 1. 认证管理

本系统使用 JWT Token 进行认证，前端需要：

- **携带 Token**: 所有需要登录的接口，请求时必须携带 `Authorization: Bearer <token>` 头
- **Token 刷新**: Token 过期后需调用刷新接口获取新 Token

```javascript
const token = localStorage.getItem('token');
fetch('/api/kg/textbook/import', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### 2. 文件上传

PDF OCR 接口使用 `multipart/form-data`，需使用 FormData：

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/api/ocr/pdf', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

---

*文档生成时间: 2026-04-07*