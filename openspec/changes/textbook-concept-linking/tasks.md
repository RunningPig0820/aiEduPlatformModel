## 开发流程说明

**重要：分阶段开发，每个阶段完成后需验证再继续下一阶段**

```
阶段1 → 运行测试 → 人工确认 → 阶段2 → 运行测试 → 人工确认 → ...
```

每个阶段完成后：
1. 运行该阶段的测试用例 `pytest tests/curriculum/test_xxx.py -v`
2. 确认测试通过后，通知人工启动下一阶段
3. 如有失败，修复问题后重新测试

---

## Part 1: 课标知识点提取（先补全知识点）

> **为什么先做课标提取？**
> - EduKG 缺少小学知识点（93%匹配失败）
> - 先从课标提取知识点，补全 Neo4j Concept
> - 再做教材知识点匹配，匹配率会更高

### 1. 项目结构初始化（阶段1）✅ 已完成

- [x] 1.1 创建 `edukg/core/curriculum/` 目录结构
- [x] 1.2 创建测试目录 `tests/curriculum/`
- [x] 1.3 配置百度 OCR API Key 环境变量 (BAIDU_OCR_API_KEY, BAIDU_OCR_SECRET_KEY)
- [x] 1.4 配置智谱 API Key 环境变量（ZHIPU_API_KEY）
- [x] 1.5 配置 Neo4j 环境变量（NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD）

---

### 2. PDF OCR 服务（阶段2）✅ 已完成

**目标**: 使用百度 OCR API 识别课标 PDF（收费服务）

- [x] 2.1 实现 `BaiduOCRService` 类，初始化百度 OCR API 客户端
- [x] 2.2 实现 `extract_text()` 调用百度 OCR API 提取文字
- [x] 2.3 实现 PDF 转图片 + OCR 识别流程
- [x] 2.4 实现 `save_ocr_result()` 保存 OCR 结果到 JSON
- [x] 2.5 处理 API 调用限制（QPS、错误重试、成本控制）
- [x] 2.6 完成 189页 PDF 的 OCR 识别

**输出**: `edukg/data/eduBureau/math/ocr_result.json`

---

### 3. 知识点提取服务（阶段3）✅ 已完成

**目标**: 使用 LLM 从课标文本提取结构化知识点

> **LLM使用**: glm-4-flash（免费），从OCR文本中识别结构化知识点

- [x] 3.1 实现 `LLMExtractor` 类，配置 ChatZhipuAI (glm-4-flash，免费)
- [x] 3.2 设计结构化 prompt，要求 JSON 输出
- [x] 3.3 实现 `extract_knowledge_points()` 提取学段、领域、知识点
- [x] 3.4 实现文本分块处理（超长文本切分）
- [x] 3.5 实现 JSON schema 验证
- [x] 3.6 保存提取结果到 `curriculum_kps.json`

**输出**: `edukg/data/output/curriculum_kps.json`（中间文件）

---

### 4. 知识图谱构建服务（阶段4）⭐ 核心阶段

**目标**: 为提取的知识点构建完整的知识图谱结构，输出符合 Neo4j 导入格式的 JSON 文件

> **LLM使用**: 需要LLM进行语义理解和推断
> - 类型判断（HAS_TYPE）：LLM推断知识点属于哪个Class
> - Statement定义：LLM生成知识点的定义描述
> - 关系提取：LLM分析知识点之间的关系

> **URI 命名规范**:
> - 版本号: `0.2` (区分 EduKG 的 0.1，表示我们自己设计的数据)
> - ID 格式: `{label_pinyin}-{md5_32bit}`
> - MD5生成: `hashlib.md5(label.encode("utf-8")).hexdigest()`
> - 示例: `http://edukg.org/knowledge/0.2/class/math#xiaoxueshugainian-{md5}`

> **数据格式参考**:
> - Class: `edukg/data/edukg/math/1_概念类(Class)/math_classes.json`
> - Entity: `edukg/data/edukg/math/8_全部关联关系(Complete)/math_entities_complete.json`
> - Relation: `edukg/data/edukg/math/8_全部关联关系(Complete)/math_knowledge_relations.json`

