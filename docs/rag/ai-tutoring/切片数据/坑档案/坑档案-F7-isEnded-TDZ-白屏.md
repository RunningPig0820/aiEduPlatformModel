# 坑档案

> summary: 解决isEnded TDZ导致的白屏问题
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: F7. isEnded TDZ 白屏
> 模块: ai-tutoring ｜ 节: 坑档案
> COS路径: ai-tutoring/rag-slices/坑档案/坑档案-F7-isEnded-TDZ-白屏.md
> 类别：开发难点

---

### F7. isEnded TDZ 白屏
**1. 问题现象**：历史链路触发 TDZ（temporal dead zone）白屏——页面直接白屏不可用。

**2. 触发流程**：历史链路（HistoryDrawer 选中会话 / 挂载恢复）走 `loadSession`/`reconcileSession`。提交 `ef8ee61` 前的代码：`const isEnded = sessionState === 'ended'` 声明在**文件尾部**（`useMemo` 之后、`return` 之前），而前面 `useEffect(() => { refreshHistory() }, [sessionId, roundCount, isEnded])` 的依赖数组**引用后部的 `const isEnded`**。

**3. 根因分析**：JS 暂时性死区（TDZ）：`const isEnded` 在声明前被 `useEffect` 依赖数组读取 → `ReferenceError: Cannot access 'isEnded' before initialization` → 组件白屏。本质是"**变量声明位置晚于被引用处**"。

**4. 排查过程**：从"白屏"反推 → 看浏览器 console ReferenceError → 定位到 `useEffect` 依赖数组引用后部 `const`。

**5. 解决方案 & 改动点**：提交 `ef8ee61`——`isEnded` 声明**提前到该 `useEffect` 之前**（当前 `useTutoringSession.js:753`），消除依赖数组引用后部 `const` 的 TDZ。

**6. 面试口述要点**：讲"**TDZ 是 JS 常见但隐蔽的初始化坑**"——const 声明前被读必抛 ReferenceError。踩坑收获：**hook 依赖项用到的变量要声明在 hook 之前**；这类白屏优先看 console 的 ReferenceError，比猜渲染问题快。

---
