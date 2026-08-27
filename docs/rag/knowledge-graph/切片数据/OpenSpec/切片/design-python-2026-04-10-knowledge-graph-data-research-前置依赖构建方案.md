# 前置依赖构建方案
> summary: 前置依赖构建核心原则：教学顺序≠学习依赖，教材顺序存 TEACHES_BEFORE，真正学习依赖存 PREREQUISITE。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-前置依赖构建方案.md
> 类别：数据关联

---

### 五、前置依赖关系构建方案（多证据融合）
> 检索摘要：前置依赖构建核心原则：教学顺序≠学习依赖，教材顺序存 TEACHES_BEFORE，真正学习依赖存 PREREQUISITE。

#### 5.1 核心原则
> 检索摘要：核心原则：教学顺序≠学习依赖，教材顺序存 TEACHES_BEFORE，真正学习依赖存 PREREQUISITE。

教学顺序 ≠ 学习依赖
教材章节顺序是教学安排顺序，不一定等于学习依赖顺序。
● 例如："勾股定理"在教材中先于"圆"，但学圆不需要先学勾股定理
● 因此：教材顺序存为 TEACHES_BEFORE，真正的学习依赖存为 PREREQUISITE

### 5.2 证据来源分类
> 检索摘要：前置依赖证据来源四类：教材章节顺序(0.7)、定义/定理依赖(0.85)、LLM多模型投票(0.8)、教师标注(1.0)，Demo 阶段按证据权重分流。

证据类型	说明	基础权重	Demo 阶段策略
教材章节顺序	同章节内按 mark 顺序	0.7	→ TEACHES_BEFORE
定义/定理依赖	从定义文本中抽取的关键概念	0.85	→ PREREQUISITE（实现）
LLM 多模型投票	GLM + DeepSeek 两模型一致	0.8	→ PREREQUISITE/CANDIDATE
教师标注	人工审核	1.0	Demo 阶段不做

### 5.3 教材章节顺序（仅生成 TEACHES_BEFORE）
> 检索摘要：教材章节顺序仅生成同章节内 TEACHES_BEFORE 关系（教学顺序），不直接转化为 PREREQUISITE。

仅生成同章节内的 TEACHES_BEFORE 关系，不直接转化为 PREREQUISITE。
def infer_teaches_before(knowledge_points):
"""
按教材和章节分组，按 mark 顺序生成 TEACHES_BEFORE 关系
注意：这是教学顺序，不是学习依赖
"""
teaches_before = []
for textbook, kps in group_by_textbook(knowledge_points):
sorted_kps = sort_by_chapter_and_mark(kps)
for i in range(1, len(sorted_kps)):
prev = sorted_kps[i-1]
curr = sorted_kps[i]
if prev.chapter == curr.chapter:  # 仅同章节
teaches_before.append({
'from': prev.uri,
'to': curr.uri,
'confidence': 0.85,
'source': 'textbook_chapter',
'evidence': ['chapter_order']
})
return teaches_before

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§五、前置依赖关系构建方案（多证据融合））
