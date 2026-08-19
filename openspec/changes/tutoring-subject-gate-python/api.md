# tutoring-subject-gate-python API 接口文档

> 基础路径: `/api/tutoring`
>
> 更新日期: 2026-08-19
>
> ⚠️ **对外前端接口契约不变**（仍是 `meta / token / done` 三段 SSE 事件流）。`subject-classify` 为 **Java↔Python 内部端点**，不对前端开放。

---

## 1. subject-classify（Java↔Python 内部，学科前置判定）

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `POST` |
| 接口路径 | `/api/tutoring/subject-classify` |
| 认证 | `x-internal-token`（与 decide/generate/understand 同源） |
| Content-Type | `application/json` |
| 开放对象 | **仅 Java 网关**，不对前端开放 |

**用途**：判定题目学科（decide 之前）。学科无关小分类器，只判学科不解题，支持文本和图片。Java 据此分流：`math` → 走数学 decide；非 `math` → 跳过（不建/不续会话）。

### 请求参数

```json
{
  "content": "自由落体运动的问题…",
  "image_url": null
}
```

| 字段 | 类型 | 必填 | 校验 |
|------|------|------|------|
| content | String | 否 | 与 image_url 至少一个非空 |
| image_url | String | 否 | 题目图片 URL（COS）；与 content 至少一个非空 |

### 响应参数

```json
{
  "subject": "physics"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| subject | String | 闭集（K12 九门 + other）：`math` / `physics` / `chemistry` / `biology` / `chinese` / `english` / `politics` / `geography` / `history` / `other`；失败/异常/闭集外 → `null`（Java 按 math 放行） |

### 请求示例

**cURL：**

```bash
# 文本数学题
curl -X POST http://localhost:9527/api/tutoring/subject-classify \
  -H "Content-Type: application/json" \
  -H "x-internal-token: <internal-token>" \
  -d '{"content": "鸡兔同笼，共35头94脚，各几只？", "image_url": null}'
# → {"subject":"math"}

# 文本物理题
curl -X POST http://localhost:9527/api/tutoring/subject-classify \
  -H "Content-Type: application/json" \
  -H "x-internal-token: <internal-token>" \
  -d '{"content": "物体做自由落体运动，求落地速度", "image_url": null}'
# → {"subject":"physics"}

# 图片题目
curl -X POST http://localhost:9527/api/tutoring/subject-classify \
  -H "Content-Type: application/json" \
  -H "x-internal-token: <internal-token>" \
  -d '{"content": null, "image_url": "https://cos.xxx/1.jpg"}'
# → {"subject":"physics"}（示例；按图内容定学科）
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 403 | Missing/Invalid internal token | `x-internal-token` 缺失或不匹配 |
| 422 | 参数校验错误 | content 与 image_url 均为空 |
| - | - | 分类失败不报 5xx：返回 `{"subject": null}`，Java 按 math 放行 |

---

## 2. 前端调用注意事项

1. **学科判定对前端透明**：前端照常发题（文字/图片），Java 内部先判学科，再决定走答疑还是返回「仅支持数学」提示流。前端契约（meta/token/done SSE）不变。
2. **非数学题不报错**：是正常 SSE 提示流（`meta(sessionId=null,type=hint) → token(提示语) → done`），前端直接展示即可（提示语「目前仅支持数学答疑，换一道数学题试试吧。」由 Java 组装）。
3. **不消耗轮次 / 无落库**：非数学题不扣 20 轮上限、不产生题目记录/掌握度/错误事件。

---

*契约对齐：后端 `openspec/changes/tutoring-subject-gate/api.md` 第 2 节（subject-classify Java↔Python 内部）。*
