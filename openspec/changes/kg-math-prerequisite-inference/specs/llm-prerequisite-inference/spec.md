## ADDED Requirements

### Requirement: LLM prerequisite inference

The system SHALL use LLM models to infer prerequisite relations between knowledge points.

#### Scenario: Call GLM-4-flash model

- **WHEN** prerequisite inference is triggered
- **THEN** the system SHALL call GLM-4-flash model via LLM Gateway

#### Scenario: Call DeepSeek model

- **WHEN** prerequisite inference is triggered
- **THEN** the system SHALL also call DeepSeek model for voting

### Requirement: Multi-model voting

The system SHALL use multi-model voting to improve accuracy.

#### Scenario: Accept when both models agree

- **WHEN** GLM-4-flash and DeepSeek both agree that a prerequisite relation exists
- **THEN** the system SHALL accept the relation

#### Scenario: Reject when models disagree

- **WHEN** GLM-4-flash and DeepSeek have different opinions
- **THEN** the system SHALL NOT accept the relation (discard or mark as candidate)

### Requirement: Confidence threshold

The system SHALL use confidence threshold to classify relations.

#### Scenario: High confidence → PREREQUISITE

- **WHEN** both models agree with confidence ≥ 0.8
- **THEN** the relation SHALL be classified as PREREQUISITE

#### Scenario: Low confidence → PREREQUISITE_CANDIDATE

- **WHEN** both models agree with confidence < 0.8
- **THEN** the relation SHALL be classified as PREREQUISITE_CANDIDATE

### Requirement: Batch processing

The system SHALL process knowledge points in batches to reduce API calls.

#### Scenario: Batch size configuration

- **WHEN** inference is executed
- **THEN** the system SHALL use configurable batch size (default: 10)

### Requirement: LLM Gateway scene

The system SHALL use prerequisite_inference scene for LLM calls.

#### Scenario: Use configured scene

- **WHEN** calling LLM Gateway
- **THEN** the system SHALL use scene: prerequisite_inference

### Requirement: CSV output format

The system SHALL output LLM inference results in CSV format.

#### Scenario: Output to CSV file

- **WHEN** inference process is complete
- **THEN** the script SHALL write the result to `math_llm_prereq.csv`

#### Scenario: CSV structure

- **WHEN** CSV file is written
- **THEN** each row SHALL have: source_uri, target_uri, relation_type, confidence, glm_result, deepseek_result