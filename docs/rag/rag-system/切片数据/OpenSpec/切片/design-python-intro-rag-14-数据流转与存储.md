# 数据流转与存储

> summary: 数据流转与存储（design-python-project-intro-rag）：离线链路（完善文档→切片+metadata→embedding→COS建rag-index --clear幂等）+在线链路分阶段，新增/api/rag/*独立路由回滚安全
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-python-intro-rag-14-数据流转与存储.md
> 类别：数据关联

---

### Migration Plan:迁移计划

> 检索摘要：落地分几步？先产知识图谱完善文档作标本定格式，离线脚本切片+metadata+embedding建COS rag-index(--clear幂等)，在线链路分阶段，新增/api/rag/*独立路由回滚安全

1. 先产出「知识图谱」完善文档作标本 → 确认格式 → 补其余 3 模块(+ RAG 功能点文档)。
2. 离线脚本:完善文档 → 切片 + metadata → embedding → COS 建 rag-index(`--clear` 幂等)。
3. 在线链路分阶段:召回 → 打分/范围门 → 生成/引用 → 权限门 → 降级 → token 展示。
4. 回滚:新增 `/api/rag/*` 独立路由,不影响既有 tutoring 路径;ark_stream 改动对既有调用透明(多返回 usage,不改变流式语义)。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-python-project-intro-rag.md`（§Migration Plan）
