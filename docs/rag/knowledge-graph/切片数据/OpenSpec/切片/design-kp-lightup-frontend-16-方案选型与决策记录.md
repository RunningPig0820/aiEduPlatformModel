# 方案选型与决策记录

> summary: 方案选型与决策记录
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kp-lightup-frontend-16-方案选型与决策记录.md
> 类别：架构设计

> 检索摘要：知识点点亮前端关键决策：掌握度以题型为主体展示（知识点由题型→知识点映射派生）；学习报告为总纲下挂掌握度+知识点总览；掌握度与题型分析合并一页；KnowledgeGraph 加可选 masteryMap prop 叠加、拒绝复制学生版组件；澄清卡 inline 非阻塞两步接口 resolve+vote；管理端审核队列后端就绪但本期前端不做；派生覆盖度契约后端同时返回 coverage 0-75 与离散四档；大列表后端分页、学生本人明细前端 slice。

**决策清单（本文档内各方案选型与决策的合并）**

1. 掌握度展示主体：掌握度以题型为主体展示（知识点由「题型→知识点映射」派生），纠正原先以知识点为主键的链路。理由：学会鸡兔同笼不等于掌握二元一次方程，题型是直接观测主体，知识点是抽象，把掌握度直接落在知识点上会夸大能力。
2. 学习报告页面结构：学习报告为总纲（摘要卡：题型计数），下挂「掌握度」（题型四类明细）与「知识点总览」（题型派生全量地图）；摘要 + 明细 + 全图诉求不同混一页会重，「题型明细」与「题型→知识点」是同一维度两层，合成一页。
3. 题型分析导航归属：掌握度（题型）与题型分析（题型→知识点）合并为一页——掌握度页点题型展开派生知识点；不再设独立「题型分析」子菜单，也不挂在错题本下（错题本是「错题」维度，题型分析是「掌握度」维度）。
4. KnowledgeGraph 叠加：给 `KnowledgeGraph.jsx` 加可选 `masteryMap` prop 叠加掌握度重着色，admin 图谱页不传保持零影响；替代方案（单独复制学生版组件）被拒绝——重复维护 ReactFlow/dagre 逻辑，双入口共享组件符合复用目标。
5. 澄清卡交互：答疑澄清卡用 inline 非阻塞（聊天线程内、可忽略），区别于现有 modal（单向门拦人）；采用两步接口 `POST /api/kp/resolve` 展示题型候选 + `POST /api/kp/vote` 落 `student_vote`，跳过即弃权。
6. 管理端审核队列：管理端审核接口（`GET/POST /api/kg/aliases/pending`）后端已就绪但本期前端不做，后续挂 `/admin/knowledge-graph` 页；教师端同理不做。
7. 数据契约：知识点派生覆盖度契约后端同时返回覆盖度 coverage（0-75）与离散四档 masteryLevel（0/25/50/75）及 status/confidence；着色用离散档，详情进度条用 coverage（百分比 = coverage/75*100）。
8. 分页策略：全量知识点/题型库大列表后端分页（`page`/`size` + `total`）；学生本人题型掌握度明细（几十条）前端 `slice` 即可。
9. Non-Goals：本期不做管理端挂起审核 UI、教师端、错题本错题列表页；不改权威图谱、不做同步/统计功能。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-matching-lightup-frontend.md`（§Goals/§4 题型分析合并/§5 masteryMap/§6 着色/§7 澄清卡/§8 管理端/§Risks/§Open Questions）
