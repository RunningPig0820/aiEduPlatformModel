# 坑档案

> summary: 解决COS transcript签名URL泄露及CORS依赖问题
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J10. COS transcript 签名 URL 泄露 / CORS
> 模块: ai-tutoring ｜ 节: 坑档案

---

### J10. COS transcript 签名 URL 泄露 / CORS
- **坑**：前端直连 COS 拿签名 URL，泄露 + CORS 依赖。
- **解决**：transcript 改**后端代理**（`GET /sessions/{id}/transcript`），前端零 COS 直连；删除 detail 签名 URL。
- **证据**：`74fadad`；前端 `5d9b68d`、`c3542b6`。
