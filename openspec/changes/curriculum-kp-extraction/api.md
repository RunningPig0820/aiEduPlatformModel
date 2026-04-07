# 课标知识点提取 使用文档

> 脚本路径: `edukg/scripts/curriculum/`
>
> 更新日期: 2026-04-07

---

## 目录

- [命令行接口](#命令行接口)
- [输出文件说明](#输出文件说明)
- [配置说明](#配置说明)
- [错误码说明](#错误码说明)

---

## 命令行接口

本模块为数据处理脚本，不提供 HTTP API，通过命令行运行。

### 1. 完整流程运行

```bash
python edukg/scripts/curriculum/main.py
```

**默认行为**:
- OCR 识别课标 PDF
- LLM 提取知识点
- 对比 EduKG Concept
- 生成 JSON + TTL 输出

### 2. 指定参数运行

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| --skip-ocr | bool | False | 跳过 OCR，使用已有 ocr_result.json |
| --skip-ttl | bool | False | 跳过 TTL 生成 |
| --debug | bool | False | 输出详细日志 |
| --pdf-path | str | eduBureau/math/*.pdf | 指定 PDF 文件路径 |
| --output-dir | str | eduBureau/math/ | 输出目录 |

**示例**:

```bash
# 跳过 OCR（已有 OCR 结果）
python main.py --skip-ocr

# 仅生成 JSON，跳过 TTL
python main.py --skip-ttl

# 指定 PDF 和输出目录
python main.py --pdf-path /path/to/curriculum.pdf --output-dir /path/to/output/

# 调试模式
python main.py --debug
```

### 3. 分步运行

```bash
# 仅 OCR
python -m curriculum.pdf_ocr --pdf-path curriculum.pdf

# 仅提取（需要 OCR 结果）
python -m curriculum.kp_extraction

# 仅对比（需要提取结果）
python -m curriculum.kp_comparison

# 仅 TTL 生成
python -m curriculum.ttl_generator
```

---

## 输出文件说明

### 1. ocr_result.json

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

| 字段 | 类型 | 说明 |
|------|------|------|
| pdf_path | String | PDF 文件路径 |
| total_pages | Integer | 总页数 |
| pages | Array | 每页文本内容 |

### 2. curriculum_kps.json

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

| 字段 | 类型 | 说明 |
|------|------|------|
| source | String | 来源文档 |
| extracted_at | String | 提取时间 |
| stages | Array | 学段列表 |
| stage.stage | String | 学段名称 |
| stage.grades | String | 年级范围 |
| stage.domains | Array | 领域列表 |
| domain.domain | String | 领域名称 |
| domain.knowledge_points | Array | 知识点列表 |

### 3. kp_comparison_report.json

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
  ],
  "by_stage": {
    "第一学段": {"total": 50, "new": 48},
    "第二学段": {"total": 40, "new": 35},
    "第三学段": {"total": 30, "new": 15},
    "第四学段": {"total": 30, "new": 7}
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| total_extracted | Integer | 提取知识点总数 |
| matched_count | Integer | 已匹配数量 |
| new_count | Integer | 新增数量 |
| match_rate | String | 匹配率 |
| results | Array | 每个知识点对比结果 |
| by_stage | Object | 按学段统计 |

### 4. curriculum_kps.ttl

RDF/TTL 格式输出（可选）。

```turtle
@prefix curriculum: <http://edukg.org/curriculum/math#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

curriculum:凑十法 a curriculum:KnowledgePoint ;
    rdfs:label "凑十法" ;
    curriculum:belongsToStage curriculum:第一学段 ;
    curriculum:belongsToDomain curriculum:数与代数 .

curriculum:20以内数的认识 a curriculum:KnowledgePoint ;
    rdfs:label "20以内数的认识" ;
    curriculum:belongsToStage curriculum:第一学段 ;
    curriculum:belongsToDomain curriculum:数与代数 .
```

---

## 配置说明

### 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| BAIDU_OCR_API_KEY | 是 | 百度 OCR API Key |
| BAIDU_OCR_SECRET_KEY | 是 | 百度 OCR Secret Key |
| ZHIPU_API_KEY | 是 | 智谱 API Key（glm-4-flash） |
| NEO4J_URI | 是 | Neo4j 连接地址 |
| NEO4J_USER | 是 | Neo4j 用户名 |
| NEO4J_PASSWORD | 是 | Neo4j 密码 |

### OCR 配置

```python
# pdf_ocr.py 使用百度 OCR API
OCR_CONFIG = {
    "api_key": os.environ["BAIDU_OCR_API_KEY"],
    "secret_key": os.environ["BAIDU_OCR_SECRET_KEY"],
    "detect_language": True,   # 自动检测语言
    "detect_direction": True,  # 检测文字方向
}
```

### LLM 配置

```python
# kp_extraction.py 默认配置
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

### Neo4j 错误码 (2xxxx)

| code | message | 说明 |
|------|---------|------|
| 20002 | Neo4j 连接失败 | 数据库连接异常 |
| 20003 | 查询失败 | Cypher 查询执行失败 |

---

## 运行示例

```bash
# 1. 配置环境变量
export BAIDU_OCR_API_KEY="your-baidu-api-key"
export BAIDU_OCR_SECRET_KEY="your-baidu-secret-key"
export ZHIPU_API_KEY="your-zhipu-api-key"
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="password"

# 2. 安装依赖
pip install baidu-aip langchain-community pdf2image

# 3. 运行完整流程
cd edukg/scripts/curriculum
python main.py

# 4. 查看输出
ls -la ../../data/eduBureau/math/
# ocr_result.json
# curriculum_kps.json
# kp_comparison_report.json
# curriculum_kps.ttl
```

---

*文档生成时间: 2026-04-07*