# 分析-03-subject-classify学科门-落地问题与复盘

> summary: subject-classify学科门落地问题与复盘
> 权威度: 0.8 ｜ 来源: 面试切片 ｜ 锚点: 落地问题与复盘
> 模块: question-analysis ｜ 节: 分析-03-subject-classify学科门
> COS路径: rag-slices/interview/question-analysis/分析-03-subject-classify学科门-落地问题与复盘.md
> 类别：项目难点复盘
> target: 面试项目问答

---

## 隐性坑与注意事项

1. **闭集外 → 空不是 other**：other = "明确非学科内容"，空 = "不知道"，语义分开——把地质/天文硬归 other 是污染。
2. **图片路径**：有图发多模态消息，纯文本走 text——同端点两种输入形态。
3. **慢修复是红线**：开思考 50~145s、关思考秒出——学科门不能成为新卡点，别调高超时。
4. **Java 两个触发点**：发起/换题各判一次，别漏判换题场景。

## 方案 vs 落地的复盘（原始设计 → 实际实现 → 影响）

**学科闭集翻转：早期 5 值 → K12 十值（扩集）**
原始方案学科闭集是 5 值（math 相关）；落地扩为完整 K12 十值（math/physics/chemistry/biology/chinese/english/politics/geography/history/other）。影响：能识别所有 K12 学科，非数学直接拒，数学专注答疑。

**subject 返回语义确认（✅落地）**
原始方案空值=失败放行；落地明确：空=闭集外/失败，other=明确非学科——Java 端据此分流，语义清晰。

**失败语义确认（✅落地）**
原始方案吞异常降级空；落地 try/except 全包裹返回空 subject——业务判定失败 ≠ 错误，不阻塞主链路。

> 证据：详见 `3.代码/分析-03-subject-classify学科门.md`（§隐性坑与注意事项 / §对账要点）｜ `4.完善文档/04-防作弊与异常防护.md`