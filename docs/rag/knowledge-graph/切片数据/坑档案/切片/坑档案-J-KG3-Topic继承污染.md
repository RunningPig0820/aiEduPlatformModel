# 坑档案-J-KG3-Topic继承污染
> summary: Topic 继承污染：知识点 topic 直接继承章节，导致"加法"被标成"图形与几何"
> 来源: 坑档案 ｜ 锚点: J-KG3 ｜ 节: 5.难点/坑档案.md
> COS路径: rag-slices/knowledge-graph/坑档案/坑档案-J-KG3-Topic继承污染.md
> 类别：开发难点
> target: 开发对账

---

**1. 问题现象**：图谱知识点的专题（topic）字段出现语义矛盾——"加法""连加连减"这类数与代数知识点被标成"图形与几何"；"三角形定义"被标成"数与代数"。专题筛选举报错数据。

**2. 触发流程**：章节增强器 `enhance_chapters.py` 按章节名规则分配 topic（"位置"章 → 图形与几何，见 `chapter_enhancer.py:96` "位置与方向"/"位置"关键词）→ 属性推断器 `kp_attribute_inferer.py` 给知识点加 topic 时**直接继承章节 topic** → 落在"位置"章下的"加法"知识点继承到"图形与几何"。

**3. 根因分析**：`kp_attribute_inferer.py:265-267`：`topic = section_topic if section_topic else "其他"`，`topic_source = f"chapter_topic:{topic}"`——知识点专题无脑抄章节专题。章节专题是按章节名关键词规则猜的（`chapter_enhancer.assign_topic`），猜错章节 → 全章知识点 topic 集体错。`problems_and_solutions.md` §五记录："'加法'应属于'数与代数'，不应继承'图形与几何'"。

**4. 排查过程**：抽样知识点看 `topic_source` 全是 `chapter_topic:...`，锁定继承逻辑；对照章节名"位置"被 `chapter_enhancer.MATH_TOPICS["图形与几何"]` 命中（"位置"关键词），确认是章节规则猜错被知识点了继承放大。

**5. 解决方案 & 改动点**：`problems_and_solutions.md` §五/§十六记录：**基于匹配的 EduKG Concept 的 Class 类型修正 topic**（`TOPIC_CLASS_MAP` 规则：数学概念/数学运算→数与代数、几何图形/几何性质→图形与几何、统计概念→统计与概率），匹配 TextbookKP→Concept 后查 Class 再覆盖 topic，数据上修正 144 个（数与代数 855→891、图形与几何 359→315）。提交 `03f3f75` 记录了该修正方案与结果统计。**注意（现状口径）**：当前 `kp_attribute_inferer.py:265-267` 默认仍是章节 topic 继承，Class 修正是按批次对数据做的一次性修正，未固化进属性推断代码——重新跑属性增强会退回章节继承。这本身是"数据级修正未落到代码"的教训。

**6. 面试口述要点**：派生属性不能无脑继承父级——"继承"把父节点的规则误差**批量放大**到所有子节点。修正要回到"语义权威源"：知识点真正的专题应由它匹配到的图谱概念类别决定，而不是它所在的章节名。另一个收获：**一次性数据修正不可靠，修完要么回写生成脚本、要么让生成逻辑幂等吸收修正**，否则数据一重跑就打回原形。
