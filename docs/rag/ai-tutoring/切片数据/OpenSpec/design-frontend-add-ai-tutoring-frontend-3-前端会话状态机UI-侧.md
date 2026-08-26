# design-frontend-add-ai-tutoring-frontend

> summary: 讲解AI答疑前端的会话状态机设计逻辑
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 3. 前端会话状态机(UI 侧)
> 模块: ai-tutoring ｜ 节: design-frontend-add-ai-tutoring-frontend
> 类别：业务流程

---

### 3. 前端会话状态机(UI 侧)

后端是"生命周期 3 态 + 护栏计数器",前端在页面内维护**交换级状态**驱动渲染:

```
         ┌────────────────────────────────────────────┐
         │  UI state: activeSession / noSession / ended │
         └────────────────────────────────────────────┘
   发送消息(或 start/request-answer)
         │
         ▼
      phase = SENDING         输入禁用,user 气泡入队
         │
         ▼
  收到 meta → phase = STREAMING
      meta.type 决定徽标;denied 字段可选提示"已调整为思路"
         │
         ▼
  token 累积 → 流式气泡实时渲染(markdown + katex)
         │
         ▼
  done → phase = IDLE
      更新 roundCount/状态;若 ARCHIVED → 切 ended 视图(总结卡片)
      写 localStorage
```
- `switch` → 渲染"已切换到新题 · 从第 1 轮重新计数"分隔,本地 answerRequestCount 归零
- `end`/ARCHIVED → 结束视图 + 总结卡片
- 任意阶段收到 50002/50003/50004/50005 → 错误映射(见决策 7)
