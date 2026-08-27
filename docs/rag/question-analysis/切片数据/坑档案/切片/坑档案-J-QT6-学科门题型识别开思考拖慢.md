# 坑档案 J-QT6 学科门/题型识别开思考拖慢 50~145s

> summary: 学科门/题型识别开思考拖慢 50~145s
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J-QT6. 学科门/题型识别开思考拖慢
> 模块: question-analysis ｜ 节: 坑档案
> COS路径: rag-slices/question-analysis/坑档案/坑档案-J-QT6-学科门题型识别开思考拖慢.md
> 类别：开发难点

---

**1. 问题现象**：学科门判定一次要 50~145 秒，答疑链路等死。

**2. 触发流程**：subject-classify / question-understand 用默认参数调 LLM（开思考）。

**3. 根因分析**：开思考（thinking）模式下模型长思考，学科门这种简单判定也拖到分钟级。

**4. 排查过程**：实测开思考 50~145s、关思考秒出。

**5. 解决方案 & 改动点**：**统一"慢修复"**——关思考（thinking disabled）+ 20s 超时 + 关 SDK 重试；慢/失败快速返回空结果，Java 走降级（闭集外放行 math / 空 topic_labels 降级 PENDING）。（`subject_classify.py:66-73`、`question_understand.py:82-91`）

**6. 面试口述要点**：前置判定环节最怕变卡点。我们实测开思考模式下学科门要 50~145 秒，这不可接受。所以专门做了慢修复：关思考 + 20 秒超时 + 关重试，宁可快速失败让 Java 走降级，也不让主链路等。
