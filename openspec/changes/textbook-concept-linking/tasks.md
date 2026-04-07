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

### 1. 项目结构初始化（阶段1）

- [x] 1.1 创建 `edukg/core/curriculum/` 目录结构
- [x] 1.2 创建测试目录 `tests/curriculum/`
- [x] 1.3 配置百度 OCR API Key 环境变量 (BAIDU_OCR_API_KEY, BAIDU_OCR_SECRET_KEY)
- [x] 1.4 配置智谱 API Key 环境变量（ZHIPU_API_KEY）
- [x] 1.5 配置 Neo4j 环境变量（NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD）

**阶段1完成验证**:
```bash
# 确认目录结构存在
ls -la edukg/core/curriculum/
ls -la tests/curriculum/

# 确认环境变量配置正确
python -c "import os; print('BAIDU_OCR_API_KEY:', os.environ.get('BAIDU_OCR_API_KEY', 'NOT SET'))"
python -c "import os; print('ZHIPU_API_KEY:', os.environ.get('ZHIPU_API_KEY', 'NOT SET'))"
python -c "import os; print('NEO4J_URI:', os.environ.get('NEO4J_URI', 'NOT SET'))"
```

---

### 2. PDF OCR 服务（阶段2）

**目标**: 使用百度 OCR API 识别课标 PDF（收费服务）

> **注意**: 百度 OCR 是收费服务，按次计费，建议控制调用次数

- [x] 2.1 实现 `BaiduOCRService` 类，初始化百度 OCR API 客户端
- [x] 2.2 实现 `extract_text()` 调用百度 OCR API 提取文字
- [x] 2.3 实现 PDF 转图片 + OCR 识别流程
- [x] 2.4 实现 `save_ocr_result()` 保存 OCR 结果到 JSON
- [x] 2.5 处理 API 调用限制（QPS、错误重试、成本控制）
- [ ] 2.6 完成 edukg/data/eduBureau/math/义务教育数学课程标准（2022年版5月9日）.pdf 的 OCR 识别

**阶段2完成验证**:
```bash
# 运行 OCR 测试
pytest tests/curriculum/test_pdf_ocr.py -v

# 手动验证：处理小 PDF 文件
python -m edukg.core.curriculum.pdf_ocr --pdf-path test.pdf --debug
# 确认生成 ocr_result.json
```

---

### 3. 知识点提取服务（阶段3）

**目标**: 使用 LLM 从课标文本提取结构化知识点

- [x] 3.1 实现 `LLMExtractor` 类，配置 ChatZhipuAI (glm-4-flash，免费)
- [x] 3.2 设计结构化 prompt，要求 JSON 输出
- [x] 3.3 实现 `extract_knowledge_points()` 提取学段、领域、知识点
- [x] 3.4 实现文本分块处理（超长文本切分）
- [x] 3.5 实现 JSON schema 验证
- [x] 3.6 保存提取结果到 `curriculum_kps.json`

**阶段3完成验证**:
```bash
# 运行 LLM 提取测试
pytest tests/curriculum/test_kp_extraction.py -v

# 手动验证：使用阶段2的 OCR 结果
python -m edukg.core.curriculum.kp_extraction --ocr-result ocr_result.json --debug
# 确认生成 curriculum_kps.json
```

---

### 3.5 知识点关系构建（阶段3.5）

**目标**: 为提取的知识点构建完整的知识图谱关系结构

> **背景**: EduKG 知识图谱包含5种关系，补充的小学知识点也需要建立这些关系
> - SUB_CLASS_OF: Class 层级关系
> - HAS_TYPE: Concept → Class 类型分类
> - RELATED_TO: Statement → Concept 定义关联
> - PART_OF: Concept → Concept 部分-整体关系
> - BELONGS_TO: Concept → Concept 所属关系

- [ ] 3.5.1 实现 `RelationBuilder` 类，分析知识点关系
- [ ] 3.5.2 实现LLM推断 Class 类型（HAS_TYPE）
  - 根据知识点语义推断应属于哪个 Class（如"凑十法"→"数学方法"）
  - 若现有 Class 不匹配，建议新增 Class（如"小学数概念"）
- [ ] 3.5.3 实现知识点定义提取（Statement）
  - 为每个知识点生成定义/描述
  - 建立 Statement → Concept 的 RELATED_TO 关系
- [ ] 3.5.4 实现知识点关系提取（PART_OF, BELONGS_TO）
  - LLM 分析知识点之间的层级关系
  - 如"20以内加法" PART_OF "加法"
  - 如"凑十法" BELONGS_TO "进位加法"
- [ ] 3.5.5 保存关系结构到 `kp_relations.json`

