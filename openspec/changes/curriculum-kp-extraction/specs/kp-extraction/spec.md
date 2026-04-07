## ADDED Requirements

### Requirement: Initialize LLM with free model
The system SHALL use glm-4-flash (智谱免费模型) for knowledge point extraction.

#### Scenario: Configure LangChain ChatZhipuAI
- **WHEN** initializing LLM service
- **THEN** system uses:
  - model: "glm-4-flash"
  - temperature: 0.1 (low for structured output)
  - API key from environment

#### Scenario: Handle API key missing
- **WHEN** ZHIPU_API_KEY not set
- **THEN** system raises ConfigurationError

### Requirement: Extract knowledge points from text
The system SHALL use LLM to extract structured knowledge points from curriculum text.

#### Scenario: Parse curriculum by section
- **WHEN** processing curriculum OCR text
- **THEN** LLM extracts:
  - Stage (学段)
  - Grades (年级范围)
  - Domain (领域)
  - Knowledge points (知识点)

#### Scenario: Use structured prompt
- **WHEN** calling LLM
- **THEN** prompt includes:
  - JSON output format requirement
  - Example structure
  - Domain-specific vocabulary (数学术语)

#### Scenario: Handle large text
- **WHEN** text exceeds token limit
- **THEN** system splits into chunks by page/section

### Requirement: Validate extracted structure
The system SHALL validate LLM output against expected schema.

#### Scenario: Validate JSON structure
- **WHEN** receiving LLM output
- **THEN** system validates:
  - Required fields: stages, stage, domains, knowledge_points
  - Valid stage names: 第一学段~第四学段
  - Valid domain names: 数与代数, 图形与几何, 统计与概率

#### Scenario: Handle invalid structure
- **WHEN** validation fails
- **THEN** system logs error and retries with clearer prompt