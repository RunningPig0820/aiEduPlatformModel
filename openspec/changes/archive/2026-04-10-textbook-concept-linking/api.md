# 教材知识点关联 使用文档

> 脚本路径: `edukg/core/`
>
> 更新日期: 2026-04-07

---

## 目录

- [教材模块](#教材模块)
- [课标模块](#课标模块)
- [输出文件说明](#输出文件说明)
- [配置说明](#配置说明)
- [错误码说明](#错误码说明)

---

## 教材模块

本模块为数据处理脚本，通过命令行运行。

### 1. 教材解析

```bash
python edukg/core/textbook/parser.py
```

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| --input | str | edukg/data/renjiao/math.json | 教材 JSON 文件路径 |
| --output | str | edukg/data/output/ | 输出目录 |
| --debug | bool | False | 输出详细日志 |

**示例**:

```bash
# 解析默认教材
python edukg/core/textbook/parser.py

# 指定输入输出
python edukg/core/textbook/parser.py --input /path/to/textbook.json --output /path/to/output/

# 调试模式
python edukg/core/textbook/parser.py --debug
```

### 2. 知识点匹配

```bash
python edukg/core/textbook/matcher.py
```

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| --chapters | str | textbook_chapters.json | 章节文件路径 |
| --use-llm | bool | False | 使用 LLM 模糊匹配 |
| --output | str | edukg/data/output/ | 输出目录 |
| --debug | bool | False | 输出详细日志 |

**示例**:

```bash
# 精确匹配
python edukg/core/textbook/matcher.py

# 使用 LLM 模糊匹配
python edukg/core/textbook/matcher.py --use-llm

# 调试模式
python edukg/core/textbook/matcher.py --debug
```

### 3. 教材完整流程

```bash
python edukg/core/textbook/main.py
```

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| --input | str | edukg/data/renjiao/math.json | 教材 JSON 文件路径 |
| --use-llm | bool | False | 使用 LLM 模糊匹配 |
| --output | str | edukg/data/output/ | 输出目录 |
| --debug | bool | False | 输出详细日志 |

---

## 课标模块

### 1. PDF OCR

> **注意**: 百度 OCR 是收费服务，按次计费，建议控制调用次数

```bash
python edukg/core/curriculum/pdf_ocr.py
```

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| --pdf-path | str | eduBureau/math/*.pdf | PDF 文件路径 |
| --output | str | edukg/data/output/ | 输出目录 |
| --debug | bool | False | 输出详细日志 |

**示例**:

```bash
# OCR 默认课标
python edukg/core/curriculum/pdf_ocr.py

# 指定 PDF 文件
python edukg/core/curriculum/pdf_ocr.py --pdf-path /path/to/curriculum.pdf

# 调试模式
python edukg/core/curriculum/pdf_ocr.py --debug
```

### 2. 知识点提取

> **免费服务**: 使用智谱 glm-4-flash，不产生费用

```bash
python edukg/core/curriculum/kp_extraction.py
```

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| --ocr-result | str | ocr_result.json | OCR 结果文件 |
| --output | str | edukg/data/output/ | 输出目录 |
| --debug | bool | False | 输出详细日志 |

### 3. 知识点对比

```bash
python edukg/core/curriculum/kp_comparison.py
```

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| --kps | str | curriculum_kps.json | 知识点文件 |
| --output | str | edukg/data/output/ | 输出目录 |
| --debug | bool | False | 输出详细日志 |

### 4. TTL 生成

```bash
python edukg/core/curriculum/ttl_generator.py
```

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| --kps | str | curriculum_kps.json | 知识点文件 |
| --output | str | edukg/data/output/ | 输出目录 |
| --skip-ttl | bool | False | 跳过 TTL 生成 |
| --debug | bool | False | 输出详细日志 |

### 5. 课标完整流程

```bash
python edukg/core/curriculum/main.py
```

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| --pdf-path | str | eduBureau/math/*.pdf | PDF 文件路径 |
| --output-dir | str | edukg/data/output/ | 输出目录 |
| --skip-ocr | bool | False | 跳过 OCR，使用已有 ocr_result.json |
| --skip-ttl | bool | False | 跳过 TTL 生成 |
| --debug | bool | False | 输出详细日志 |

**示例**:

```bash
# 完整流程
python edukg/core/curriculum/main.py

# 跳过 OCR（已有 OCR 结果）
python edukg/core/curriculum/main.py --skip-ocr

# 仅生成 JSON，跳过 TTL
python edukg/core/curriculum/main.py --skip-ttl

# 调试模式
python edukg/core/curriculum/main.py --debug
```

---

## 输出文件说明

### 1. textbook_chapters.json

教材章节结构。

```json
{
  "source": "人教版数学",
  "parsed_at": "2026-04-07T10:30:00Z",
  "total_chapters": 29,
  "chapters": [
    {
      "name": "人教版_数学_七年级_上册_第一章_有理数",
      "publisher": "人教版",
      "subject": "数学",
      "grade": "七年级",
      "semester": "上册",
      "chapter": "第一章有理数",
      "order": 1,
      "knowledge_points": ["有理数", "数轴", "相反数"]
    }
  ]
}
```

### 2. matching_report.json

教材知识点匹配报告。

```json
{
  "matched_at": "2026-04-07T10:35:00Z",
  "total_textbook_kps": 346,
  "matched_count": 24,
  "unmatched_count": 322,
  "match_rate": "6%",
  "matches": [
    {
      "textbook_kp": "一元一次方程",
      "concept_label": "一元一次方程",
      "match_type": "exact",
      "confidence": 1.0
    },
    {
      "textbook_kp": "正数和负数的概念",
      "concept_label": "正数",
      "match_type": "fuzzy",
      "confidence": 0.8
    }
  ]
}
```

### 3. ocr_result.json

OCR 识别原始结果。

```json
{
  "pdf_path": "义务教育数学课程标准（2022年版）.pdf",
  "total_pages": 189,
  "pages": [
    {
      "page_num": 1,
      "text": "义务教育数学课程标准..."
    }
  ]
}
```

### 4. curriculum_kps.json

LLM 提取的结构化知识点。

```json
{
  "source": "义务教育数学课程标准（2022年版）",
  "extracted_at": "2026-04-07T10:30:00Z",
  "stages": [
    {
      "stage": "第一学段",
      "grades": "1-2年级",
      "domains": [
        {
          "domain": "数与代数",
          "knowledge_points": ["20以内数的认识", "加减法", "乘法的初步认识"]
        },
        {
          "domain": "图形与几何",
          "knowledge_points": ["认识图形", "位置与方向"]
        }
      ]
    }
  ]
}
```

### 5. kp_comparison_report.json

与 EduKG Concept 对比报告。

```json
{
  "comparison_at": "2026-04-07T10:35:00Z",
  "total_extracted": 150,
  "matched_count": 45,
  "new_count": 105,
  "match_rate": "30%",
  "results": [
    {
      "knowledge_point": "一元一次方程",
      "status": "matched",
      "concept_label": "一元一次方程"
    },
    {
      "knowledge_point": "凑十法",
      "status": "new",
      "suggested_types": ["数学概念", "计算方法"]
    }
  ]
}
```

### 6. curriculum_kps.ttl

RDF/TTL 格式输出（可选）。

```turtle
@prefix curriculum: <http://edukg.org/curriculum/math#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

curriculum:凑十法 a curriculum:KnowledgePoint ;
    rdfs:label "凑十法" ;
    curriculum:belongsToStage curriculum:第一学段 ;
    curriculum:belongsToDomain curriculum:数与代数 .
```

---

## 配置说明

### 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| NEO4J_URI | 是 | Neo4j 连接地址 |
| NEO4J_USER | 是 | Neo4j 用户名 |
| NEO4J_PASSWORD | 是 | Neo4j 密码 |
| BAIDU_OCR_API_KEY | 是 | 百度 OCR API Key（收费服务） |
| BAIDU_OCR_SECRET_KEY | 是 | 百度 OCR Secret Key（收费服务） |
| ZHIPU_API_KEY | 是 | 智谱 API Key（glm-4-flash 免费） |

### OCR 配置

```python
# pdf_ocr.py 使用百度 OCR API（收费服务）
OCR_CONFIG = {
    "api_key": os.environ["BAIDU_OCR_API_KEY"],
    "secret_key": os.environ["BAIDU_OCR_SECRET_KEY"],
    "detect_language": True,   # 自动检测语言
    "detect_direction": True,  # 检测文字方向
}
```

### LLM 配置

```python
# kp_extraction.py 默认配置（免费）
LLM_CONFIG = {
    "model": "glm-4-flash",  # 免费
    "temperature": 0.1,      # 低温度，稳定输出
    "max_tokens": 4096
}
```

---

## 错误码说明

### 通用错误码 (1xxxx)

| code | message | 说明 |
|------|---------|------|
| 00000 | success | 成功 |
| 10000 | 系统错误 | 服务器内部错误 |
| 10001 | 参数错误 | 命令行参数格式不正确 |
| 10002 | 实体不存在 | 文件不存在 |
| 10003 | 配置错误 | 环境变量缺失 |

### Neo4j 错误码 (2xxxx)

| code | message | 说明 |
|------|---------|------|
| 20002 | Neo4j 连接失败 | 数据库连接异常 |
| 20003 | 查询失败 | Cypher 查询执行失败 |

### OCR 错误码 (3xxxx)

| code | message | 说明 |
|------|---------|------|
| 30001 | 文件格式错误 | 不是有效的 PDF 文件 |
| 30002 | OCR API 调用失败 | 百度 OCR API 调用异常 |
| 30003 | OCR API 限流 | 超过 QPS 限制 |
| 30004 | OCR 处理失败 | PDF 转图片或识别出错 |

### LLM 错误码 (4xxxx)

| code | message | 说明 |
|------|---------|------|
| 40001 | API Key 缺失 | ZHIPU_API_KEY 未配置 |
| 40002 | LLM 调用失败 | API 调用超时或失败 |
| 40003 | 输出格式错误 | LLM 返回格式不符合 schema |

---

## 运行示例

```bash
# 1. 配置环境变量
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="password"
export BAIDU_OCR_API_KEY="your-baidu-api-key"
export BAIDU_OCR_SECRET_KEY="your-baidu-secret-key"
export ZHIPU_API_KEY="your-zhipu-api-key"

# 2. 安装依赖
pip install baidu-aip langchain-community pdf2image

# 3. 运行课标模块（先补全知识点）
python edukg/core/curriculum/main.py --debug

# 4. 人工导入 curriculum_kps.ttl 到 Neo4j

# 5. 运行教材模块（补全后匹配更准确）
python edukg/core/textbook/main.py --debug

# 6. 查看输出
ls -la edukg/data/output/
# textbook_chapters.json
# matching_report.json
# ocr_result.json
# curriculum_kps.json
# kp_comparison_report.json
# curriculum_kps.ttl
```

---

## 目录结构

```
edukg/core/
├── curriculum/                   # 课标模块
│   ├── __init__.py
│   ├── pdf_ocr.py               # 百度 OCR（收费）
│   ├── kp_extraction.py         # LLM 提取（免费）
│   ├── kp_comparison.py         # 对比分析
│   ├── ttl_generator.py         # TTL 生成
│   └── main.py                  # 主脚本
│
└── textbook/                     # 教材模块
    ├── __init__.py
    ├── parser.py                # 解析教材 JSON
    ├── matcher.py               # 匹配知识点
    └── main.py                  # 主脚本
```

---

*文档生成时间: 2026-04-07*