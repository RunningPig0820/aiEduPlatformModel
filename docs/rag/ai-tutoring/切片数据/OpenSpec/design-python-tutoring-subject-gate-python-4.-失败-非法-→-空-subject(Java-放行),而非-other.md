# design-python-tutoring-subject-gate-python

> summary: 明确学科判定异常情况的输出规则，保障Java侧安全放行
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 4. 失败/非法 → 空 subject(Java 放行),而非 other
> 模块: ai-tutoring ｜ 节: design-python-tutoring-subject-gate-python

---

### 4. 失败/非法 → 空 subject(Java 放行),而非 other

| 情况 | 输出 | Java 行为 | 方向 |
|------|------|-----------|------|
| 明确任一非 math 学科(物理/化学/生物/语文/英语/政治/地理/历史) | 对应学科 | 跳过「仅支持数学」 | 正确 |
| 明确数学 | math | 放行走 decide | 正确 |
| 图片无法辨认/非学科 | other | 跳过 | 正确 |
| 拿不准 math vs 其他 | math | 放行 | 漏拦(安全) |
| LLM 异常/超时 | None | 按 math 放行 | 漏拦(安全) |
| 输出闭集外学科 | None | 按 math 放行 | 漏拦(安全) |