**阶段3.5完成验证**:
```bash
# 运行关系构建测试
pytest tests/curriculum/test_relation_builder.py -v

# 手动验证：生成关系结构
python -m edukg.core.curriculum.relation_builder --kps curriculum_kps.json --debug
# 确认生成 kp_relations.json

# 查看关系结构示例
cat edukg/data/output/kp_relations.json | head -50
```

---

### 4. 知识点对比服务（阶段4）

**目标**: 对比课标知识点与 EduKG Concept

- [x] 4.1 实现 `ConceptComparator` 类，连接 Neo4j（只读）
- [x] 4.2 实现 `query_existing_concepts()` 查询所有 Concept label
- [x] 4.3 实现 `compare_knowledge_points()` 对比匹配状态
- [x] 4.4 实现 `generate_comparison_report()` 生成对比报告
- [x] 4.5 保存报告到 `kp_comparison_report.json`

**阶段4完成验证**:
```bash
# 运行对比测试
pytest tests/curriculum/test_kp_comparison.py -v

# 手动验证：使用阶段3的提取结果
python -m edukg.core.curriculum.kp_comparison --kps curriculum_kps.json --debug
# 确认生成 kp_comparison_report.json
```

---

### 5. TTL 生成服务（阶段5）

**目标**: 生成 TTL 格式文件，包含完整的关系结构

- [x] 5.1 实现 `TTLGenerator` 类
- [x] 5.2 定义 namespace 和 prefix
- [x] 5.3 实现 `generate_ttl()` 创建 TTL triples
- [ ] 5.4 实现 `generate_relations_ttl()` 生成关系三元组
  - HAS_TYPE: Concept → Class
  - RELATED_TO: Statement → Concept
  - PART_OF: Concept → Concept
  - BELONGS_TO: Concept → Concept
- [ ] 5.5 实现 `generate_class_ttl()` 生成新增 Class 定义
- [x] 5.6 保存 TTL 到 `curriculum_kps.ttl`

**阶段5完成验证**:
```bash
# 运行 TTL 测试
pytest tests/curriculum/test_ttl_generator.py -v

# 手动验证：生成 TTL
python -m edukg.core.curriculum.ttl_generator --kps curriculum_kps.json --relations kp_relations.json --debug
# 确认生成 curriculum_kps.ttl

# 验证 TTL 包含关系结构
grep "HAS_TYPE" curriculum_kps.ttl
grep "RELATED_TO" curriculum_kps.ttl
grep "PART_OF" curriculum_kps.ttl
grep "BELONGS_TO" curriculum_kps.ttl

# 人工确认后，手动导入 Neo4j
# (使用现有导入脚本或 Neo4j 浏览器)
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

**阶段6完成验证**:
```bash
# 运行解析测试
pytest tests/textbook/test_parser.py -v

# 手动验证：解析教材 JSON
python -m edukg.core.textbook.parser --input edukg/data/renjiao/math.json --debug
# 确认生成 textbook_chapters.json
```

---

### 7. 知识点匹配服务（阶段7）

**目标**: 匹配教材知识点与 Neo4j Concept（补全后匹配率更高）

- [ ] 7.1 实现 `ConceptMatcher` 类，连接 Neo4j（只读）
- [ ] 7.2 实现 `query_all_concepts()` 查询所有 Concept label
- [ ] 7.3 实现 `exact_match()` 精确匹配（label 完全相同）
- [ ] 7.4 实现 `fuzzy_match()` 模糊匹配（LLM 语义匹配）
- [ ] 7.5 实现 `generate_matching_report()` 输出匹配报告
- [ ] 7.6 保存报告到 `matching_report.json`

**阶段7完成验证**:
```bash
# 运行匹配测试
pytest tests/textbook/test_matcher.py -v

# 手动验证：匹配知识点
python -m edukg.core.textbook.matcher --chapters textbook_chapters.json --debug
# 确认生成 matching_report.json

# 查看匹配报告（预期匹配率大幅提升）
cat edukg/data/output/matching_report.json
```

---

## Part 3: 整合与文档

### 8. 主脚本整合（阶段8）

**目标**: 整合所有服务，提供命令行接口

- [ ] 8.1 创建 `edukg/core/curriculum/main.py` 整合课标模块
- [ ] 8.2 创建 `edukg/core/textbook/main.py` 整合教材模块
- [ ] 8.3 实现命令行参数（--skip-ocr, --skip-ttl, --debug）
- [ ] 8.4 实现错误处理和日志记录
- [ ] 8.5 验证完整流程

**阶段8完成验证**:
```bash
# 运行主脚本测试
pytest tests/curriculum/test_main.py -v
pytest tests/textbook/test_main.py -v

