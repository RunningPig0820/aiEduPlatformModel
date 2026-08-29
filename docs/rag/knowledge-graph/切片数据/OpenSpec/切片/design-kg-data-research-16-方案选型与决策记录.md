# 方案选型与决策记录

> summary: 方案选型与决策记录
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-data-research-16-方案选型与决策记录.md
> 类别：架构设计

---

> 检索摘要：本文档做了哪些关键设计选型决策？前置构建确认为 LLM 推理(GLM-4-flash 免费主力、batch 50、温度0.3、<0.7 丢弃)、状态存储 MySQL 替代 SQLite、缓存键 SHA256 替代 MD5、年级倒置改宽松按跨度惩罚、定义依赖改词边界匹配防误报、mark 字段兼容解析、跨源映射表、学科分三类处理、成本估算修正。

本文档关键选型与决策记录（OpenSpec 设计素材层，权威度 0.7；=设计决策，落地请以代码/真相源核对）：

1. **前置关系构建方案已确认 LLM 推理（状态：）**：GLM-4-flash 免费主力、batch_size 50、temperature 0.3、置信度 <0.7 直接丢弃不做人工审核；relateTo 保留为 RELATED_TO，Demo 阶段不做 LLM 验证补充，核心闭环跑通后再优化。复用现有 LLM Gateway 新增 prerequisite_inference scene。
2. **状态管理 MySQL 替代 SQLite（状态：）**：已有 MySQL 环境无需额外安装、并发性能好、运维工具丰富、数据安全有备份机制；承接处理状态/LLM 缓存/成本表。
3. **缓存键 SHA256 替代 MD5（状态：）**：避免碰撞风险；基于 uri 排序 + prompt_version + model 生成唯一缓存键，取 32 位。
4. **年级倒置宽松处理（状态：）**：原方案把"高年级指向低年级"直接判异常，但跨学段复习/螺旋式课程设计合理（如高二物理用初三数学）；改为按年级跨度惩罚置信度 ×0.95/0.9/0.5/0.3，<0.6 降级候选。
5. **定义依赖抽取改进（状态：）**：原简单字符串匹配误报多（"指数"匹配"指数函数"、"合"匹配"集合"）；改进为词边界匹配 + 停用词表 + 同义词映射 + 概念层级追溯。
6. **mark 字段兼容解析（状态：）**：mark 格式不统一（6.2.1/6-2-1/第六章第二节/Chapter 6.2.1）；parse_mark_field 兼容解析返回(章节,小节,序号)，无法解析按教材序号 fallback。
7. **跨源映射表（状态：）**：为未来引入好未来等外部数据建立 SQLite kp_source_mapping（canonical_uri/external_id/source_name/confidence），避免 URI 变化导致关系失效。
8. **学科分三类处理策略（状态：）**：强逻辑链(数理化生)→PREREQUISITE P1；语言(英语)→语法词汇层级 P2；主题(历史语文地理政治)→主题分类 P3。
9. **成本估算修正（状态：）**：数学 4490 知识点/批 50 ≈ 90 次（智谱指出非 1000 次），两模型投票 180 次 +10% 重试 ≈ 200 次；GLM-4-flash 免费、DeepSeek 付费约 1-2 元。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§8.3、§13.2、§13.6、§9.3、§5.4、§4.2.1、§2.2.1、§8.1、§14.1）
