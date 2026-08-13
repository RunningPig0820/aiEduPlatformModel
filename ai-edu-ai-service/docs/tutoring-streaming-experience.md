# 答疑流式体验问题 — 请模型端评估能否优化

> 提出方:前端/Java 网关
> 日期:2026-08-13
> 目的:请教模型端(方舟 Doubao seed 2.0 调用侧)是否有能力改善"流式体验卡顿"。

---

## ✅ 最终结论(2026-08-13 更新:分层思考开关)

**决策: 分阶段思考开关 —— decide 关思考(意图秒出)、generate 开思考(思考 = AI 版进度条)。**

- 2026-08-12 曾拍板"全关思考":思考模式 = 模型"写草稿",是卡顿根源;关思考后切
  `doubao-seed-2-0-mini`(四模态、便宜),decide ~1.5s / generate ~1.2s / 看图全流程 ~3.4s。
- 2026-08-13 前端需求:等待期要有过程输出("思考过程 = AI 版的进度条")。权衡后仅对
  **generate** 重开思考——引导解答段(最长等待)流式吐 `reasoning_content` → `thinking` 事件,
  前端思考条实时流入;decide 保持关思考,意图分类秒出(~1.5s,无思考文本)。
- 落地:`core/tutoring/ark_stream.py` 的 `stream_chat(enable_thinking=...)` 参数化开关,
  `generator.py` 传 `enable_thinking=True`,`decider.py` 保持默认(False)。
- 遗留风险:开思考的 generate 可能有首发静默(~数秒)+ 内容短时涌出(见 §2.2 实测),
  由前端打字机 reveal + "思考中…"脉动提示兜底。

---

## 一、现象(用户可感知)

学生端 AI 答疑页面,用户反馈:

1. **思考过程不是逐字蹦,是一句一句蹦出来**,观感不流畅
2. **答案感觉像"攒完所有内容一次性输出"**,不是持续流动
3. **整体"很卡",明显不如 ChatGPT / Claude 网页版流畅**

## 二、已确认的事实(实测数据)

### 2.1 全链路逐事件转发,无攒积

`方舟 → Python(ark_stream 逐行解析)→ Java(WebClient bodyToFlux 逐事件)→ 前端(readSSE 逐片)` —— 每一层都是收到一个事件立即转发,代码无任何 buffer/攒积/节流。

### 2.2 实测 generate 端点(2026-08-13,直连 Python /api/tutoring/generate)

```
t= 0.02s   ev=meta      (Java 自建,非模型)
t= 6.54s   ev=thinking  len=2  '符合'   ← 首个 thinking 在请求发出 ~6.5s 后才到
t= 6.59s   ev=thinking  len=2  '要求'
... (thinking 32 片,每片 1~2 字,0.7s 内全部到达)
t= 7.23s   ev=token     len=2  '如果'   ← token 紧随其后
... (token 34 片,每片 1~2 字,0.2s 内全部到达)
t= 7.40s   ev=done
```

**关键观察**:
- `thinking` 32 片 + `token` 34 片,全部在 **~0.9s 内涌出**(中位间隔 0.000s)
- 从请求发出到首个事件却要 **~6.5s 静默期**
- 用户看到的"卡顿/一次性输出",根源是:**长时间静默 → 内容瞬间涌出**,而非持续流动

### 2.3 decide 阶段更久

首轮 decide(模型决策 action 类型)实测 **17~48s** 静默,期间前端只有"AI 思考中"占位。当前 Java 侧未透传 decide thinking(Java 侧演进中),但即便透传,若模型端同样是"长时间静默后涌出",体验仍不佳。

## 三、想请教模型端的核心问题

### Q1:静默期能否缩短 / 提前流出?

方舟 Doubao seed 2.0 思考模式下,`generate` 请求发出后约 **6.5s** 才返回第一个 `reasoning_content`。这段时间模型在做什么?是否有办法让思考过程**更早开始流式返回**(而非思考接近完成才吐)?

### Q2:`reasoning_content` 能否随思考过程逐 token 持续输出?

当前实测是"32 片在 0.7s 内全部到达"——即模型内部思考接近完成后才一次性快速吐完 thinking,而不是思考过程中持续流出。ChatGPT/Claude 的体验是**思考过程中逐字持续流动**。方舟是否有配置可以改变这一行为(如 `thinking` 参数、`stream_options`、`max_tokens` 拆分、或专门的思考流模式)?

### Q3:decide 阶段 17~48s 能否优化?

decide(决策 action 类型)的静默期远超 generate。这是否是模型推理复杂度导致的正常现象?是否有模型/参数层面的优化空间(如换更快模型、限制思考轮数、temperature 等)?

### Q4:是否存在流式节奏相关的可用参数?

请确认方舟 OpenAI 兼容接口对以下内容的支持情况(若有则给出参数建议):
- 控制 `reasoning_content` 输出节奏/粒度的参数
- `stream_options.include_usage` 是否可用
- 思考模式(`thinking.type`)的细分选项
- 是否有"边思考边输出"模式(相对"思考完再输出")

## 四、我方已在做的(无需模型端支持)

- 前端:thinking 打字机逐字 reveal + 静默期脉动提示(渲染层平滑)
- Java:decide thinking 透传中(消除 decide 黑盒,但静默仍在模型侧)
- 这些是"治标"——改善观感,无法消除模型静默期本身

## 五、期望

如果模型端能通过参数/接入方式让 `reasoning_content` **在思考过程中持续逐 token 流出**(像 ChatGPT 那样),前端即可呈现真正的流畅流式体验。请评估:
1. 上述 Q1~Q4 哪些有解、怎么解
2. 若无解,是否属于方舟思考模式的固有行为,需产品侧接受

---

*附:实测脚本可按需提供(python3 直接流式打 generate 端点,记录每事件时间/分片长度)。*
