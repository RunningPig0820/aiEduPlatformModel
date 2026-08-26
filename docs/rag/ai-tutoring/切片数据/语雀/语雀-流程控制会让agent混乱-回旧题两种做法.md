# 语雀-流程控制会让agent混乱

> summary: 讲AI答疑回旧题的两种做法，及换题判定的代码逻辑
> 权威度: 0.7 ｜ 来源: 语雀 ｜ 锚点: 回旧题两种做法
> 模块: ai-tutoring ｜ 节: 语雀-流程控制会让agent混乱
> COS路径: ai-tutoring/rag-slices/语雀/语雀-流程控制会让agent混乱-回旧题两种做法.md
> 类别：业务流程

---

## 回旧题两种做法

| 做法 | 行为 | 复杂度 |
|------|------|--------|
| A（推荐） | 回旧题 = 开新会话重新引导；旧会话记录（含掌握度、错误、transcript）永久留档 | 状态机零改动，纯线性 |
| B | 断点恢复旧会话（ARCHIVED 可转回 GUIDING） | 需给 ARCHIVED 加 resume 转换，状态机出现回边 |

断点恢复（F6）的边界要收紧：只用于"同一个会话内暂时离开"（比如中途退出 app，Redis TTL 内回来续聊）；不用于换题后的回跳。这样就不需要"多会话栈"或"回边"，状态机保持纯线性。

> ⚠️ **最新逻辑（2026-08 代码）**：换题判定权**回 Java**——Java 检测新题图 URL 首次出现 → decide 请求带 `is_new_question=true` → Python **短路返回 switch（不调 LLM）** → Java 重置计数（`TutoringAppService.sendMessage`）。原因：Python 无状态，无法区分"本轮刚换题" vs "早几轮已换在答题"；由 Java 在"新图出现这一轮"置信号最可靠。