# 运行课标完整流程
python edukg/core/curriculum/main.py --debug

# 运行教材完整流程
python edukg/core/textbook/main.py --debug

# 确认所有输出文件生成
ls -la edukg/data/output/
```

---

### 9. 文档（阶段9）

- [ ] 9.1 编写 README.md 记录使用方法
- [ ] 9.2 记录输出文件格式说明
- [ ] 9.3 验证数据质量

**阶段9完成验证**:
```bash
# 运行所有测试
pytest tests/ -v

# 最终验证输出文件
ls -la edukg/data/output/
# ocr_result.json, curriculum_kps.json, kp_comparison_report.json, curriculum_kps.ttl
# textbook_chapters.json, matching_report.json
```

---

## 任务统计

| 阶段 | 任务数量 | 说明 | 依赖 |
|------|----------|------|------|
| 阶段1 | 5 | 项目结构初始化 | - |
| 阶段2 | 5 | PDF OCR 服务（百度收费） | 阶段1 |
| 阶段3 | 6 | 知识点提取服务（LLM免费） | 阶段2 |
| **阶段3.5** | **5** | **知识点关系构建（新增）** | **阶段3** |
| 阶段4 | 5 | 知识点对比服务 | 阶段3.5 |
| 阶段5 | 6 | TTL 生成服务（含关系） | 阶段4 |
| **里程碑** | - | **人工导入 Neo4j 补全知识点** | 阶段5 |
| 阶段6 | 5 | 教材解析服务 | 阶段5（知识点已补全） |
| 阶段7 | 6 | 知识点匹配服务 | 阶段6 |
| 阶段8 | 5 | 主脚本整合 | 阶段7 |
| 阶段9 | 3 | 文档 | 阶段8 |
| **总计** | **46** | | |

---

## 输出文件说明

| 文件 | 阶段 | 说明 |
|------|------|------|
| ocr_result.json | 阶段2 | OCR 识别结果 |
| curriculum_kps.json | 阶段3 | 课标知识点结构 |
| kp_relations.json | 阶段3.5 | **知识点关系结构（HAS_TYPE, PART_OF, BELONGS_TO, Statement）** |
| kp_comparison_report.json | 阶段4 | 与 EduKG 对比报告 |
| curriculum_kps.ttl | 阶段5 | **TTL 格式输出（包含完整关系结构）** |
| textbook_chapters.json | 阶段6 | 教材章节结构 |
| matching_report.json | 阶段7 | 教材知识点匹配报告 |

---

## 知识图谱关系结构

### 新增知识点需要建立的关系

| 关系类型 | 起点 | 终点 | 语义 | 示例 |
|---------|------|------|------|------|
| HAS_TYPE | Concept | Class | 类型分类 | 凑十法 → 数学方法 |
| RELATED_TO | Statement | Concept | 定义关联 | 凑十法的定义 → 凑十法 |
| PART_OF | Concept | Concept | 部分-整体 | 20以内加法 → 加法 |
| BELONGS_TO | Concept | Concept | 所属关系 | 凑十法 → 进位加法 |

### 可能新增的 Class

| Class | 父类 | 说明 |
|-------|------|------|
| 小学数概念 | 数学概念 | 数的认识、数数、比大小 |
| 小学运算方法 | 数学方法 | 竖式计算、凑十法、破十法 |
| 小学几何概念 | 几何概念 | 简单图形认识 |

---

## 开发顺序说明

```
Part 1: 课标知识点提取（阶段1-5）
  ↓
[人工导入 Neo4j 补全知识点]
  ↓
Part 2: 教材知识点匹配（阶段6-7）
  ↓
Part 3: 整合与文档（阶段8-9）
```

**为什么这样安排？**
- EduKG 缺少小学知识点（当前匹配率仅 6%）
- 先从课标提取知识点，补全 Neo4j Concept
- 人工导入后，再做教材匹配，匹配率会大幅提升
- 避免 93% 匹配失败后还要手动创建大量 Concept

---

## 目录结构

```
edukg/core/
├── curriculum/                   # 课标模块
│   ├── __init__.py
│   ├── pdf_ocr.py               # 百度 OCR（收费）
│   ├── kp_extraction.py         # LLM 提取（免费）
│   ├── relation_builder.py      # **关系构建（新增）**
│   ├── kp_comparison.py         # 对比分析
│   ├── ttl_generator.py         # TTL 生成
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
│   ├── test_relation_builder.py  # **关系构建测试（新增）**
│   ├── test_kp_comparison.py
│   ├── test_ttl_generator.py
│   └── test_main.py
│
└── textbook/
    ├── test_parser.py
    ├── test_matcher.py
    └── test_main.py
```