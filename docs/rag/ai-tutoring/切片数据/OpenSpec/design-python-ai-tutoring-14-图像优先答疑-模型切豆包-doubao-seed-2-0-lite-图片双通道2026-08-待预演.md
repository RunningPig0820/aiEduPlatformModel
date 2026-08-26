# design-python-ai-tutoring

> summary: 解决图像优先答疑的模型切换与双通道适配问题
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 14. 图像优先答疑:模型切豆包 doubao-seed-2-0-lite + 图片双通道(2026-08 待预演)
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-python-ai-tutoring-14-图像优先答疑-模型切豆包-doubao-seed-2-0-lite-图片双通道2026-08-待预演.md
> 类别：架构设计

---

### 14. 图像优先答疑:模型切豆包 doubao-seed-2-0-lite + 图片双通道(2026-08 待预演)

**背景**: 数学/化学题目大量含**公式 + 图形**(受力分析图/实例图),OCR 拆解必然丢信息 → 题目作为**图片整体**进多模态模型。答疑引擎从 deepseek-v4-flash(纯文本)切到 **doubao-seed-2-0-lite**(火山方舟,图+文全模态,OpenAI 兼容)。

**关键约束: 文本与图片双通道共存(并不一定都有图片)**。纯文本题目(手打/粘贴)继续走文本,行为与现状完全一致;图片题目走 `image_url`。`ChatTurn.image_url` 可选字段,无图时向后兼容。

**契约**: `ChatTurn` 加 `image_url: Optional[str]`(COS 签名 URL,content 可为空)。Java 发来的 history 首条 user 消息即题目图片。换题判定扩展:新图片消息 = 新题 → switch(文本逻辑不变)。

**实现要点**:
- Factory 加 `doubao` provider(OpenAI 兼容,base_url=方舟 ark.cn-beijing.volces.com/api/v3)
- `structured.py` 从"字符串 prompt"改为"消息列表": ② JSON hint 拼接要改 `messages + [SystemMessage(_JSON_HINT)]`;纠错重试重设计
- `prompts.py`: 看图决策指令 + 带图消息渲染成 `[图片题目]` 占位(真实图走多模态通道)
- **换题信号(确定性,2026-08 后端联调定稿)**: 换题检测由 **Java 做**(它知道何时收到新图/新题),decide 请求带 `is_new_question=true` → Python **短路直接返回 `type=switch`,不调 LLM**。原因: Python 无状态,无法从累积 history 区分"这轮刚换题" vs "早几轮已换、这轮在答题"(两种情况下图片结构一样);由 Java 在"新图出现的这一轮"置信号最可靠。废弃早期"历史 2+ 张图=换题"的推断(会每轮误触发)。Java 收到 switch 重置轮次计数。

**风险(未实测,必须先技术预演)**:
- [R10] **图片 + function calling 同时用是否支持**(①段 `bind_tools` 在 lite+图片下可用性)——不通则全程走 JSON mode
- [R11] **方舟是否可直接访问 COS 签名 URL**——不可则改 base64(图片进请求体)
- [R12] **structured 消息化后四段降级回归**(②的 hint 拼接、纠错重试都要改)

**落地顺序**: 先 spike(配置+Factory+真实题图,实测 R10/R11 + 看图读题)→ 通过再全量改(契约/structured/prompts/decider/generator/测试)。

**spike 进展(2026-08, task 10.1 完成)**:
- ✅ 配置/Factory/doubao provider 已就绪(settings + .env + model_config),连接与模型列表正常
- ✅ **正确模型 ID**:`doubao-seed-2-0-lite-260428`(控制台显示名 `Doubao-Seed-2.0-lite` 不可直接调用;同族还有 -260215)
- ✅ **R10 排除**:图片消息 + `bind_tools` function calling 实测**可用**(带图正常返回 tool_call)→ ①段走 function calling 不降级
- ✅ **R11 排除**:方舟**可直接访问 COS 签名 URL**(base64 不需要)
- ✅ **看图读题**:实测完整读出含 LaTeX 公式的数学题(公式/选项全对)——doubao-seed-2-0-lite 视觉能力达标
- 结论: 豆包全模态模型适合答疑,可进入 10.2-10.6 实现
