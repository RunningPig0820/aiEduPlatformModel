# 图谱数据模型与两层结构

> summary: 节点关系模型、URI 命名与小学类扩展
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-textbook-concept-linking-03-图谱数据模型与两层结构.md
> 类别：数据存储

Neo4j 数学知识图谱（设计时基线）：
- Class 概念类 38 个；Concept 知识点 1,275 个；Statement 定义/定理 2,810 个。
- 关系类型：SUB_CLASS_OF（子类）、HAS_TYPE（类型）、RELATED_TO（关联）、PART_OF（部分-整体）、BELONGS_TO（属于）。
- 教材数据：小学数学 12 册、102 章、约 200 知识点；初中 6 册、29 章、约 300 知识点；高中 6 册、21 章、约 100 知识点。

两层结构对齐：既有 EduKG 语义层（Class/Concept/Statement）之上，本次新增的小学知识点通过匹配或新建补充进语义层，保持教材结构层（册/章/知识点）与语义层（Class/Concept/Statement）的衔接。教材知识点经匹配挂接既有 Concept，匹配不到的经人工确认后新建节点并补充关系。

为小学补全规划的新增 Class：
| Class | 父类 | 说明 |
|-------|------|------|
| 小学数概念 | 数学概念 | 数的认识、数数、比大小 |
| 小学运算方法 | 数学方法 | 竖式计算、凑十法、破十法 |
| 小学几何概念 | 几何概念 | 简单图形认识 |

URI 命名规范（新增数据版本）：
- 版本号 0.2，区分 EduKG 的 0.1，表示本团队自行设计的数据。
- ID 格式：`{label_pinyin}-{md5_32bit}`，对 label 字符串计算 MD5，取 32 位小写字符。
- 示例：label "小学数概念" → uri `http://edukg.org/knowledge/0.2/class/math#xiaoxueshugainian-{md5}`。
- 输出文件按 Neo4j 导入格式分开存储：classes.json（Class 定义）、concepts.json（Concept 知识点）、statements.json（Statement 定义）、relations.json（关系 RELATED_TO/PART_OF/BELONGS_TO），避免单文件过大、便于错误定位，可直接复用现有导入脚本。
