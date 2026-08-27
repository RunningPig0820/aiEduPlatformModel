# 坑档案-J-KG4-小学高中知识点缺失LLM补全
> summary: 小学/高中知识点缺失：原始教材 JSON 知识点字段为空，靠 LLM 双模型推断补 1052 个
> 来源: 坑档案 ｜ 锚点: J-KG4 ｜ 节: 5.难点/坑档案.md
> COS路径: rag-slices/knowledge-graph/坑档案/坑档案-J-KG4-小学高中知识点缺失LLM补全.md
> 类别：开发难点
> target: 开发对账

---

**1. 问题现象**：教材目录 JSON 里小学 3-6 年级 `knowledge_points` 全空、高中必修也仅有"综合测试"标记，只有初中 7-9 年级 252 个较完整——教材图谱小学/高中学段"没有知识点可挂"。

**2. 触发流程**：`generate_textbook_data.py` 解析人教版教材 JSON 生成 sections → 发现小学 1-6 与高中大量小节 `existing_kps` 为空 → `infer_textbook_kp.py` 分析出 295 个缺失章节 → 逐章节调 LLM 推断。

**3. 根因分析**：**上游教材数据源不完整**（人教版教材 JSON 未标注知识点，小学/高中尤其缺）。`problems_and_solutions.md` §一统计：小学 1-2 年级 47 个、小学 3-6 年级 0 个、初中 252 个、高中必修 0 个。不是解析 bug，是源数据本身没有知识点列。

**4. 排查过程**：`infer_textbook_kp.py --dry-run` 输出 `missing_sections` 按学段统计，确认小学/高中整片缺失、初中完整——排除解析逻辑问题，定位到源数据。

**5. 解决方案 & 改动点**：用**双模型投票 LLM 推断**补全：`edukg/scripts/kg_data/textbook/infer_textbook_kp.py:157-164`（`analyze_missing_kps` 判定小学 1-6 与高中 `need_infer = len(existing_kps)==0`）→ `edukg/core/llm_inference/textbook_kp_inferer.py`（`infer_batch`，GLM+DeepSeek 两模型都输出才采纳，取主模型结果，见 `dual_model_voter.py:288-316`）。结果：缺失 295 章节 → 推断 1052 知识点，平均置信度 0.93；`merge_inferred_kps.py` 合并回主文件并重生成 IN_UNIT 关系。提交：`64a77e1 [知识图谱]-[小学知识点生成]`、`9885742 [知识图谱]-[小学知识点推理]`、`9ec9644 [知识图谱]-[小学知识点整理]`。

**6. 面试口述要点**：遇到"数据缺一半"先分层定位——是解析丢了、还是源数据就没有（本项目是后者）。LLM 补数据要用**双模型投票**降低幻觉（两模型一致才采纳），并给每条带 confidence 供下游过滤。推断类任务天然要接断点续传（见 J-KG8），否则 2-3 小时任务中断全废。
