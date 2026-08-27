# 前置依赖构建方案（续）
> summary: 前置依赖构建核心原则：教学顺序≠学习依赖，教材顺序存 TEACHES_BEFORE，真正学习依赖存 PREREQUISITE。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-前置依赖构建方案-6.md
> 类别：数据关联

---

### 五、前置依赖关系构建方案（多证据融合）（续）

> 检索摘要：前置依赖构建核心原则：教学顺序≠学习依赖，教材顺序存 TEACHES_BEFORE，真正学习依赖存 PREREQUISITE。

#### 5.5.3 幻觉检测 + JSON 容错（智谱建议）- 支持 JSON 数组格式
> 检索摘要：LLM 输出幻觉检测+JSON容错：解析数组/对象双格式、修复JSON尾逗号、过滤不存在知识点与前置，激进修复作兜底。

import json
import re

def parse_and_validate_llm_response(response: str, valid_kp_names: set) -> dict:
    """
    解析 LLM 响应，验证并过滤幻觉
    支持 JSON 数组格式（新）和对象格式（旧）
    """
    # 1. JSON 格式修复
    # 移除 markdown 代码块标记
    clean = re.sub(r'^```json\s*', '', response)
    clean = re.sub(r'\s*```$', '', clean)
    # 修复尾部逗号
    clean = re.sub(r',\s*}', '}', clean)
    clean = re.sub(r',\s*]', ']', clean)

    # 2. 解析 JSON
    try:
        parsed = json.loads(clean)
    except json.JSONDecodeError as e:
        logging.warning(f"JSON 解析失败: {e}, 尝试修复...")
        parsed = aggressive_json_repair(clean)

    # 3. 格式转换：数组格式 → 对象格式（统一处理）
    if isinstance(parsed, list):
        parsed = {item['target']: item for item in parsed if 'target' in item}

    # 4. 幻觉检测：过滤不存在知识点
    validated = {}
    for kp_name, info in parsed.items():
        # 校验知识点名称
        if kp_name not in valid_kp_names:
            logging.warning(f"幻觉检测: '{kp_name}' 不在合法集合中，丢弃")
            continue

        # 校验前置知识点名称
        valid_prereqs = [p for p in info.get('prerequisites', []) if p in valid_kp_names]
        if len(valid_prereqs) != len(info.get('prerequisites', [])):
            filtered = set(info['prerequisites']) - set(valid_prereqs)
            logging.warning(f"幻觉检测: 前置知识点 {filtered} 不合法，已过滤")

        validated[kp_name] = {
            'prerequisites': valid_prereqs,
            'reason': info.get('reason', ''),
            'confidence': info.get('confidence', 0.0)
        }

    return validated

def aggressive_json_repair(text: str) -> dict:
    """
    激进的 JSON 修复策略
    """
    # 尝试提取最后一个完整 JSON 对象
    # 匹配 {...} 模式
    matches = re.findall(r'\{[^{}]*\}', text)
    if matches:
        # 尝试拼接所有匹配
        combined = '{' + ', '.join(matches) + '}'
        try:
            return json.loads(combined)
        except:
            pass
    # 最终 fallback：返回空对象
    return {}

投票合并算法：
def llm_inference_with_voting(kp_batch):
    """
    两模型投票：至少两个模型输出一致才采纳
    """
    results = []
    for provider in LLM_CONFIG["providers"]:
        llm = LLMFactory.get_llm(scene="prerequisite_inference", provider=provider)
        response = llm.chat(prompt)
        parsed = parse_json(response)
        results.append(parsed)

    # 投票合并
    candidate_relations = {}
    for result in results:
        for target, info in result.items():
            for prereq in info["prerequisites"]:
                key = (prereq, target)
                if key not in candidate_relations:
                    candidate_relations[key] = []
                candidate_relations[key].append({
                    "confidence": info["confidence"],
                    "reason": info["reason"]
                })

    # 最终候选：两模型一致，取平均置信度
    final_candidates = []
    for (from_kp, to_kp), votes in candidate_relations.items():
        if len(votes) >= 2:  # 两模型一致
            avg_conf = sum(v["confidence"] for v in votes) / len(vote)
            final_candidates.append({
                "from": from_kp,
                "to": to_kp,
                "confidence": avg_conf,
                "evidence_types": ["llm_inference"],
                "source": "llm_multi_vote"
            })
    return final_candidates

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§五、前置依赖关系构建方案（多证据融合）（续））
