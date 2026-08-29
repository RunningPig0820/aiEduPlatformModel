# 前置依赖与学习路径：LLM 多模型投票

> summary: 前置依赖与学习路径（LLM 多模型投票）
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-data-research-07-前置依赖与学习路径-2.md
> 类别：数据关联

---

> 检索摘要：前置依赖怎么用 LLM 多模型投票构建？GLM-4-flash(免费主力)+DeepSeek-V3(投票验证)两模型，temperature 0.3、批大小 10、滑动窗口携带前序章节核心知识点上下文；Few-Shot 提示词严格区分核心前置 vs 教学顺序；幻觉检测+JSON 容错（支持数组/对象、修复尾逗号、过滤不存在知识点）；两模型一致才采纳取平均置信度。

**LLM 配置（状态：）**
- providers: [zhipu, deepseek]；model: glm-4-flash + deepseek-V3；scene: prerequisite_inference；temperature 0.3（降低随机性提高一致性）；batch_size 10（调小批次提高精度）；max_retries 2
- 滑动窗口上下文：context_window = {prev_chapter_kps: 20（前序章节核心知识点数）, same_chapter_kps: 50（同章节知识点数）}

**Few-Shot Prompting（智谱建议，状态：）**：在 Prompt 中增加高质量标注示例，引导模型区分**核心前置（概念依赖）**与**教学顺序（时间依赖）**：
- 任务：判断知识点 A 是否是学习 B 之前必须掌握的**核心前置知识**（不学 A 则无法理解/学会 B，无论教学顺序）。
- 示例1 正确判断："一元二次方程"核心前置 ["方程"]（confidence 0.95，方程是定义核心概念）；"二次函数"核心前置 ["函数"]（0.9，函数特例）。
- 示例2 区分教学顺序："圆的性质"核心前置 []（教材先教勾股定理，但学圆性质不需要先学勾股定理，两者独立）。
- 示例3 反例警示：因"勾股定理"和"圆"在同一章就判定前置；将"方程"作为"二次函数"前置（辅助但不绝对必须）。
- 输入：前序章节核心知识点表 + 当前批次知识点表（名称/类型/定义描述）；输出**严格 JSON 数组**：[{target, prerequisites, reason, confidence}]，前置必须在列表中（不能虚构），无则空数组，只输出 JSON 数组不要额外解释。

**滑动窗口上下文（智谱建议，状态：）**：解决跨章节依赖识别——携带最近 2 个前序章节核心知识点作为批次上下文。核心知识点选取优先级：① 定义类知识点（score+100）② 高频被引用（ref_count，上限 50）③ 教材标注"重点"（+30）④ 向量相似度（可选，当前章节核心定义与前序章节计算相似度取最相关）。

**幻觉检测 + JSON 容错（智谱建议，状态：）**：支持 JSON 数组（新）/对象（旧）双格式；移除 markdown 代码块标记；修复尾逗号（,\s*}→} / ,\s*]→]）；解析失败走 aggressive_json_repair（提取所有 {…} 拼接兜底，失败返回空对象）；幻觉检测过滤不在合法知识点集合的名称/前置名，丢弃并告警；数组格式转换为按 target 聚合的统一对象。

**投票合并算法（状态：）**：两个模型各自输出候选关系，按 (from_kp, to_kp) 聚合投票；**至少两个模型输出一致才采纳**，置信度取两模型平均，evidence_types=["llm_inference"]、source="llm_multi_vote"；单模型结果不采纳。

**前置关系构建方案（已确认：LLM 推理，状态：）**：模型选 GLM-4-flash（免费，主力）；复用现有 LLM Gateway 新增 prerequisite_inference scene；按学科分组、按章节/主题分批（每批 50）；置信度 <0.7 直接丢弃不做人工审核；relateTo 数据保留为 RELATED_TO，Demo 阶段不做 LLM 验证补充，核心闭环跑通后再优化。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§5.5 LLM 多模型投票、§8.3 前置关系构建方案）
