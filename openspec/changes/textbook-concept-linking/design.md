## Context

### 当前状态

```
Neo4j 数学知识图谱:
├── Class: 38 个（概念类）
├── Concept: 1,275 个（知识点）
├── Statement: 2,810 个（定义/定理）
└── 关系: SUB_CLASS_OF, HAS_TYPE, RELATED_TO, PART_OF, BELONGS_TO

教材数据:
├── 小学数学: 12册, 102章, ~200知识点
├── 初中数学: 6册, 29章, ~300知识点
└── 高中数学: 6册, 21章, ~100知识点

知识点匹配现状:
├── 教材知识点: 346个
├── 匹配成功: 24个 (6%)
└── 匹配失败: 322个 (93%) ← 主要缺少小学知识点

课标文件:
├── 义务教育数学课程标准（2022年版）.pdf
└── 扫描版，189页
```

### 约束

- EduKG 主要覆盖初中和高中，缺少小学知识点
- 教材知识点命名与 Concept 命名不完全一致
- 课标 PDF 是扫描版，需要 OCR
- 需要支持多学科扩展
- **不直接导入 Neo4j**，只生成文件供人工确认后导入

## Goals / Non-Goals

**Goals:**

1. 解析教材 JSON 数据，生成章节结构文件
2. 匹配教材知识点与 Neo4j Concept，生成匹配报告
3. OCR 识别课标 PDF（百度 OCR API，收费）
4. LLM 提取课标知识点（glm-4-flash 免费）
5. 对比课标知识点与 EduKG Concept，生成对比报告
6. 输出 JSON/TTL 格式文件

**Non-Goals:**

1. **不自动导入 Neo4j**（人工确认后手动导入）
2. 不处理其他学科（物理、化学）的教材，仅数学
3. 不实现作业切题功能（后续迭代）
4. 不实现学生学习状态跟踪（后续迭代）

## Decisions

### 1. 数据处理服务（不导入 Neo4j）

**决策**: 生成 JSON/TTL 文件，不直接导入 Neo4j

**理由**:
- 避免自动创建低质量 Concept
- 人工确认确保数据准确
- 匹配报告便于追踪
- 支持回滚和调整

**替代方案**:
- ❌ 自动导入 Neo4j：可能创建重复/低质量节点，无法回滚

```
输出文件:
├── edukg/data/eduBureau/math/
│   ├── ocr_result.json              # OCR 结果
│   ├── classes.json                 # Class 定义（Neo4j格式）
│   ├── concepts.json                # Concept 知识点（Neo4j格式）
│   ├── statements.json              # Statement 定义（Neo4j格式）
│   └── relations.json               # 关系（Neo4j格式）
├── edukg/data/output/
│   ├── curriculum_kps.json          # 课标知识点（中间文件）
│   ├── kp_comparison_report.json    # 对比报告
│   ├── textbook_chapters.json       # 章节结构
│   └── matching_report.json         # 匹配报告
```

**JSON 格式要求**:
- 符合 Neo4j 导入格式
- 参考 EduKG 现有数据格式:
  - Class: `edukg/data/edukg/math/1_概念类(Class)/math_classes.json`
  - Entity: `edukg/data/edukg/math/8_全部关联关系(Complete)/math_entities_complete.json`
  - Relation: `edukg/data/edukg/math/8_全部关联关系(Complete)/math_knowledge_relations.json`

### 2. OCR 技术选型

**决策**: 使用百度 OCR API（收费服务）

**理由**:
- 用户已有百度 OCR 账号
- 中文识别效果好
- API 调用简单，无需本地部署
- 支持 QPS 限制和重试

**费用说明**:
- 百度 OCR 是收费服务，按次计费
- 建议控制调用次数，优先处理关键页面
- 可使用免费额度或购买套餐

**替代方案**:
- ❌ PaddleOCR：需要本地部署 GPU，维护成本高
- ❌ PyMuPDF：仅提取已有文字，无法识别扫描版

### 3. LLM 选型

**决策**: 使用智谱 glm-4-flash（免费）

**理由**:
- 免费，成本可控
- 中文理解能力强
- 支持 JSON 结构化输出
- 通过 LangChain 集成

**替代方案**:
- ❌ DeepSeek：需要付费
- ❌ 百炼 qwen：需要付费

### 4. 模块架构

**决策**: 分为两个独立模块（教材 + 课标），放在 `edukg/core/` 目录

```
edukg/core/
├── textbook/                    # 教材模块
│   ├── parser.py                # 解析教材 JSON
│   ├── matcher.py               # 匹配知识点
│   └── main.py                  # 主脚本
│
└── curriculum/                  # 课标模块
    ├── pdf_ocr.py               # 百度 OCR（收费）
    ├── kp_extraction.py         # LLM 提取
    ├── relation_builder.py      # 关系构建（Neo4j格式）
    ├── kp_comparison.py         # 对比分析
    └── main.py                  # 主脚本
```

**理由**:
- 教材和课标是两个独立的数据源
- 职责单一，便于测试
- 可独立运行，也可整合运行
- 放在 `edukg/core/` 与现有项目结构保持一致

### 5. 知识点匹配策略

**决策**: 精确匹配 + LLM 模糊匹配，输出报告

```
匹配流程:
1. 精确匹配: label 完全相同 → matched (confidence: 1.0)
2. 模糊匹配: LLM 语义匹配 → fuzzy_match (confidence: 0.8)
3. 无匹配: Concept 不存在 → new (confidence: 0.0)
4. 输出报告: matching_report.json
```

**理由**:
- 精确匹配成本低，先尝试
- LLM 模糊匹配提高匹配率
- 输出报告供人工确认

### 6. 知识点关系构建策略

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

## Risks / Trade-offs

### Risk 1: 知识点匹配不准确

**风险**: 模糊匹配可能关联错误的知识点

**缓解**:
- 输出匹配报告，人工确认
- 记录匹配置信度，低置信度标记待确认
- 不自动导入，需人工确认

### Risk 2: 小学知识点大量缺失

**风险**: EduKG 没有小学知识点，需要手动创建

**缓解**:
- 从课标提取小学知识点作为基准
- 对比报告标记缺失知识点
- 人工确认后手动导入

### Risk 3: OCR 识别准确率

**风险**: 课标 PDF 扫描质量影响 OCR 准确率

**缓解**:
- 人工校验 OCR 结果
- 提取后人工整理知识点列表
- 不直接导入，先确认再入库

### Risk 4: API 调用成本

**风险**: 百度 OCR 收费，LLM API 费用

**缓解**:
- 百度 OCR: 控制调用次数，使用免费额度或套餐
- LLM: 使用 glm-4-flash 免费
- 分批处理，记录进度

## Migration Plan

### 阶段一: 课标 OCR + 提取（先补全知识点）

```bash
1. 百度 OCR 识别课标 PDF
2. LLM 提取知识点结构
3. 与 Neo4j Concept 对比
4. 输出 kp_comparison_report.json
5. 人工确认后导入 Neo4j
```

### 阶段二: 教材解析 + 匹配

```bash
1. 解析教材 JSON 数据
2. 查询 Neo4j Concept（只读）
3. 精确匹配 + LLM 模糊匹配
4. 输出 matching_report.json
5. 人工确认
```

### 阶段三: TTL 生成（可选）

```bash
1. 整合教材 + 课标知识点
2. 生成 TTL 格式文件
3. 人工确认后手动导入 Neo4j
```