> **输入文件**: `edukg/data/eduBureau/math/ocr_result.json`

#### 4.1 基础设施

- [x] 4.1.1 实现 `KGBuilder` 类，知识图谱构建主服务
- [x] 4.1.2 实现 `URIGenerator` 类，生成符合规范的 URI
  - 版本号: 0.2
  - ID生成: `{pinyin(label)}-{md5(label)}`
  - 支持三种类型: class, instance, statement

#### 4.2 Class 提取（使用LLM判断类型）

- [x] 4.2.1 实现 `ClassExtractor` 类
- [x] 4.2.2 实现 LLM 推断知识点类型
  - 现有38个Class的列表作为上下文
  - LLM判断每个知识点应属于哪个Class
  - 若无匹配Class，建议新增Class（如"小学数概念"）
- [x] 4.2.3 生成 classes.json（格式符合Neo4j导入）

**输出**: `edukg/data/eduBureau/math/classes.json`

#### 4.3 Concept 提取

- [x] 4.3.1 实现 `ConceptExtractor` 类
- [x] 4.3.2 从知识点列表生成 Concept 实体
- [x] 4.3.3 添加 HAS_TYPE 关系（关联到Class）
- [x] 4.3.4 生成 concepts.json（格式符合Neo4j导入）

**输出**: `edukg/data/eduBureau/math/concepts.json`

#### 4.4 Statement 提取（使用LLM生成定义）

- [x] 4.4.1 实现 `StatementExtractor` 类
- [x] 4.4.2 实现 LLM 生成知识点定义
  - 基于课标文本生成准确的定义
  - 添加 content 字段存储定义内容
- [x] 4.4.3 生成 statements.json（格式符合Neo4j导入）

**输出**: `edukg/data/eduBureau/math/statements.json`

#### 4.5 关系提取（使用LLM分析关系）

- [x] 4.5.1 实现 `RelationExtractor` 类
- [x] 4.5.2 实现 LLM 分析知识点关系
  - RELATED_TO: Statement → Concept
  - PART_OF: Concept → Concept（部分-整体）
  - BELONGS_TO: Concept → Concept（所属关系）
- [x] 4.5.3 生成 relations.json（格式符合Neo4j导入）

**输出**: `edukg/data/eduBureau/math/relations.json`

**阶段4完成验证**:
```bash
# 运行知识图谱构建测试
pytest tests/curriculum/test_kg_builder.py -v

# 手动验证：生成知识图谱结构
python -m edukg.core.curriculum.kg_builder --ocr-result edukg/data/eduBureau/math/ocr_result.json --debug

# 确认生成4个JSON文件
ls -la edukg/data/eduBureau/math/
# classes.json, concepts.json, statements.json, relations.json
```

---

### 5. 知识点对比服务（阶段5）✅ 已完成

**目标**: 对比课标知识点与 EduKG Concept

- [x] 5.1 实现 `ConceptComparator` 类，连接 Neo4j（只读）
- [x] 5.2 实现 `query_existing_concepts()` 查询所有 Concept label
- [x] 5.3 实现 `compare_knowledge_points()` 对比匹配状态
- [x] 5.4 实现 `generate_comparison_report()` 生成对比报告
- [x] 5.5 保存报告到 `kp_comparison_report.json`

**输出**: `edukg/data/output/kp_comparison_report.json`

---

### 里程碑：人工导入 Neo4j

完成阶段4后，使用现有导入脚本将知识图谱数据导入Neo4j：

```bash
# 使用现有导入脚本
python edukg/scripts/kg_data/import_kg.py \
  --classes edukg/data/eduBureau/math/classes.json \
  --concepts edukg/data/eduBureau/math/concepts.json \
  --statements edukg/data/eduBureau/math/statements.json \
  --relations edukg/data/eduBureau/math/relations.json
```

---

## Part 2: 教材知识点匹配（补全后匹配更准确）

> **前提**: Part 1 完成后，Neo4j 已包含小学知识点（人工导入后）
> 此时教材匹配率会大幅提升

### 6. 教材解析服务（阶段6）

**目标**: 解析教材 JSON 文件，生成章节结构

