# 前置依赖（PREREQUISITE）关系是怎么推断出来的？
> summary: 数据关联引导问题回答：主链路是 LLM 单路径——Neo4j 加载 Concept→±5 邻居配对→双模型投票→≥0.8 落 PREREQUISITE/<0.8 落 CANDIDATE→DAG 无环验证；三来源融合是设计目标未接入主链路
> 权威度: 1.0（合成问答答案切片，非原始证据）
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/引导问题/引导问题-18-数据关联-前置依赖PREREQUISITE关系是怎么.md
> 类别：数据关联

**核心结论**：前置依赖（PREREQUISITE）当前主链路是 LLM 单路径——从 Neo4j 加载 Concept（约 1275+ 个）→ 按 label 排序前后 ±5 邻居配对（约 10×N 对）→ GLM-4-flash + DeepSeek 双模型投票 → 置信度≥0.8 落 PREREQUISITE、<0.8 落 PREREQUISITE_CANDIDATE → validate_dag 无环验证；"三来源融合"是设计目标、未接入主链路。

## 分层展开
- **候选对生成（简化版）**：`generate_kp_pairs` 从 Neo4j 加载 Concept（`MATCH (c:Concept) OPTIONAL MATCH (s:Statement)-[:RELATED_TO]->(c)`），每概念与按 label 排序前后各 5 个配对，约 10×N 个有序对——代码注释自述"应基于启发式规则筛选候选对"（依据：分析-08）。
- **双模型投票**：DualModelVoter 并行调 GLM-4-flash + DeepSeek；两模型 decision 一致→采纳取均值；不一致→加权 DS=0.6/GLM=0.4/阈值 0.5，仅 DeepSeek=True 可过线（DS 一票否决），置信度=胜者×0.7（依据：分析-08 / 完善文档 06）。
- **分类阈值**：`_infer_pair` 用 confidence≥0.8 判定 PREREQUISITE，否则 PREREQUISITE_CANDIDATE；主链路实际只有 0.8 一个分界，CONFIDENCE_THRESHOLD_LOW=0.6 只在未调用的 vote_prerequisite() 里（依据：分析-08 / 完善文档 06）。
- **DAG 无环验证**：validate_dag.py 只把 PREREQUISITE 与 CANDIDATE 建图，DFS `detect_cycles` 找环，有环退出码 1；输出覆盖率/平均链长/置信度分布（依据：分析-08 / 完善文档 06）。
- **口径提醒（最大翻转）**：三来源融合 `fuse_results` 方法完整实现（去重/定义依赖升级 0.9/LLM 重合升级 min(已有+0.1,1.0)/source=multi_evidence）但主链路未接入；CLI 只产 llm_prereq.json，final_prereq.json 无生产方，直接跑 validate_dag.py 会 FileNotFoundError（依据：分析-08 / 完善文档 06）。
- **其他未落地**：年级倒置惩罚代码中不存在；断点续传 --resume 未落地（infer_prerequisites.py 无 resume 参数）（依据：分析-08 / 完善文档 06）。

## 追问防御
- **可能追问：为什么不直接融合三来源？** → 融合是语雀 D9 的**设计目标非落地现状**——fuse_results 存在但未挂 CLI 主流程，infer_prerequisites.py 只调 infer_batch→save_results；当前是 LLM 单路径 + 0.8 单阈值，面试要如实讲（依据：完善文档 06 / 分析-08）。
- **可能追问：置信度低怎么办？** → 两级置信产出兜底：<0.8 不丢弃，落 PREREQUISITE_CANDIDATE 保留待人工补审；投票不一致不采纳（但加权路径 DS=True 可一票通过，置信×0.7 打折）（依据：完善文档 06）。
- **可能追问：成本可控吗？** → GLM-4-flash 免费主力 + DeepSeek 兜底，1295 概念全推断成本估算 <0.01 元；但 generate_kp_pairs 实际产 ~10N 对，estimate_inference_cost 按 2N 估算偏低约 5 倍（依据：分析-08）。

> 证据：详见 `4.完善文档/06-前置依赖与学习路径.md` ｜ `3.代码/分析-08-前置依赖推断.md` ｜ `5.难点/坑档案.md（J-KG6）`
