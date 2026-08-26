# 坑档案

> summary: 解决COS transcript签名URL泄露及CORS依赖问题
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J10. COS transcript 签名 URL 泄露 / CORS
> 模块: ai-tutoring ｜ 节: 坑档案
> COS路径: rag-slices/ai-tutoring/坑档案/坑档案-J10-COS-transcript-签名-URL-泄露-CORS.md
> 类别：开发难点

---

### J10. COS transcript 签名 URL 泄露 / CORS
**1. 问题现象**：前端直连 COS 拿签名 URL 下载 transcript——签名 URL 可被转发泄露（凭据外泄风险），且存储桶需配 CORS 给前端域（依赖环境）。

**2. 触发流程**（旧链路）：前端从 `detail/archive` 响应拿 `transcriptUrl`（COS 签名 URL）→ 前端直连 COS 下载。

**3. 根因分析**：把**签名 URL 交给前端** = 把 COS 临时凭证交给浏览器，任何拿到 URL 的人都可下载；且 COS 桶 CORS 配置跟前端域绑定，环境迁移就得改。本质是"**存储访问凭证外露 + 安全边界模糊**"。

**4. 排查过程**：安全 review 发现 transcriptUrl 落到前端响应 → 确认签名 URL 可转发（泄露面）且依赖桶 CORS（环境耦合）。

**5. 解决方案 & 改动点**：
- 新增后端代理 `GET /sessions/{sessionId}/transcript`（`TutoringController.java:166-172`），服务端读 COS 透传，前端零 COS 直连
- `FileStorageService` 新增 `download(objectKey)`（`cosClient.getObject`，404 NoSuchKey → null）；`TutoringTranscriptArchiver` 新增 `readMessages`（key=`TRANSCRIPT_DIR/{studentId}/{sessionId}.json`，损坏/缺失 → 空列表）
- `TutoringSessionDTO` 删 `transcriptUrl` 字段、assembler 删映射、`resolveTranscriptUrl`/`transcriptUrlExpireMinutes` 死代码清理；内部 DB/Redis objectKey 保留

**6. 面试口述要点**：讲"**签名 URL 不该下发给前端**"——COS 临时凭证到浏览器 = 泄露面 + CORS 依赖。技术权衡：**后端代理**（服务端读 COS 透传）换取"前端零直连 + 权限收敛到后端"，代价是加一层转发。踩坑收获：**所有存储访问收敛到后端，前端永远不拿云厂商凭证**。

---
