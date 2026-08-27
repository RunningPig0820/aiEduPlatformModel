# 全量知识点分页接口（学生端知识点总览）

> summary: 新增 POST /api/kg/knowledge-points 按学段分页列教材知识点，Mapper 反向 JOIN 从 textbook 过滤到知识点，供学生端全量知识地图底图。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D14-全量知识点分页接口-学生端知识点总览.md
> 类别：数据关联

> 检索摘要：新增 POST /api/kg/knowledge-points 按学段分页列教材知识点，Mapper 反向 JOIN 从 textbook 过滤到知识点，供学生端全量知识地图底图。

**决策**：新增 `POST /api/kg/knowledge-points`（body `{stage, page, size}`，对齐现有 kg 接口全 POST body 风格），按学段分页列教材知识点，每项带 `kpUri`/`kpLabel`/`stage`/`chapterLabel`/`sectionLabel`。

**实现**：Mapper 反向 JOIN（`t_kg_textbook`[stage 过滤] → `t_kg_textbook_chapter` → `t_kg_chapter_section` → `t_kg_section_kp` → `t_kg_knowledge_point`）+ COUNT 分页。数据源 kg 镜像只读。

**权限**：登录即可（学生端），路径 `/api/kg`（区别于 `/api/auth/kg` 管理前缀）。

**理由**：知识点总览是"全量知识地图"底图（1000+ 条），按学段分页避免一次拉全量；`chapterLabel`/`sectionLabel` 供前端"学段→章节→知识点"二次分组。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D14 全量知识点分页接口（学生端知识点总览））
