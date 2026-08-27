# 10. 错误处理
> summary: 错误处理：树展开与图谱加载失败给重试按钮，渲染异常由 Error Boundary 捕获，未登录无权限统一拦截跳登录。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/frontend-2026-06-09-knowledge-graph-ui-front-D10-错误处理.md
> 类别：开发难点

> 检索摘要：错误处理：树展开与图谱加载失败给重试按钮，渲染异常由 Error Boundary 捕获，未登录无权限统一拦截跳登录。

- 树节点展开和图谱加载失败时，提供"重试"按钮和友好错误提示
- 图谱渲染异常由全局 Error Boundary 捕获
- 未登录或无权限时，API 层统一拦截并跳转登录

> 证据：详见 `2.OpenSpec design 决策/design-frontend-2026-06-09-knowledge-graph-ui-front.md`（§10. 错误处理）
