# 分学科处理策略（续）
> summary: 学科分三类：强逻辑链学科(数理化生)建 PREREQUISITE，语言学科(英语)建语法词汇层级，主题关联学科(历史语文地理政治)建主题分类。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-分学科处理策略-3.md
> 类别：数据关联

---

### 八、分学科处理策略（学科类型划分）（续）

> 检索摘要：学科分三类：强逻辑链学科(数理化生)建 PREREQUISITE，语言学科(英语)建语法词汇层级，主题关联学科(历史语文地理政治)建主题分类。

#### 8.4.3 主题关联学科（历史/语文/地理/政治）
> 检索摘要：THEME 关系用于主题聚类与推荐而非学习依赖，按历史/语文/地理主题表匹配知识点生成主题关联。

THEME 关系：用于主题聚类和推荐，非学习依赖。
def build_theme_relations(knowledge_points: list, subject: str) -> list:
    """
    构建主题关联关系
    """
    # 历史主题
    HISTORY_THEMES = {
        "中国近代史": ["鸦片战争", "太平天国", "洋务运动", "甲午战争", "戊戌变法"],
        "世界近代史": ["文艺复兴", "宗教改革", "启蒙运动", "工业革命"],
        "中国古代史": ["秦朝", "汉朝", "唐朝", "宋朝", "明朝", "清朝"],
    }

    # 语文主题
    CHINESE_THEMES = {
        "唐诗": ["李白", "杜甫", "白居易", "王维"],
        "宋词": ["苏轼", "辛弃疾", "李清照", "柳永"],
        "古文运动": ["韩愈", "柳宗元", "欧阳修"],
    }

    # 地理主题
    GEOGRAPHY_THEMES = {
        "中国地理": ["地形", "气候", "河流", "资源"],
        "世界地理": ["亚洲", "欧洲", "非洲", "美洲"],
    }

    themes_map = {
        "history": HISTORY_THEMES,
        "chinese": CHINESE_THEMES,
        "geography": GEOGRAPHY_THEMES,
    }

    themes = themes_map.get(subject, {})
    relations = []

    for kp in knowledge_points:
        for theme_name, theme_kps in themes.items():
            if kp.name in theme_kps:
                relations.append({
                    'from': kp.uri,
                    'to': theme_name,
                    'relation_type': 'THEME',
                    'source': 'rule_based'
                })

    return relations

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§八、分学科处理策略（学科类型划分）（续））
