# 知识图谱 API 接口文档

> 本文档供 Java 后端参考，用于前端知识图谱渲染和查询。

---

## 1. 概述

### 1.1 服务地址

```
Python AI 服务: http://localhost:9527
知识图谱 API 前缀: /api/kg
```

### 1.2 认证方式

所有接口需要在 Header 中携带内部 Token：

```
x-internal-token: <your-internal-token>
```

### 1.3 支持的学科

| 学科 | 代码 | 中文名 |
|------|------|--------|
| 数学 | `math` | 数学 |
| 物理 | `physics` | 物理 |
| 化学 | `chemistry` | 化学 |
| 生物 | `biology` | 生物 |
| 语文 | `chinese` | 语文 |
| 历史 | `history` | 历史 |
| 地理 | `geo` | 地理 |
| 政治 | `politics` | 政治 |
| 英语 | `english` | 英语 |

---

## 2. API 端点列表

| 端点 | 方法 | 功能 | 前端渲染用途 |
|------|------|------|--------------|
| `/api/kg/entities` | GET | 搜索知识点 | 搜索框联想 |
| `/api/kg/entity/{uri}` | GET | 获取知识点详情 | 知识点详情页 |
| `/api/kg/link` | POST | 文本实体识别 | 文本高亮、标签提取 |
| `/api/kg/subject/{subject}/tree` | GET | 获取知识树 | 知识图谱树形展示 |
| `/api/kg/subject/{subject}/classes` | GET | 获取学科分类 | 学科分类展示 |
| `/api/kg/student/{id}/progress` | GET | 获取学习进度 | 学习进度展示 |
| `/api/kg/student/{id}/progress` | POST | 更新学习进度 | 记录学习状态 |
| `/api/kg/student/{id}/statistics` | GET | 获取学习统计 | 学习统计图表 |
| `/api/kg/recommend` | GET | 获取推荐知识点 | 智能推荐 |
| `/api/kg/learning-path` | GET | 获取学习路径 | 学习路径规划 |

---

## 3. API 详细说明

### 3.1 搜索知识点

**请求**

```
GET /api/kg/entities?label={keyword}&subject={subject}&limit={limit}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| label | string | 是 | 搜索关键词 (1-100字符) |
| subject | string | 否 | 学科过滤 (见学科代码) |
| limit | int | 否 | 返回数量 (默认20, 最大100) |

**响应**

```json
{
  "total": 5,
  "entities": [
    {
      "label": "一元二次方程",
      "uri": "http://edukg.org/knowledge/3.0/instance/math#xxx",
      "subject": "math"
    }
  ]
}
```

**前端用途**: 搜索框下拉联想、知识点快速选择

---

### 3.2 获取知识点详情

**请求**

```
GET /api/kg/entity/{uri}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uri | string | 是 | 知识点 URI (URL编码) |

**响应**

```json
{
  "uri": "http://edukg.org/knowledge/3.0/instance/math#xxx",
  "label": "一元二次方程",
  "subject": "math",
  "description": "含有一个未知数，且未知数的最高次数为2的整式方程",
  "properties": [],
  "relationships": {
    "prerequisite": [
      {"label": "一元一次方程", "uri": "..."}
    ],
    "relatedTo": [
      {"label": "二次函数", "uri": "..."}
    ]
  }
}
```

**前端用途**: 知识点详情页、知识点卡片

---

### 3.3 文本实体识别

**请求**

```
POST /api/kg/link
Content-Type: application/json

{
  "text": "一元二次方程是初中数学的重要内容",
  "subject": "math",
  "enrich_context": false
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 待分析文本 (1-10000字符) |
| subject | string | 否 | 学科上下文 |
| enrich_context | bool | 否 | 是否返回上下文信息 |

**响应**

```json
{
  "entities": [
    {
      "label": "一元二次方程",
      "uri": "http://edukg.org/knowledge/3.0/instance/math#xxx",
      "subject": "math",
      "positions": [
        {"start": 0, "end": 6}
      ],
      "context": null
    }
  ]
}
```

**前端用途**:
- 文本中知识点高亮
- 自动标签提取
- 题目知识点标注

---

### 3.4 获取知识树

**请求**

```
GET /api/kg/subject/{subject}/tree?depth={depth}&student_id={studentId}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| subject | string | 是 | 学科代码 |
| depth | int | 否 | 树深度 (默认3, 最大5) |
| student_id | string | 否 | 学生ID (返回学习进度) |

**响应**

```json
{
  "subject": "math",
  "tree": {
    "id": "root",
    "label": "数学",
    "type": "class",
    "subject": "math",
    "progress": null,
    "children": [
      {
        "id": "http://edukg.org/knowledge/xxx",
        "label": "一元二次方程",
        "type": "entity",
        "subject": "math",
        "progress": "mastered",
        "children": []
      }
    ]
  }
}
```

**前端用途**: 知识图谱树形展示、思维导图渲染

**进度状态**:
- `not_started` - 未开始
- `in_progress` - 学习中
- `mastered` - 已掌握

---

### 3.5 获取学科分类

**请求**

```
GET /api/kg/subject/{subject}/classes
```

**响应**

```json
{
  "classes": [
    {
      "uri": "http://edukg.org/class/math",
      "label": "数学",
      "entity_count": 5280
    }
  ]
}
```

**前端用途**: 学科分类标签页、知识点分类导航

---

### 3.6 获取学习进度

**请求**

