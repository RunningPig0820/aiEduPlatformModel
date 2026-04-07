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
```

### 约束

- EduKG 主要覆盖初中和高中，缺少小学知识点
- 教材知识点命名与 Concept 命名不完全一致
- 课标 PDF 是扫描版，需要 OCR
- 需要支持多学科扩展

## Goals / Non-Goals

**Goals:**

1. 创建教材章节节点，存储教材目录结构
2. 关联章节到 Concept，支持按教材查询知识点
3. 支持教材知识点与 Concept 的精确/模糊匹配
4. 输出匹配报告，支持人工确认
5. 实现 PDF OCR 服务，支持课标识别

**Non-Goals:**

1. 不处理其他学科（物理、化学）的教材，仅数学
2. 不实现作业切题功能（后续迭代）
3. 不实现学生学习状态跟踪（后续迭代）
4. 不处理课标知识点的自动导入（先人工确认）

## Decisions

### 1. 章节节点设计

**决策**: 使用 `textbook_chapter` 作为统一节点标签，通过属性区分不同教材

**理由**:
- 单一节点类型，避免创建大量相似类型（按出版社×学科组合会有 20+ 类型）
- Neo4j 处理 30-40w 数据没问题，属性索引完全够用
- 查询灵活，可组合任意属性筛选
- 新出版社、新科目只需添加数据，不需改代码

**替代方案**:
- ❌ 按出版社命名（如 `Renjiao_Chapter`）：类型数量爆炸，维护困难
- ❌ Textbook + Chapter 分开：查询复杂，教材不会复用

```
textbook_chapter:
├── name: "人教版_数学_七年级_上册_第一章_有理数"  # 唯一标识
├── publisher: "人教版"      # 人教版/北师大版/苏教版...
├── subject: "数学"          # 数学/物理/化学/语文...
├── grade: "七年级"          # 一年级~十二年级
├── semester: "上册"         # 上册/下册
├── chapter: "第一章有理数"
└── order: 1
```

**数据量估算**:
- 12(K12) × 2(上下册) × 20(学科) × 40(章节) × 20(教材版本) ≈ 30-40w 条

### 2. 知识点关联流程

**决策**: 三步流程（导入 → 匹配 → 确认）

```
Step 1: 导入章节节点（不关联知识点）
        ↓
Step 2: 匹配教材知识点 → Concept
        ├── 精确匹配: label 完全相同
        ├── 模糊匹配: LLM 语义匹配
        └── 输出匹配报告
        ↓
Step 3: 人工确认
        ├── 确认匹配正确
        ├── 创建缺失的 Concept（小学知识点）
        └── 创建 CONTAINS 关系
```

**理由**:
- 避免自动创建低质量 Concept
- 人工确认确保数据准确
- 匹配报告便于追踪

**替代方案**:
- ❌ 自动创建 Concept：可能创建重复/低质量节点
- ❌ 仅精确匹配：匹配率太低（6%）

### 3. PDF OCR 服务

**决策**: 使用 PaddleOCR 作为 OCR 引擎

**理由**:
- 中文识别效果好
- 支持表格、公式识别
- 可部署到服务器

**服务设计**:

```python
class PDFOCRService:
    def __init__(self):
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')

    def extract_text(self, pdf_path: str) -> List[PageText]:
        """提取 PDF 文字"""
        pass

    def extract_curriculum_points(self, pdf_path: str) -> List[KnowledgePoint]:
        """提取课标知识点"""
        pass
```

### 4. 模块架构

**决策**: 按功能模块组织代码

```
ai-edu-ai-service/
└── core/
    ├── ocr/
    │   ├── pdf_ocr.py          # PDF OCR 服务
    │   └── homework_cutter.py  # 作业切题（后续）
    │
    └── kg/
        └── textbook/
            ├── parser.py       # 解析教材 JSON
            ├── linker.py       # 知识点关联
            └── importer.py     # 导入 Neo4j
```

**理由**:
- 职责单一，便于测试
- 支持多学科扩展
- OCR 和 KG 解耦

## Risks / Trade-offs

### Risk 1: 知识点匹配不准确

**风险**: 模糊匹配可能关联错误的知识点

**缓解**:
- 输出匹配报告，人工确认
- 记录匹配置信度，低置信度标记待确认
- 支持回滚错误关联

### Risk 2: 小学知识点大量缺失

**风险**: EduKG 没有小学知识点，需要手动创建

**缓解**:
- 从课标提取小学知识点作为基准
- 优先导入教材，标记缺失知识点
- 后续补充小学 Concept

### Risk 3: OCR 识别准确率

**风险**: 课标 PDF 扫描质量影响 OCR 准确率

**缓解**:
- 人工校验 OCR 结果
- 提取后人工整理知识点列表
- 不直接导入，先确认再入库

## Migration Plan

### 阶段一: 教材章节导入

```bash
1. 解析教材 JSON 数据
2. 创建 textbook_chapter 节点
3. 验证导入结果
```

### 阶段二: 知识点关联

```bash
1. 精确匹配教材知识点 → Concept
2. 模糊匹配（LLM）剩余知识点
3. 输出匹配报告
4. 人工确认
5. 创建 CONTAINS 关系
```

### 阶段三: 课标 OCR（后续）

```bash
1. OCR 识别课标 PDF
2. 提取知识点列表
3. 与 EduKG Concept 对比
4. 补充缺失知识点
```