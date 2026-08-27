# 前置依赖构建方案（续）
> summary: 前置依赖构建核心原则：教学顺序≠学习依赖，教材顺序存 TEACHES_BEFORE，真正学习依赖存 PREREQUISITE。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-前置依赖构建方案-5.md
> 类别：数据关联

---

### 五、前置依赖关系构建方案（多证据融合）（续）

> 检索摘要：前置依赖构建核心原则：教学顺序≠学习依赖，教材顺序存 TEACHES_BEFORE，真正学习依赖存 PREREQUISITE。

#### 5.5.2 滑动窗口上下文（智谱建议）
> 检索摘要：滑动窗口上下文解决跨章节依赖识别：携带最近2个前序章节核心知识点（按定义类/引用频次/重点标注优先级选取）作为批次上下文。

解决跨章节依赖识别问题：携带前序章节核心知识点作为上下文。

```python
def build_batch_with_context(kps_by_chapter, current_chapter, config):
    """
    构建带滑动窗口上下文的批次
    """
    # 获取前序章节（按教材顺序）
    prev_chapters = get_previous_chapters(current_chapter)

    # 提取前序章节核心知识点（高频引用、定义类型）
    prev_kps = []
    for chapter in prev_chapters[-2:]:  # 最近2个章节
        chapter_kps = kps_by_chapter[chapter]
        # 按引用频次排序，取前N个
        core_kps = sorted(chapter_kps, key=lambda kp: kp.ref_count)[:config['prev_chapter_kps']]
        prev_kps.extend(core_kps)

    # 当前章节知识点
    current_kps = kps_by_chapter[current_chapter][:config['same_chapter_kps']]

    return {
        'prev_context': prev_kps,
        'current_batch': current_kps
    }
```
核心知识点选取标准（新增）：
选取前序章节核心知识点时，按以下优先级排序：
优先级	条件	说明
①	定义类知识点	如"函数定义"、"方程定义"，是基础概念
②	高频被引用	从定义依赖统计，被多个知识点依赖
③	教材标注"重点"	如有元数据
④	向量相似度（可选）	当前章节核心定义与前序章节知识点计算相似度，取最相关

def select_core_knowledge_points(chapter_kps: list, config: dict) -> list:
    """
    选取核心知识点（按优先级）
    """
    scored_kps = []
    for kp in chapter_kps:
        score = 0
        # 优先级1: 定义类
        if kp.type == "定义":
            score += 100
        # 优先级2: 高频被引用
        score += min(kp.ref_count, 50)  # 上限50
        # 优先级3: 重点标注
        if getattr(kp, 'is_key_point', False):
            score += 30
        scored_kps.append((score, kp))

    # 按分数降序，取前N个
    scored_kps.sort(key=lambda x: x[0], reverse=True)
    return [kp for _, kp in scored_kps[:config['prev_chapter_kps']]]

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§五、前置依赖关系构建方案（多证据融合）（续））
