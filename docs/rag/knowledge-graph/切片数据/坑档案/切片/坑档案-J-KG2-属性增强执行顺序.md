# 坑档案-J-KG2-属性增强执行顺序
> summary: 属性增强执行顺序 bug：增强跑在 LLM 推断前，属性覆盖率仅 22%
> 来源: 坑档案 ｜ 锚点: J-KG2 ｜ 节: 5.难点/坑档案.md
> COS路径: rag-slices/knowledge-graph/坑档案/坑档案-J-KG2-属性增强执行顺序.md
> 类别：开发难点
> target: 开发对账

---

**1. 问题现象**：`textbook_kps.json` 里 1350 个知识点，只有 299 个带 difficulty/importance/cognitive_level/topic 属性，覆盖率 22%——大量知识点在教学属性面板上显示为"默认值/缺失"。

**2. 触发流程**：管道按顺序执行：① `enhance_kp_attributes.py` 对现有 299 个知识点做属性增强 → ② `infer_textbook_kp.py` 用 LLM 推断出 1052 个缺失知识点 → ③ `merge_inferred_kps.py` 合并成 1350 个。问题在于属性增强只跑在①，②新增的知识点从没经过属性增强。

**3. 根因分析**：**执行顺序错误**——`problems_and_solutions.md` §十一记录时间线：`12:10 属性增强(enhance_kp_attributes.py)仅处理原有299个 → 13:47 LLM推断(infer_textbook_kp.py)新增1052个 → 14:45 合并(merge_inferred_kps.py)共1350个`。属性增强作为独立步骤先跑，天然覆盖不到后生成的推断知识点；`KPAttributeInferer.infer_batch`（`kp_attribute_inferer.py:280-345`）只遍历入参 kps，不会自愈补跑。

**4. 排查过程**：属性分布报告 `kp_attributes_distribution.json` 与知识点总数对不上——总数 1350、增强文件只有 299 条；核对时间线发现 enhance 与 infer 的先后关系反了。

**5. 解决方案 & 改动点**：对全部 1350 个知识点**重新跑属性增强并强制覆盖**：`python enhance_kp_attributes.py --enhance --force`（`edukg/scripts/kg_data/textbook/enhance_kp_attributes.py:15` 定义 `--force`、`:100-122` `enhance_kps` 强制重建 `textbook_kps_enhanced.json`）→ `--merge`（`:125-149` 合并回主文件）。属性推断是纯规则（无 LLM），重跑成本低。修复提交：`03f3f75 [知识图谱]-[教学知识点和知识点推断]`（problems 文档 §十一记录）；`5cf7f62 [知识图谱]-[教材知识点导入]` 里 enhance 脚本参数化收口。

**6. 面试口述要点**：管道化数据加工最典型的坑是**步骤依赖顺序被隐式假设**——增强依赖"所有知识点已生成"，但生成被拆成"先规则后 LLM 两批"，顺序写错就漏一批。教训：规则类步骤设计成可 `--force` 幂等重跑，发现覆盖率不对能低成本补；同时要把"步骤间前置关系"显式写进 README/编排脚本，而不是靠人脑记。
