# 页面化-ui-api（语雀原稿）

> 来源：https://www.yuque.com/zhangmin-jrrer/iu9s4m/yzf9lwvt8k7tebx5
> 字数：3103 ｜ 下载：2026-08-24

# 知识图谱 API 接口文档
> 基础路径: `/api/kg`
>
> 更新日期: 2026-04-17
>

---

## 目录
+ [通用响应结构](#通用响应结构)
+ [1. 全量同步](#1-全量同步)
+ [2. 查询同步状态](#2-查询同步状态)
+ [3. 同步历史记录](#3-同步历史记录)
+ [4. 获取教材列表](#4-获取教材列表)
+ [5. 获取教材章节树](#5-获取教材章节树)
+ [6. 获取小节知识点](#6-获取小节知识点)
+ [7. 获取知识点详情](#7-获取知识点详情)
+ [8. 获取年级知识体系](#8-获取年级知识体系)
+ [9. 获取年级统计](#9-获取年级统计)
+ [10. Neo4j 健康检查](#10-neo4j-健康检查)
+ [11. 批量获取概念关联](#11-批量获取概念关联)
+ [错误码说明](#错误码说明)
+ [前端调用注意事项](#前端调用注意事项)

---

## 通用响应结构
本系统所有接口均使用 `ApiResponse<T>` 统一包装：

```json
{
  "code": "00000",
  "message": "success",
  "data": { ... }
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| code | String | 状态码，`00000` 表示成功，非 `00000` 表示异常 |
| message | String | 提示信息，成功时为 "success"，失败时为错误描述 |
| data | Object | 业务数据，类型因接口而异（可能为 null） |


> **注**: 本系统中所有节点标识符均使用 `uri`（Neo4j 中的 URI），而非自增 ID。  
例如：`uri: "http://edukg.org/knowledge/3.1/textbook/一年级上册"`
>
> 下文中的响应示例仅展示 `data` 字段内容，实际返回均包裹在 `ApiResponse` 中。
>

---

## 1. 全量同步
### 基本信息
| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `POST` |
| 接口路径 | `/api/kg/sync/full` |
| 权限要求 | **需要 ADMIN 或 TEACHER 角色** |
| Content-Type | `application/json` |


### 请求参数
**Request Body（可选，不传则全量同步）**

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| subject | String | 否 | 学科过滤，如 `math` |
| phase | String | 否 | 学段过滤，如 `primary` |
| grade | String | 否 | 年级过滤，如 `一年级` |
| textbookUri | String | 否 | 指定教材 URI，精确同步某一本教材 |


### 响应参数 (`SyncResult`)
```json
{
  "syncId": 1,
  "status": "success",
  "insertedCount": 10,
  "updatedCount": 50,
  "statusChangedCount": 2,
  "reconciliationStatus": "matched",
  "duration": 5230
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| syncId | Long | 同步任务 ID |
| status | String | 同步状态：`success` / `running` / `failed` |
| insertedCount | int | 新增节点数 |
| updatedCount | int | 更新节点数 |
| statusChangedCount | int | 状态变更数（如标记为 deleted） |
| reconciliationStatus | String | 对账结果：`matched` / `mismatched` |
| duration | long | 同步耗时（毫秒） |


### 请求示例
**全量同步:**

```bash
curl -X POST http://localhost:8080/api/kg/sync/full
```

**定向同步（仅同步一年级数学）:**

```bash
curl -X POST http://localhost:8080/api/kg/sync/full \
  -H "Content-Type: application/json" \
  -d '{"subject":"math","grade":"一年级"}'
```

### 常见错误
| code | message | 说明 |
| --- | --- | --- |
| 70006 | 同步正在进行 | 已有同步任务在执行，请勿重复触发 |
| 70007 | 同步参数错误 | 请求参数格式不正确 |


---

## 2. 查询同步状态
### 基本信息
| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/sync/status` |
| 需要登录 | 否 |


### 响应参数 (`SyncStatusDTO`)
```json
{
  "status": "idle",
  "lastSyncAt": "2026-04-17T10:05:00",
  "lastSyncStatus": "success",
  "lastInsertedCount": 10,
  "lastUpdatedCount": 50,
  "lastReconciliationStatus": "matched"
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| status | String | 当前状态：`idle`（空闲） / `running`（同步中） |
| lastSyncAt | String | 最近一次同步完成时间（ISO 8601），空闲时为 null |
| lastSyncStatus | String | 最近一次同步状态：`success` / `failed` |
| lastInsertedCount | int | 最近一次同步新增数 |
| lastUpdatedCount | int | 最近一次同步更新数 |
| lastReconciliationStatus | String | 最近一次对账结果：`matched` / `mismatched` |


---

## 3. 同步历史记录
### 基本信息
| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/sync/records` |
| 需要登录 | 否 |


### 请求参数
**Query 参数**

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| page | int | 否 | 1 | 页码（从 1 开始） |
| size | int | 否 | 10 | 每页条数 |


### 响应参数 (`List<SyncRecordDTO>`)
```json
[
  {
    "id": 1,
    "syncType": "full",
    "scope": "{\"subject\":\"math\"}",
    "status": "success",
    "insertedCount": 10,
    "updatedCount": 50,
    "statusChangedCount": 2,
    "reconciliationStatus": "matched",
    "errorMessage": null,
    "startedAt": "2026-04-17T10:00:00",
    "finishedAt": "2026-04-17T10:05:00"
  }
]
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | Long | 同步记录 ID |
| syncType | String | 同步类型：`full` |
| scope | String | 同步范围（JSON 字符串），如 `{"subject":"math"}` |
| status | String | 同步状态：`success` / `failed` / `running` |
| insertedCount | int | 新增节点数 |
| updatedCount | int | 更新节点数 |
| statusChangedCount | int | 状态变更数 |
| reconciliationStatus | String | 对账结果 |
| errorMessage | String | 错误信息（失败时） |
| startedAt | String | 开始时间 |
| finishedAt | String | 完成时间 |


---

## 4. 获取教材列表
### 基本信息
| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/textbooks` |
| 需要登录 | 否 |


### 请求参数
**Query 参数**

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| subject | String | 否 | 无（查询全部） | 学科过滤 |
| phase | String | 否 | 无（查询全部） | 学段：`primary` / `middle` / `high` |


### 响应参数 (`List<KgTextbookDTO>`)
```json
[
  {
    "uri": "http://edukg.org/knowledge/3.1/textbook/一年级上册",
    "label": "一年级上册",
    "grade": "一年级",
    "phase": "primary",
    "subject": "math",
    "status": "active"
  }
]
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| uri | String | 教材 URI |
| label | String | 教材名称 |
| grade | String | 所属年级 |
| phase | String | 所属学段 |
| subject | String | 所属学科 |
| status | String | 状态：`active` / `deleted` / `merged` |


---

## 5. 获取教材章节树
### 基本信息
| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/textbooks/{uri}/chapters` |
| 需要登录 | 否 |


> 注：`{uri}` 需要 URL 编码。
>

### 响应参数 (`List<ChapterTreeNode>`)
返回章节树列表，每个章节含小节和知识点计数：

```json
[
  {
    "uri": "http://edukg.org/knowledge/3.1/chapter/准备课",
    "label": "准备课",
    "topic": "数与代数",
    "orderIndex": 1,
    "sections": [
      {
        "uri": "http://edukg.org/knowledge/3.1/section/10以内数的认识",
        "label": "10以内数的认识",
        "orderIndex": 1,
        "knowledgePointCount": 5
      }
    ]
  }
]
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| uri | String | 章节 URI |
| label | String | 章节名称 |
| topic | String | 章节所属专题 |
| orderIndex | Integer | 排序序号 |
| sections | List<SectionNode> | 小节列表（空章节会被过滤） |


**SectionNode 结构：**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| uri | String | 小节 URI |
| label | String | 小节名称 |
| orderIndex | Integer | 排序序号 |
| knowledgePointCount | Integer | 该小节包含的知识点数 |


### 常见错误
| code | message | 说明 |
| --- | --- | --- |
| 70001 | 教材不存在 | 请求的教材不存在 |


---

## 6. 获取小节知识点
### 基本信息
| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/sections/{uri}/points` |
| 需要登录 | 否 |


> 注：`{uri}` 需要 URL 编码。
>

### 响应参数 (`List<KgKnowledgePointDetailDTO>`)
返回知识点详情列表：

```json
[
  {
    "uri": "http://edukg.org/knowledge/3.1/kp/10以内数的认识",
    "label": "10以内数的认识",
    "difficulty": "easy",
    "importance": "high",
    "cognitiveLevel": "记忆",
    "sectionUri": "http://edukg.org/knowledge/3.1/section/10以内数的认识",
    "sectionLabel": "10以内数的认识",
    "chapterUri": "http://edukg.org/knowledge/3.1/chapter/准备课",
    "chapterLabel": "准备课"
  }
]
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| uri | String | 知识点 URI |
| label | String | 知识点名称 |
| difficulty | String | 难度：`easy` / `medium` / `hard` |
| importance | String | 重要程度：`high` / `medium` / `low` |
| cognitiveLevel | String | 认知层级：`记忆` / `理解` / `应用` / `分析` |
| sectionUri | String | 所属小节 URI |
| sectionLabel | String | 所属小节名称 |
| chapterUri | String | 所属章节 URI |
| chapterLabel | String | 所属章节名称 |


### 常见错误
| code | message | 说明 |
| --- | --- | --- |
| 70004 | 小节不存在 | 请求的小节不存在 |


---

## 7. 获取知识点详情
### 基本信息
| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/knowledge-points/{uri}` |
| 需要登录 | 否 |


> 注：`{uri}` 需要 URL 编码。
>

### 响应参数 (`KgKnowledgePointDetailDTO`)
```json
{
  "uri": "http://edukg.org/knowledge/3.1/kp/加法",
  "label": "加法",
  "difficulty": "easy",
  "importance": "high",
  "cognitiveLevel": "理解",
  "sectionUri": "http://edukg.org/knowledge/3.1/section/10以内数的认识",
  "sectionLabel": "10以内数的认识",
  "chapterUri": "http://edukg.org/knowledge/3.1/chapter/准备课",
  "chapterLabel": "准备课"
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| uri | String | 知识点 URI |
| label | String | 知识点名称 |
| difficulty | String | 难度 |
| importance | String | 重要程度 |
| cognitiveLevel | String | 认知层级 |
| sectionUri | String | 所属小节 URI |
| sectionLabel | String | 所属小节名称 |
| chapterUri | String | 所属章节 URI |
| chapterLabel | String | 所属章节名称 |


> 注：知识点详情返回 2 层父级（section + chapter），不返回教材/年级等更高层级。
>

### 常见错误
| code | message | 说明 |
| --- | --- | --- |
| 70003 | 知识点不存在 | 请求的知识点不存在（含已软删除/已合并） |


---

## 8. 获取年级知识体系
### 基本信息
| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/system/grade/{grade}` |
| 需要登录 | 否 |


### 请求参数
**Path 参数**

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| grade | String | 是 | 年级：`一年级` ~ `高三` |


**Query 参数**

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| groupBy | String | 否 | `subject` | 分组方式：`subject`（按学科） / `topic`（按专题） |


### 响应参数 (`KgGradeSystemDTO`)
```json
{
  "grade": "一年级",
  "groupBy": "subject",
  "groups": [
    {
      "key": "math",
      "label": "数学",
      "chapters": [
        {
          "uri": "http://edukg.org/knowledge/3.1/chapter/准备课",
          "label": "准备课",
          "topic": "数与代数",
          "orderIndex": 1,
          "sections": [
            {
              "uri": "http://edukg.org/knowledge/3.1/section/10以内数的认识",
              "label": "10以内数的认识",
              "knowledgePoints": [
                {
                  "uri": "http://edukg.org/knowledge/3.1/kp/10以内数的认识",
                  "label": "10以内数的认识",
                  "difficulty": "easy",
                  "importance": "high",
                  "cognitiveLevel": "记忆",
                  "status": "active"
                }
              ]
            }
          ]
        }
      ],
      "knowledgePointCount": 45
    }
  ],
  "totalKnowledgePoints": 45
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| grade | String | 年级名称 |
| groupBy | String | 实际使用的分组方式 |
| groups | List<GroupDTO> | 分组列表 |
| totalKnowledgePoints | int | 知识点总数 |


**GroupDTO 结构：**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| key | String | 分组键（学科值如 "math" 或专题值） |
| label | String | 分组展示名称（如 "数学"） |
| chapters | List<ChapterNode> | 章节列表 |
| knowledgePointCount | int | 该分组下知识点总数 |


**ChapterNode 结构：**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| uri | String | 章节 URI |
| label | String | 章节名称 |
| topic | String | 专题名称 |
| orderIndex | Integer | 排序序号 |
| sections | List<SectionNode> | 小节列表 |


**SectionNode 结构（知识体系上下文）：**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| uri | String | 小节 URI |
| label | String | 小节名称 |
| knowledgePoints | List<KgKnowledgePointDTO> | 知识点列表 |


### 常见错误
| code | message | 说明 |
| --- | --- | --- |
| 10000 | 年级不存在 | 请求的年级不存在，返回空结构 |


---

## 9. 获取年级统计
### 基本信息
| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/system/stats/{grade}` |
| 需要登录 | 否 |


### 响应参数 (`StatsDTO`)
```json
{
  "grade": "一年级",
  "totalKnowledgePoints": 150,
  "totalTextbooks": 2,
  "totalChapters": 12,
  "totalSections": 45,
  "difficultyDistribution": {
    "easy": 60,
    "medium": 70,
    "hard": 20
  }
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| grade | String | 年级名称 |
| totalKnowledgePoints | int | 知识点总数 |
| totalTextbooks | int | 教材总数 |
| totalChapters | int | 章节总数 |
| totalSections | int | 小节总数 |
| difficultyDistribution | Map<String, Integer> | 难度分布（key: `easy`/`medium`/`hard`） |


---

## 10. Neo4j 健康检查
### 基本信息
| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `GET` |
| 接口路径 | `/api/kg/neo4j/health` |
| 需要登录 | 否 |


### 响应参数 (`HealthDTO`)
Neo4j 可用：

```json
{
  "available": true,
  "responseTimeMs": 50,
  "message": "Neo4j connection OK"
}
```

Neo4j 不可用：

```json
{
  "available": false,
  "responseTimeMs": 0,
  "message": "connection timeout"
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| available | boolean | Neo4j 是否可用 |
| responseTimeMs | long | 响应时间（毫秒） |
| message | String | 状态描述或错误信息 |


---

## 11. 批量获取概念关联
### 基本信息
| 项目 | 值 |
| --- | --- |
| HTTP 方法 | `POST` |
| 接口路径 | `/api/kg/concepts/batch-relations` |
| 需要登录 | 否 |
| Content-Type | `application/json` |


### 请求参数
```json
{
  "uris": [
    "http://edukg.org/knowledge/0.1/instance/math#加法",
    "http://edukg.org/knowledge/0.1/instance/math#减法"
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| uris | List<String> | 是 | 概念 URI 列表 |


### 响应参数 (`BatchRelationsDTO`)
```json
{
  "relations": [
    {
      "uri": "http://edukg.org/knowledge/0.1/instance/math#加法",
      "relatedUris": [
        "http://edukg.org/knowledge/0.1/instance/math#加法定义",
        "http://edukg.org/knowledge/0.1/instance/math#加法性质"
      ]
    },
    {
      "uri": "http://edukg.org/knowledge/0.1/instance/math#减法",
      "relatedUris": [
        "http://edukg.org/knowledge/0.1/instance/math#减法定义"
      ]
    }
  ]
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| relations | List<RelationEntry> | 关联结果列表 |


**RelationEntry 结构：**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| uri | String | 概念 URI |
| relatedUris | List<String> | 关联的 URI 列表 |


> **缓存策略**: 查询结果存入 Redis，TTL = 300s。Neo4j 不可用时返回空 relations 列表。
>

---

## 错误码说明
### 通用错误码
| code | message | 说明 |
| --- | --- | --- |
| 00000 | success | 成功 |
| 10000 | 系统错误 | 服务器内部错误 |
| 10001 | 参数错误 | 请求参数格式不正确 |


### 知识图谱错误码 (7xxxx)
| code | message | 说明 |
| --- | --- | --- |
| 70001 | 教材不存在 | 请求的教材不存在 |
| 70002 | 章节不存在 | 请求的章节不存在 |
| 70003 | 知识点不存在 | 请求的知识点不存在（含已软删除/已合并） |
| 70004 | 小节不存在 | 请求的小节不存在 |
| 70005 | Neo4j 查询失败 | 图数据库查询异常 |
| 70006 | 同步正在进行 | 已有同步任务在执行 |
| 70007 | 同步参数错误 | 同步请求参数格式不正确 |


---

## 前端调用注意事项
### 1. CORS 配置
前端独立部署，后端已配置 CORS 允许跨域。

### 2. URI 编码
所有路径参数中的 `uri` 需要 URL 编码。例如：

```javascript
const uri = encodeURIComponent('http://edukg.org/knowledge/3.1/textbook/一年级上册');
fetch(`/api/kg/textbooks/${uri}/chapters`);
```

### 3. 权限说明
同步接口（`POST /api/kg/sync/full`）需要 ADMIN 或 TEACHER 角色，其他查询接口无需登录。

### 4. 响应结构
所有接口返回 `ApiResponse<T>` 包装格式，前端需先解包 `data` 字段获取业务数据：

```javascript
const response = await fetch('/api/kg/textbooks');
const result = await response.json();
if (result.code === '00000') {
  const textbooks = result.data; // List<KgTextbookDTO>
}
```

---

_文档生成时间: 2026-04-17_