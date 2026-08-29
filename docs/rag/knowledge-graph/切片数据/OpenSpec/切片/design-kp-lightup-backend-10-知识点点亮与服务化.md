# 知识点点亮与服务化

> summary: 知识点点亮与服务化
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kp-lightup-backend-10-知识点点亮与服务化.md
> 类别：操作流程

---

> 检索摘要：掌握度显示=掌握值×置信档位两维，低置信/挂起渲染疑似态（虚线+待确认角标）；复用 KnowledgeGraph.jsx 新增学生端图谱页；服务化接口含学生疑似接口、全量知识点分页、题型库分页、掌握度明细与派生覆盖度接口。

**D6 点亮 + 疑似态**：掌握度显示 = 掌握值 × 置信档位两维。

| 档位（MasteryLevel 五档） | 掌握值 | 语义 | 前端视觉 |
|---|---|---|---|
| notStarted | 0 | 未开始（还没学） | 中性灰 |
| beginner | 25 | 入门/薄弱 | 红 |
| intermediate | 50 | 进阶/练习中 | 黄 |
| advanced | 75 | 高级/掌握 | 绿 |
| master | 100 | 精通 | 深绿 |
| 解析低置信/挂起 | — | 疑似 | 虚线 + 「待确认」角标 |

- 挂起 label 不落掌握度（不污染数据），前端渲染「疑似薄弱」待确认态。
- MasteryItemDTO 增加 status(RESOLVED/PENDING) + confidence；前端再叠加 obs 的 PENDING 列表渲染疑似节点。
- 掌握度回退（错解析）：重判把 二元一次方程组→假设法 后，错记在旧 kp 上的掌握度打标 MIGRATED + 挂人工复核，不自动删（自动删可能丢真实信号）。本期只打标 + 记录迁移日志，自动迁移列为后续。

**D7 学生端图谱页**：复用 KnowledgeGraph.jsx 组件，新增学生路由 + 页面（当前学生端无图谱页，仅 admin 有）。取图：现有 POST /api/auth/kg/knowledge-points/graph（节点带 uri）。取掌握度：增强后 GET /api/students/{id}/mastery。匹配：mastery.kpKey == node.id → 按档位着色。疑似节点从 obs PENDING 列表渲染虚线 + 角标。

**D12 学生端疑似接口 + obs 接入答疑主流程**：
1. 学生端疑似接口 GET /api/students/{id}/pending-kps：返回该生 status=PENDING/WEAK 的派生观测（学生权限，studentId 必须等于会话 userId）。学生端「待确认清单」（疑似薄弱点）的数据源。
2. obs 接入答疑主流程：applyMasteryAndErrors 升级为调用 resolve(label, session.getStudentId())（替代 resolveLabelToUri 的 default 兼容路径），使解析产生 obs、年级锚生效；掌握度写入同步取 status/confidence（不再硬编码 RESOLVED）。

理由：前端对接暴露两个断层——(a) getMastery 硬编码 RESOLVED，学生拿不到自己的疑似点（现有 pending 接口是 ADMIN/TEACHER 专属且返回全体）；(b) 灰度遗留：resolveLabelToUri 传 null，obs 派生层未接进答疑主流程，题型库聚合/维护闭环无输入数据。

**D13 知识点学段/章节归属反查（mastery stage 字段）**：MasteryItemDTO 增加 stage（primary/middle/high）+ 可选 chapterLabel/sectionLabel。反查链路沿用现有 getKnowledgePointDetail 的 kp→section→chapter 两级，再延伸一跳 chapter→textbook 取 stage：
kp_uri → t_kg_section_kp → t_kg_chapter_section → t_kg_textbook_chapter → t_kg_textbook(stage)

批量反查：新增值对象 KgKpPlacement（kpUri/stage/chapterLabel/sectionLabel）+ KgKnowledgePointRepository.findPlacementByUris(List<String>)，Mapper 一条 LEFT JOIN SQL 批量反查（getStudentMastery 一次返回多 kp，避免 N+1）。一个 kp 挂多个 section 时取首个非空 stage（跨教材同 kp 罕见，取先收录）。理由：学生掌握点天然跨年级（三年级可问初中内容），「按年级框定范围」的前提不成立；学段是更宽更稳的分组粒度。stage 已在 KgTextbook.stage（与 KgStageEnum code 对齐），零 schema 变更，纯反查。

**D14 全量知识点分页接口（学生端知识点总览）**：新增 POST /api/kg/knowledge-points（body {stage, page, size}，对齐现有 kg 接口全 POST body 风格），按学段分页列教材知识点，每项带 kpUri/kpLabel/stage/chapterLabel/sectionLabel。实现：Mapper 反向 JOIN（t_kg_textbook[stage 过滤] → t_kg_textbook_chapter → t_kg_chapter_section → t_kg_section_kp → t_kg_knowledge_point）+ COUNT 分页。数据源 kg 镜像只读。权限：登录即可（学生端），路径 /api/kg（区别于 /api/auth/kg 管理前缀）。理由：知识点总览是「全量知识地图」底图（1000+ 条），按学段分页避免一次拉全量；chapterLabel/sectionLabel 供前端「学段→章节→知识点」二次分组。

**D15 题型库分页 + 关联知识点接口（题型分析）**：新增 GET /api/kp/question-types?page=1&size=20：分页列题型（id/topicLabel/status/hitCount + total），QuestionTypeRepository 补 findPage。GET /api/kp/question-types/{id}/knowledge-points：该题型关联知识点（QuestionTypeKpRepository.findByQuestionTypeId 已有 + kgKnowledgePointRepository.findByUris 反查 kpLabel），返回 kpUri/kpLabel/gradeRange/ratio/hitCount。理由：题型分析页需「题型库浏览 + 通过题型看关联知识点」。QuestionType/QuestionTypeKp 目前只有 kp_uri 无 name，kpLabel 从 kg 镜像反查（不冗余存 name，权威标签唯一来源 kg 镜像）。

**D19 掌握度接口改造 + 派生覆盖度接口**：
1. 改造 GET /api/students/{id}/mastery → 返回题型掌握度 items[] { topicKey, topicLabel, masteryLevel, status, confidence, updatedAt }。
2. 新增 GET /api/students/{id}/kp-coverage → 返回知识点派生覆盖度 items[] { kpUri, kpLabel, coverage, masteryLevel, status, confidence, stage, chapterLabel, sectionLabel }。
3. 已实现保留：POST /api/kg/knowledge-points（全量知识点分页）、GET /api/kp/question-types（题型库分页）、GET /api/kp/question-types/{id}/knowledge-points。

理由：题型掌握度与知识点覆盖度是两个不同粒度视图（一个按题型、一个按知识点），拆开各自清晰。stage/chapterLabel/sectionLabel 从 mastery 移入覆盖度接口（这些是知识点的归属属性，题型无归属语义）；kpLabel 反查沿用 kg 镜像（权威标签唯一来源）。
