# curriculum-kp Specification

## Purpose
TBD - created by archiving change textbook-concept-linking. Update Purpose after archive.
## Requirements
### Requirement: Extract text from PDF using Baidu OCR API
The system SHALL extract text content from scanned PDF files using Baidu OCR API.

#### Scenario: Extract text from curriculum PDF
- **WHEN** processing 义务教育数学课程标准（2022年版）.pdf
- **THEN** system extracts text content for each page via Baidu OCR API

#### Scenario: Convert PDF to images for OCR
- **WHEN** processing PDF file
- **THEN** system converts each page to image before OCR recognition

#### Scenario: Save OCR result to JSON
- **WHEN** OCR extraction completes
- **THEN** system saves result to `ocr_result.json` with page-by-page content

#### Scenario: Handle multi-page PDF
- **WHEN** processing PDF with 189 pages
- **THEN** system extracts text from all pages with progress indicator

#### Scenario: Handle API rate limit
- **WHEN** Baidu OCR API returns rate limit error
- **THEN** system waits and retries with exponential backoff

#### Scenario: Handle OCR API failure
- **WHEN** Baidu OCR API call fails
- **THEN** system raises OCRAPIError with clear message

### Requirement: Extract structured knowledge points using LLM
The system SHALL use LLM to extract structured knowledge points from OCR text.

#### Scenario: Extract knowledge points by stage
- **WHEN** LLM processes curriculum text
- **THEN** system extracts knowledge points organized by:
  - 学段 (第一学段 1-2年级, 第二学段 3-4年级, etc.)
  - 领域 (数与代数, 图形与几何, 统计与概率)

#### Scenario: Use glm-4-flash model
- **WHEN** extracting knowledge points
- **THEN** system uses glm-4-flash (free model) via LangChain

#### Scenario: Output structured JSON
- **WHEN** extraction completes
- **THEN** output is JSON with structure:
  ```json
  {
    "stages": [
      {
        "stage": "第一学段",
        "grades": "1-2年级",
        "domains": [
          {
            "domain": "数与代数",
            "knowledge_points": ["20以内数的认识", "加减法"]
          }
        ]
      }
    ]
  }
  ```

#### Scenario: Handle LLM response parsing error
- **WHEN** LLM returns malformed response
- **THEN** system retries with clearer prompt or logs error

### Requirement: Compare with existing EduKG concepts
The system SHALL compare extracted knowledge points with existing EduKG Concept nodes (read-only).

#### Scenario: Query existing concepts
- **WHEN** starting comparison
- **THEN** system queries all Concept nodes from Neo4j (read-only)

#### Scenario: Identify matching concepts
- **WHEN** knowledge point "一元一次方程" exists in EduKG
- **THEN** comparison result shows "matched" status

#### Scenario: Identify missing concepts
- **WHEN** knowledge point "凑十法" not in EduKG
- **THEN** comparison result shows "new" status with suggestion

#### Scenario: Generate comparison report
- **WHEN** comparison completes
- **THEN** system saves report to `kp_comparison_report.json`

### Requirement: Generate TTL output
The system SHALL generate RDF/TTL format output for knowledge points.

#### Scenario: Create TTL file
- **WHEN** knowledge points are confirmed
- **THEN** system generates `textbook_kps.ttl` with proper namespace

#### Scenario: TTL format compliance
- **WHEN** generating TTL
- **THEN** output follows EduKG namespace conventions:
  - Prefix: `curriculum:math#`
  - Types: `curriculum:KnowledgePoint`
  - Relations: `curriculum:belongsToStage`, `curriculum:belongsToDomain`

#### Scenario: Skip TTL generation
- **WHEN** user requests only JSON output
- **THEN** system skips TTL generation step

