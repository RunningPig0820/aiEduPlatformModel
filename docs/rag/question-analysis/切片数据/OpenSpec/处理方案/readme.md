# 切片数据 / OpenSpec / 处理方案

> 本来源（2.OpenSpec design 决策）从源文档到切片数据的完整处理路径。

## 一、源头

- 源文档：`2.OpenSpec design 决策/design-*.md`（6 份 RAG 版，权威 0.7，素材溯源库；85 个 `###` 小节）
- 原始草稿归档：`2.OpenSpec design 决策/原来的文件/`（证据源，不进库）
- 生成提示词：`2.OpenSpec design 决策/处理方案/提示词/spec文件整理` + `spec信息补充提示词`（双轨：spec 自身成文进池 + 收敛事实折入语雀 canonical）

## 二、切片（2026-08-27 改：提示词 + 大模型按 ### 切）

> 脚本导出（export_slices_md.py）方案已废弃，与 代码/坑档案/引导问题/语雀 对齐改用 **提示词 + 大模型**。提示词：`提示词/OpenSpec-切片-提示词.md`。

- 按 `###` 切，一个决策/小节一块（决策 D# 归一化；背景/目标非目标/风险/迁移/开放问题/验收反馈各自成块）
- 100% 保留 Migration/Risks/OpenQuestions；`# ==== 分节 ====` 分隔线不作 chunk
- 头部精简 6 行（summary 完整保留 + 权威度 0.7 + 模块 + COS路径 + 类别 + 状态）；机器元信息（entry_id/source_doc/status tag）由 QT⑥⑦ 摄入时从文件名+状态推导，md 头不写
- 块元数据 `authority=0.7 + source=OpenSpec`（同切片池，不物理隔离第三索引——靠元数据识别）

## 三、切片结果

- 约 85 块（backend-kp 18 / backend-qtm 15 / frontend-kp 14 / frontend-qtm 20 / python-signal 8 / python-qtm 10），全落 `切片/`

## 四、检索侧规则

- design_spec 只做**补充溯源**：优先 0.8/1.0 真相源，主库无答案才允许引用 0.7 素材库；引用必须提示「该信息来源于历史设计文档，请核对代码确认实际落地情况」，禁止把 ⚠️/❓ 当已上线功能。
