# 坑档案

> summary: 解决isEnded TDZ导致的白屏问题
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: F7. isEnded TDZ 白屏
> 模块: ai-tutoring ｜ 节: 坑档案

---

### F7. isEnded TDZ 白屏
- **坑**：历史链路触发 TDZ（temporal dead zone）白屏。
- **解决**：修复 isEnded 初始化时机。
- **证据**：`ef8ee61`。