```
GET /api/kg/student/{student_id}/progress?subject={subject}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| student_id | string | 是 | 学生ID |
| subject | string | 否 | 学科过滤 |

**响应**

```json
{
  "student_id": "student_001",
  "progress": [
    {
      "entity_uri": "http://edukg.org/knowledge/xxx",
      "entity_label": "一元二次方程",
      "subject": "math",
      "status": "mastered",
      "score": 90,
      "updated_at": "2026-03-27T10:00:00"
    }
  ]
}
```

**前端用途**: 学习进度列表、知识点掌握情况

---

### 3.7 更新学习进度

**请求**

```
POST /api/kg/student/{student_id}/progress
Content-Type: application/json

{
  "entity_uri": "http://edukg.org/knowledge/xxx",
  "status": "mastered",
  "score": 90
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| entity_uri | string | 是 | 知识点 URI |
| status | string | 是 | 状态: not_started/in_progress/mastered |
| score | int | 否 | 分数 (0-100) |

**响应**

```json
{
  "success": true,
  "progress": {
    "entity_uri": "http://edukg.org/knowledge/xxx",
    "entity_label": "一元二次方程",
    "subject": "math",
    "status": "mastered",
    "score": 90
  }
}
```

**前端用途**: 记录学习状态、更新进度条

---

### 3.8 获取学习统计

**请求**

```
GET /api/kg/student/{student_id}/statistics
```

**响应**

```json
{
  "student_id": "student_001",
  "overall": {
    "total": 100,
    "mastered": 30,
    "in_progress": 20,
    "not_started": 50
  },
  "by_subject": []
}
```

**前端用途**: 学习统计图表、进度仪表盘

---

### 3.9 获取推荐知识点

**请求**

```
GET /api/kg/recommend?entity_uri={uri}&subject={subject}&student_id={studentId}&limit={limit}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| entity_uri | string | 否 | 基于该知识点推荐 |
| subject | string | 否 | 学科过滤 |
| student_id | string | 否 | 学生ID (个性化推荐) |
| limit | int | 否 | 返回数量 (默认10, 最大50) |

**响应**

```json
{
  "recommendations": [
    {
      "entity_uri": "http://edukg.org/knowledge/xxx",
      "label": "二次函数",
      "reason": "Related to current knowledge point",
      "difficulty": null,
      "mastered": false
    }
  ]
}
```

**前端用途**: 相关知识点推荐、智能学习建议

---

### 3.10 获取学习路径

**请求**

```
GET /api/kg/learning-path?target_entity_uri={uri}&student_id={studentId}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| target_entity_uri | string | 是 | 目标知识点 URI |
| student_id | string | 是 | 学生ID |

**响应**

```json
{
  "path": [
    {
      "order": 1,
      "entity_uri": "http://edukg.org/knowledge/xxx",
      "label": "一元一次方程",
      "status": "mastered"
    },
    {
      "order": 2,
      "entity_uri": "http://edukg.org/knowledge/yyy",
      "label": "一元二次方程",
      "status": "not_started"
    }
  ]
}
```

**前端用途**: 学习路径规划、前置知识展示

---

## 4. 前端渲染建议

### 4.1 知识图谱树形展示

```
推荐使用组件:
- D3.js (树形图)
- ECharts (树图/关系图)
- AntV G6 (关系图)

数据结构 (KnowledgeTreeNode):
{
  id: string,          // 唯一标识
  label: string,       // 显示名称
  type: "class" | "entity",
  subject: string,     // 学科
  progress: string,    // 学习进度
  children: []         // 子节点
}

颜色建议:
- mastered: 绿色
- in_progress: 蓝色
- not_started: 灰色
```

### 4.2 知识点搜索联想

```
调用: GET /api/kg/entities?label={keyword}
展示: 下拉列表 + 学科标签
点击: 跳转到知识点详情页
```

### 4.3 文本知识点高亮

```
调用: POST /api/kg/link
处理:
1. 获取 entities 数组
2. 根据 positions 中的 start/end 定位文本
3. 添加高亮样式和点击事件
```

---

## 5. 错误码

| HTTP状态码 | 错误码 | 说明 |
|------------|--------|------|
| 400 | 10001 | 参数无效 |
| 404 | 10002 | 资源不存在 |
| 403 | 10004 | 未授权 (缺少 token) |
| 400 | 20001 | 学科不存在 |
| 404 | 20002 | 知识点不存在 |
| 503 | 20003 | 图谱服务不可用 |
| 404 | 20004 | 学生不存在 |

---

## 6. Java 调用示例

```java
// 使用 RestTemplate 调用
RestTemplate restTemplate = new RestTemplate();

// 设置请求头
HttpHeaders headers = new HttpHeaders();
headers.set("x-internal-token", "your-internal-token");

// 搜索知识点
String url = "http://localhost:9527/api/kg/entities?label=方程&subject=math";
HttpEntity<String> entity = new HttpEntity<>(headers);
ResponseEntity<EntitySearchResponse> response = restTemplate.exchange(
    url, HttpMethod.GET, entity, EntitySearchResponse.class
);

// 响应对象
@Data
public class EntitySearchResponse {
    private Integer total;
    private List<EntityItem> entities;
}

@Data
public class EntityItem {
    private String label;
    private String uri;
    private String subject;
}
```

---

## 7. 数据规模

| 数据 | 数量 |
|------|------|
| 知识点实体 | ~51,760 |
| 学科数量 | 9 |
| 关系数量 | ~2,396 |

---

*文档更新时间: 2026-03-27*
*Python AI 服务版本: 1.0.0*