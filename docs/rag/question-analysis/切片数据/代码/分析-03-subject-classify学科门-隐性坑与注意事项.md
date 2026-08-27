# 分析-03-subject-classify学科门

> summary: (无 summary)
> 权威度: 0.8 ｜ 来源: 代码 ｜ 锚点: 隐性坑与注意事项
> 模块: question-analysis ｜ 节: 分析-03-subject-classify学科门

---

## 隐性坑与注意事项

- **闭集外 → None 不是 other**：other = "明确非学科内容"，None = "不知道"，语义分开（`subject_classify.py:48-55`）。
- **图片路径**：image_url 存在时发多模态消息，纯文本走 text。（`subject_classify.py:75-81`）
- **慢修复**：开思考实测 50~145s、关思考秒出——学科门不能成为新卡点，别调高超时。（`subject_classify.py:68-69` 注释）
- **Java 触发点**：发起/换题两个点各判一次（`api/tutoring.py:136-149` 注释）。