- [ ] 6.1 创建 `edukg/core/textbook/` 目录结构
- [ ] 6.2 创建测试目录 `tests/textbook/`
- [ ] 6.3 实现 `TextbookParser` 类，解析教材 JSON 文件
- [ ] 6.4 实现 `parse_chapter()` 解析单个章节结构
- [ ] 6.5 保存解析结果到 `textbook_chapters.json`

**输出**: `edukg/data/output/textbook_chapters.json`

---

### 7. 知识点匹配服务（阶段7）

**目标**: 匹配教材知识点与 Neo4j Concept（补全后匹配率更高）

> **LLM使用**: 模糊匹配时使用LLM进行语义匹配

- [ ] 7.1 实现 `ConceptMatcher` 类，连接 Neo4j（只读）
- [ ] 7.2 实现 `query_all_concepts()` 查询所有 Concept label
- [ ] 7.3 实现 `exact_match()` 精确匹配（label 完全相同）
- [ ] 7.4 实现 `fuzzy_match()` 模糊匹配（LLM 语义匹配）
- [ ] 7.5 实现 `generate_matching_report()` 输出匹配报告
- [ ] 7.6 保存报告到 `matching_report.json`

**输出**: `edukg/data/output/matching_report.json`

---

## Part 3: 整合与文档

### 8. 主脚本整合（阶段8）

**目标**: 整合所有服务，提供命令行接口

- [ ] 8.1 创建 `edukg/core/curriculum/main.py` 整合课标模块
- [ ] 8.2 创建 `edukg/core/textbook/main.py` 整合教材模块
- [ ] 8.3 实现命令行参数（--skip-ocr, --debug）
- [ ] 8.4 实现错误处理和日志记录
- [ ] 8.5 验证完整流程

---

### 9. 文档（阶段9）

- [ ] 9.1 编写 README.md 记录使用方法
- [ ] 9.2 记录输出文件格式说明
- [ ] 9.3 验证数据质量

---

## 任务统计

| 阶段 | 任务数量 | 说明 | 状态 |
|------|----------|------|------|
| 阶段1 | 5 | 项目结构初始化 | ✅ 完成 |
| 阶段2 | 6 | PDF OCR 服务 | ✅ 完成 |
| 阶段3 | 6 | 知识点提取服务 | ✅ 完成 |
| **阶段4** | **13** | **知识图谱构建服务（核心）** | **待实现** |
| 阶段5 | 5 | 知识点对比服务 | ✅ 完成 |
| **里程碑** | - | **人工导入 Neo4j** | - |
| 阶段6 | 5 | 教材解析服务 | 待实现 |
| 阶段7 | 6 | 知识点匹配服务 | 待实现 |
| 阶段8 | 5 | 主脚本整合 | 待实现 |
| 阶段9 | 3 | 文档 | 待实现 |
| **总计** | **54** | | |

---

## LLM 使用说明

| 任务 | 是否需要LLM | LLM作用 | 模型 |
|------|-------------|---------|------|
| 知识点提取（阶段3）| ✅ 需要 | 从OCR文本中识别结构化知识点 | glm-4-flash |
| 类型判断（阶段4.2）| ✅ 需要 | 推断知识点属于哪个Class | glm-4-flash |
| Statement定义（阶段4.4）| ✅ 需要 | 生成知识点的定义描述 | glm-4-flash |
| 关系提取（阶段4.5）| ✅ 需要 | 分析知识点之间的关系 | glm-4-flash |
| 模糊匹配（阶段7）| ✅ 需要 | 语义匹配教材知识点 | glm-4-flash |

**成本说明**: glm-4-flash 是免费模型，无需担心API费用

---

## 输出文件说明

### Part 1 输出（课标知识点提取）

