# 分析-03-subject-classify学科门

> summary: (无 summary)
> 权威度: 0.8 ｜ 来源: 代码 ｜ 锚点: 对账要点
> 模块: question-analysis ｜ 节: 分析-03-subject-classify学科门

---

## 对账要点

| 对账分类 | 项 | 语雀/design 口径 | 代码现状 | 结论 |
|---|---|---|---|---|
| 方案vs实现 | 学科闭集 | 早期闭集 5 值 | 完整 K12 十值 | ⚠️翻转（扩集） |
| 接口契约 | subject 返回 | `None`=失败放行 | `None`=闭集外/失败；other=明确非学科 | ✅落地 |
| 注释vs运行行为 | 失败语义 | 吞异常降级空 | try/except 全包裹返回空 subject | ✅落地 |
