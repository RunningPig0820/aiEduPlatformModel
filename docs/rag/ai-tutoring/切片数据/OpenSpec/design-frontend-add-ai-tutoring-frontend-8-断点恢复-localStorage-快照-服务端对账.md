# design-frontend-add-ai-tutoring-frontend

> summary: 讲AI答疑的断点恢复及本地快照对账方案
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 8. 断点恢复:localStorage 快照 + 服务端对账
> 模块: ai-tutoring ｜ 节: design-frontend-add-ai-tutoring-frontend
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-frontend-add-ai-tutoring-frontend-8-断点恢复-localStorage-快照-服务端对账.md
> 类别：开发难点

---

### 8. 断点恢复:localStorage 快照 + 服务端对账

规避"无活跃会话查询接口"缺口,不新增后端接口。

localStorage schema(`ai_tutoring_sessions`,上限 10 条,先进先出):
```json
[{
  "id": 1001,
  "title": "鸡兔同笼,共35头94脚…",   // 首条用户消息截断
  "status": "ACTIVE",
  "messages": [{ "role": "user|ai", "content": "...", "type": "hint"?, "createdAt": 1710000000000 }],
  "roundCount": 3,
  "updatedAt": 1710000000000
}]
```

进入页面时序:
1. 读 localStorage → 有 ACTIVE 会话 → **秒渲染本地快照**(离线也可见,DeepSeek 感)
2. 同时 `GET /sessions/{id}` 对账:
   - ACTIVE → 校正 roundCount/answerRequestCount/status;若服务端 recentMessages 多于本地(多设备)则补齐
   - 50003 → 切 ended 视图(本地保留为历史)
   - 50002 → 本地降级为历史,引导新会话
3. 无本地会话 → 空状态引导("拍题或输入一道数学题" + 示例)
4. 每次 `done` / 归档后写 localStorage

轻量历史入口(方案 A):页面内提供"历史"下拉/抽屉,可回看最近会话;历史回看只读。
