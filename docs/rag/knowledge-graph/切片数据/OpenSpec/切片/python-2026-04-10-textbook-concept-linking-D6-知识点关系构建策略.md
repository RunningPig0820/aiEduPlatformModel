# D6 知识点关系构建策略
> summary: 用 LLM 推断 Class 类型/Statement 定义/知识点关系，输出 classes/concepts/statements/relations 四文件符合 Neo4j 导入格式，URI 版本 0.2。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/python-2026-04-10-textbook-concept-linking-D6-知识点关系构建策略.md
> 类别：数据关联

> 检索摘要：用 LLM 推断 Class 类型/Statement 定义/知识点关系，输出 classes/concepts/statements/relations 四文件符合 Neo4j 导入格式，URI 版本 0.2。

**决策**: 使用 LLM 推断知识点的关系结构，输出符合 Neo4j 导入格式的独立文件

```
关系构建流程:
1. Class 类型推断: LLM 根据知识点语义推断 HAS_TYPE 关系
   - 凑十法 → 数学方法
   - 20以内加法 → 数学运算
   - 若现有 Class 不匹配，建议新增 Class

2. Statement 定义提取: 为每个知识点生成定义
   - 凑十法的定义: "将一个数拆分成10和另一部分..."
   - 建立 Statement → Concept 的 RELATED_TO 关系

3. 知识点关系提取: LLM 分析知识点之间的关系
   - PART_OF: 20以内加法 → 加法（部分-整体）
   - BELONGS_TO: 凑十法 → 进位加法（所属关系）

4. 输出文件（分开存储，符合Neo4j导入格式）:
   - classes.json: Class 定义
   - concepts.json: Concept 知识点
   - statements.json: Statement 定义
   - relations.json: 关系（RELATED_TO, PART_OF, BELONGS_TO）
```

**理由**:
- EduKG 有完整的关系结构，补充的知识点也需要建立关系
- LLM 可以理解知识点语义，推断正确的关系
- 分开存储避免单文件过大，便于错误定位
- 符合 Neo4j 导入格式，可直接使用现有导入脚本

**URI 命名规范**:
```
版本号: 0.2 (区分 EduKG 的 0.1，表示我们自己设计的数据)
ID格式: {label_pinyin}-{md5_32bit}
MD5: 对 label 字符串计算 MD5，取 32 位小写字符

示例:
- label: "小学数概念"
- uri: "http://edukg.org/knowledge/0.2/class/math#xiaoxueshugainian-{md5}"
```

**可能新增的 Class**:
| Class | 父类 | 说明 |
|-------|------|------|
| 小学数概念 | 数学概念 | 数的认识、数数、比大小 |
| 小学运算方法 | 数学方法 | 竖式计算、凑十法、破十法 |
| 小学几何概念 | 几何概念 | 简单图形认识 |

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-textbook-concept-linking.md`（§D6 知识点关系构建策略）
