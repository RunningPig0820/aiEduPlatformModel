## ADDED Requirements

### Requirement: Extract text from PDF
The system SHALL extract text content from PDF files using OCR.

#### Scenario: Extract text from scanned PDF
- **WHEN** processing scanned PDF file
- **THEN** system returns text content for each page

#### Scenario: Handle multi-page PDF
- **WHEN** processing PDF with 189 pages
- **THEN** system extracts text from all pages

#### Scenario: Handle non-existent file
- **WHEN** PDF file does not exist
- **THEN** system raises FileNotFoundError

### Requirement: Extract curriculum knowledge points
The system SHALL extract knowledge points from curriculum standard PDF.

#### Scenario: Extract math curriculum points
- **WHEN** processing 义务教育数学课程标准（2022年版）.pdf
- **THEN** system extracts knowledge points organized by:
  - 学段 (第一学段 1-2年级, 第二学段 3-4年级, etc.)
  - 领域 (数与代数, 图形与几何, 统计与概率)

#### Scenario: Output structured data
- **WHEN** extraction completes
- **THEN** output is JSON with structure:
  ```json
  {
    "stage": "第一学段",
    "domain": "数与代数",
    "knowledge_points": ["20以内数的认识", "加减法"]
  }
  ```

### Requirement: Support OCR configuration
The system SHALL support OCR engine configuration.

#### Scenario: Configure PaddleOCR
- **WHEN** initializing OCR service
- **THEN** system supports configuration for:
  - language (ch, en)
  - use_angle_cls (True/False)
  - show_log (True/False)

#### Scenario: Use configured OCR engine
- **WHEN** OCR engine is configured
- **THEN** all OCR operations use the configured engine

### Requirement: Provide OCR API endpoint
The system SHALL provide REST API for OCR operations.

#### Scenario: API endpoint for PDF OCR
- **WHEN** POST /api/ocr/pdf with PDF file
- **THEN** returns extracted text in JSON format

#### Scenario: API endpoint for curriculum extraction
- **WHEN** POST /api/ocr/curriculum with PDF file
- **THEN** returns extracted knowledge points in JSON format