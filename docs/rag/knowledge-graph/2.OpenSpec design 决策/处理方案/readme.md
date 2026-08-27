1. 判断 spec 业务含义（13 design + 13 proposal → 问题地图：每个 spec 解决什么问题）
2. 移动到 `原来的文件/` 下归档（原始素材，仅人肉溯源）
3. 将低价值的 spec 移除/归档（proposal 同源精简版，Why 被 design Context 覆盖）
4. 提示词将高价值的整理出来（`提示词/spec信息补充提示题.md` → 收敛事实增量折入语雀 canonical）
5. 将高价值的 spec 补充到语雀文档中（双轨①：决策 +D# / 选型 +n / 场景 +n / 演进阶段增量）
6. 通过 `提示词/spec文件整理.md` 整理高价值的 spec（双轨②：每份 design 各自成文 `design-*.md` 进切片池，权威 0.7 素材溯源库）
7. 目前还是太原始，需要在此调整 需要人工看一下是否符合 rag 和切片

## 本模块 design 清单（13 份，待第①步评估归档）

| design 文件 | 主题 | 端 |
|---|---|---|
| design-python-2026-03-28-integrate-edukg-knowledge-graph.md | 集成 EduKG 知识图谱 | Python |
| design-python-2026-04-08-kg-infrastructure-init.md | 图谱基础设施初始化 | Python |
| design-python-2026-04-10-knowledge-graph-data-research.md | 图谱数据调研（90KB 大文件） | Python |
| design-python-2026-04-10-textbook-concept-linking.md | 教材知识点↔图谱概念匹配 | Python |
| design-python-2026-04-10-textbook-crawler.md | 教材爬虫 | Python |
| design-python-2026-04-15-kg-math-complete-graph.md | 数学完整图谱构建 | Python |
| design-python-kg-math-prerequisite-inference.md | 前置依赖推断 | Python |
| design-python-kp-match-review-system.md | 知识点匹配评审系统 | Python |
| design-backend-2026-06-03-knowledge-graph-datasource.md | 图谱 datasource 同步后端 | Java |
| design-backend-2026-06-03-knowledge-graph-ui.md | 图谱 UI 后端 | Java |
| design-backend-kp-matching-lightup.md | 知识点点亮匹配后端 | Java |
| design-frontend-2026-06-09-knowledge-graph-ui-front.md | 图谱 UI 前端 | 前端 |
| design-frontend-kp-matching-lightup-frontend.md | 知识点点亮前端 | 前端 |
