# 掌握度信号题型化 API 契约变更

> 基础路径: `/api/tutoring`
> 变更日期: 2026-08-17
> 主契约文档: `openspec/changes/ai-tutoring/api.md`

## 变更点

`POST /api/tutoring/decide` 响应的 `mastery_signals` 字段改名 + 语义翻转。

### 字段改名

| 项 | 旧 | 新 |
|----|----|----|
| 字段名 | `kp_label` | `topic_label` |
| 语义 | 知识点 label | 题型 label |

### 响应示例（变更后）

```json
{
  "type": "hint",
  "reason": "学生已设未知数，给一条引导性反问",
  "eval": {"correct": true, "error_type": null, "emotion": "NEUTRAL", "exercise_complete": false},
  "mastery_signals": [{"topic_label": "鸡兔同笼", "signal": "practicing"}],
  "question_kps": ["二元一次方程组"],
  "new_question": null,
  "end_reason": null,
  "summary": null,
  "safety_flag": false,
  "degraded": false
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| mastery_signals[].topic_label | String | **题型** label（如「鸡兔同笼」「相遇问题」），**不是知识点** |
| mastery_signals[].signal | String | 不变：mastered/practicing/struggling（Java 映射 75/50/25） |
| question_kps | Array[String] | 不变：题目涉及**知识点**（如「二元一次方程组」） |

## 兼容性

- **Java 侧**：`@JsonAlias("topic_label")` 兼容旧字段名 `kp_label`，Python 改名不阻塞 Java 上线。
- **前端侧**：读 Java 透传的 `kpLabel`（camelCase），与 Python 字段名无关，不受影响。
- **mastery_snapshot 入参**：保留不动（Java 契约不变），但不再作为 mastery_signals 的接地源。

## 不改的

- `question_kps` 继续输出知识点。
- `signal` 枚举不变。
- 请求体（history / round_count / answer_request_count / mastery_snapshot / subject_hint / is_new_question）不变。
