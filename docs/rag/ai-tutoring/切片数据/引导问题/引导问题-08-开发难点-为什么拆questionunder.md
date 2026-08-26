# 为什么拆 question_understand / decide / generate？

> summary: 为什么拆 question_understand / decide / generate？
> 权威度: 1.0 ｜ 来源: 引导问题 ｜ 锚点: 为什么拆 question_understand / decide / generate？
> 模块: ai-tutoring ｜ 节: 开发难点
> COS路径: rag-slices/ai-tutoring/引导问题/引导问题-08-开发难点-为什么拆questionunder.md
> 类别：开发难点

## 回答

**核心结论**：三个子任务职责不同，拆开才能独立可控、可单测、可换模型，也让护栏有地方插入。

**分层展开**：
- **question_understand**：独立 stateless 视觉端点，看图识别题型名（1~5 个），只服务题型分析页，不参与答疑匹配——答疑的题型识别由 decide 读题顺带产出 question_kps。
- **decide**：只判动作，输出 ActionMeta（type 闭集/eval/mastery_signals）。判断密集 → 关思考、低温度、意图秒出；配结构化输出四段降级，绝不吐畸形。
- **generate**：只按 Java 已放行的 action_type 流式生成正文。长输出段 → 开思考（思考 = AI 版进度条），让等待可见。
- **为什么拆**：① Java 护栏能插在 decide 与 generate 之间（审批 type 才放行正文），"类型先行流式"安全成立；② 每段独立测试（tests 覆盖）、独立换模型（decide 低温度判动作、generate 负责长文）；③ 故障边界清晰——decide 挂了不影响 generate 已有能力。