| 文件 | 阶段 | 说明 |
|------|------|------|
| `edukg/data/eduBureau/math/ocr_result.json` | 阶段2 | OCR 识别结果 |
| `edukg/data/eduBureau/math/classes.json` | 阶段4 | Class 定义（Neo4j格式） |
| `edukg/data/eduBureau/math/concepts.json` | 阶段4 | Concept 知识点（Neo4j格式） |
| `edukg/data/eduBureau/math/statements.json` | 阶段4 | Statement 定义（Neo4j格式） |
| `edukg/data/eduBureau/math/relations.json` | 阶段4 | 关系（Neo4j格式） |
| `edukg/data/output/curriculum_kps.json` | 阶段3 | 课标知识点（中间文件） |
| `edukg/data/output/kp_comparison_report.json` | 阶段5 | 对比报告 |

### Part 2 输出（教材知识点匹配）

| 文件 | 阶段 | 说明 |
|------|------|------|
| `edukg/data/output/textbook_chapters.json` | 阶段6 | 教材章节结构 |
| `edukg/data/output/matching_report.json` | 阶段7 | 匹配报告 |

---

## URI 命名规范

```
URI 格式: http://edukg.org/knowledge/{version}/{type}/math#{id}

┌─────────────────────────────────────────────────────────────────┐
│ version: 0.2 (我们自己设计的数据，区分 EduKG 的 0.1)              │
│ type: class | instance | statement                              │
│ id: {label_pinyin}-{md5(label)}                                  │
│                                                                  │
│ MD5生成代码:                                                      │
│ import hashlib                                                   │
│ md5_str = hashlib.md5(label.encode("utf-8")).hexdigest()         │
└─────────────────────────────────────────────────────────────────┘

示例:
- label: "小学数概念"
- pinyin: "xiaoxueshugainian"
- md5: hashlib.md5("小学数概念".encode("utf-8")).hexdigest()
- uri: "http://edukg.org/knowledge/0.2/class/math#xiaoxueshugainian-{md5}"
```

---

## JSON 格式规范

### classes.json
```json
{
  "subject": "math",
  "subject_name": "数学",
  "class_count": 5,
  "classes": [
    {
      "uri": "http://edukg.org/knowledge/0.2/class/math#xiaoxueshugainian-{md5}",
      "id": "xiaoxueshugainian-{md5}",
      "subject": "math",
      "label": "小学数概念",
      "description": "小学数概念",
      "parents": ["http://edukg.org/knowledge/0.1/class/math#shuxuegainian-{md5}"],
      "type": "owl:Class"
    }
  ]
}
```

### concepts.json
```json
[
  {
    "uri": "http://edukg.org/knowledge/0.2/instance/math#coutishufa-{md5}",
    "label": "凑十法",
    "types": ["shuxuefangfa-{md5}"]
  }
]
```

### statements.json
```json
[
  {
    "uri": "http://edukg.org/knowledge/0.2/statement/math#coutishufa-dingyi-{md5}",
    "label": "凑十法的定义",
    "types": ["shuxuedingyi-{md5}"],
    "content": "凑十法是一种计算方法，将一个数拆分成10和另一部分..."
  }
]
```

### relations.json
```json
{
  "metadata": {
    "total_relations": 100,
    "description": "小学数学知识点关联关系"
  },
  "relations": [
    {
      "from": {"uri": "...", "label": "凑十法的定义"},
      "relation": "relatedTo",
      "to": {"uri": "...", "label": "凑十法"}
    }
  ]
}
```

---

## 目录结构

```
edukg/core/
├── curriculum/                   # 课标模块
│   ├── __init__.py
│   ├── pdf_ocr.py               # 百度 OCR（收费）
│   ├── kp_extraction.py         # LLM 提取（免费）
│   ├── kg_builder.py            # 知识图谱构建（核心）
│   ├── kp_comparison.py         # 对比分析
│   └── main.py                  # 主脚本
│
└── textbook/                     # 教材模块
    ├── __init__.py
    ├── parser.py                # 解析教材 JSON
    ├── matcher.py               # 匹配知识点
    └── main.py                  # 主脚本

tests/
├── curriculum/
│   ├── test_pdf_ocr.py
│   ├── test_kp_extraction.py
│   ├── test_kg_builder.py       # 知识图谱构建测试
│   ├── test_kp_comparison.py
│   └── test_main.py
│
└── textbook/
    ├── test_parser.py
    ├── test_matcher.py
    └── test_main.py
```