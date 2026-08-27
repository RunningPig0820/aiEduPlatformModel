# 分析-03-subject-classify学科门-坑与对账

> summary: subject-classify学科门坑与对账
> 来源: 切片 ｜ 锚点: 坑与对账
> 节: 分析-03-subject-classify学科门
> COS路径: rag-slices/question-analysis/代码/分析-03-subject-classify学科门-坑与对账.md
> 类别：开发难点
> target: 开发对账

---

## 隐性坑与注意事项

- **闭集外 → None 不是 other**：other = "明确非学科内容"，None = "不知道"，语义分开（`subject_classify.py:48-55`）。
- **图片路径**：image_url 存在时发多模态消息，纯文本走 text。（`subject_classify.py:75-81`）
- **慢修复**：开思考实测 50~145s、关思考秒出——学科门不能成为新卡点，别调高超时。（`subject_classify.py:68-69` 注释）
- **Java 触发点**：发起/换题两个点各判一次（`api/tutoring.py:136-149` 注释）。

## 对账要点（方案 vs 代码复盘）

**学科闭集 —— ⚠️翻转（扩集）**
原始方案学科闭集仅 5 值；落地为完整 K12 十值（`SubjectType`：math/physics/chemistry/biology/chinese/english/politics/geography/history/other）。业务影响：覆盖全 K12 学科门，非数学直接拒、数学专注答疑，消除 5 值时代的学科漏判。

**subject 返回语义 —— ✅落地**
原始方案 `None` = 失败放行；落地明确语义分离：`None` = 闭集外/失败，`other` = 明确非学科。Java 端据此分流（other 跳过、None 按 math 放行），与 design 口径一致。

**失败语义（吞异常降级空） —— ✅落地**
原始方案失败时吞异常降级为空；落地 `try/except` 全包裹返回空 subject——业务判定失败 ≠ 错误，不阻塞主链路，注释与运行行为一致。

> 证据：详见 `3.代码/分析-03-subject-classify学科门.md`（§隐性坑与注意事项 / §对账要点）
