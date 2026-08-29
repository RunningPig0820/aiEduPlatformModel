# 两道门分别挡什么？权限门为什么在 Java、范围门为什么只在白盒链路？

> summary: 两道门分别挡什么？权限门为什么在 Java、范围门为什么只在白盒链路？
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-32-架构设计-两道门分别挡什么权限门为什么在Java范.md
> 类别：架构设计

---

## 回答

**核心结论**：权限门挡"能不能看"（Java 角色门、非学生 403、0 token）；范围门挡"有没有覆盖"（0.75/0.5 双路都低才拒、短路不调 generate）；范围门 0.75/0.5 **只在白盒 check_boundary 生效**，1.6C 旧端点只有空命中拒答。

**分层展开**：
- **权限门**：挡"能不能看"——Java 网关 `requireStudent`→`TutoringAuth.isStudent`（可信 HttpSession 取 role），仅 STUDENT 放行、非学生固定 403、0 token 不产 trace；Python 无权限门，只有 `verify_internal_token` 服务鉴权（依据：完善文档 09 / 分析-08）。
- **范围门**：挡"有没有覆盖"——白盒 `check_boundary`：rerank 空 → 拒答；或 `vec_conf<0.75 且 bm_conf<0.5` 双路都低才拒、单路高即过；触发 → boundary 固定话术 + **短路不调 generate**（0 token 防无谓成本）（依据：完善文档 09 / 分析-04）。
- **权限门为什么在 Java**：Java 是天然聚合点（token/trace/session 每轮过手），角色从可信 session 取、body 传 role 忽略；Python 无状态、不自己认证，保住无状态边界可水平扩展（依据：完善文档 03 / 分析-08）。
- **范围门只白盒**：1.6C `/query` 端点无 0.75/0.5 阈值门，只有 `if not hits` 空命中拒答（模块 docstring 自称"置信度过低→拒答"与实际不符）；范围门 0.75/0.5 只在白盒链路 + 评测边界拒答类型生效（依据：完善文档 09 / 分析-04 / 分析-07）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 32 问）｜ `4.完善文档/03-为什么这么设计.md`、`09-权限与边界.md` ｜ `3.代码/分析-04-检索编排.md`、`分析-08-Java后端网关与SSE中继.md`
