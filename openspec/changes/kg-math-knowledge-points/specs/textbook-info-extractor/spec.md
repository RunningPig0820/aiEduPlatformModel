## ADDED Requirements

### Requirement: Textbook information extraction

The system SHALL provide a script to extract textbook information from main.ttl.

#### Scenario: Extract textbook entities

- **WHEN** the textbook extractor script is executed against `main.ttl`
- **THEN** it SHALL extract textbook entities with properties: name, isbn, subject, grade

#### Scenario: Extract chapter information

- **WHEN** textbook data is parsed
- **THEN** the extractor SHALL also extract chapter information with properties: name, order, textbook_isbn

### Requirement: Knowledge point-textbook matching

The system SHALL match knowledge points to textbooks using label similarity.

#### Scenario: Match by label similarity

- **WHEN** a knowledge point label matches a textbook chapter name
- **THEN** the matcher SHALL create a mapping record linking the knowledge point to the chapter

#### Scenario: Handle unmatched knowledge points

- **WHEN** a knowledge point cannot be matched to any textbook
- **THEN** the matcher SHALL mark the knowledge point as "年级未知"

#### Scenario: Matching coverage validation

- **WHEN** matching process is complete
- **THEN** matching coverage SHALL be at least 80% (knowledge points matched to textbook/chapter)

### Requirement: Grade inference

The system SHALL infer grade level from textbook information.

#### Scenario: Infer grade from textbook name

- **WHEN** a knowledge point is matched to a textbook
- **THEN** the system SHALL infer grade level using predefined textbook-grade mapping

#### Scenario: Handle初中 textbooks

- **WHEN** a knowledge point is matched to a初中 textbook
- **THEN** the system SHALL correctly infer grade as 初一/初二/初三 based on textbook name

#### Scenario: Handle高中 textbooks

- **WHEN** a knowledge point is matched to a高中 textbook
- **THEN** the system SHALL correctly infer grade as 高一/高二/高三 based on textbook name

### Requirement: Mapping output format

The system SHALL output textbook-knowledge point mapping in JSON format.

#### Scenario: Output to JSON file

- **WHEN** extraction and matching process is complete
- **THEN** the script SHALL write the result to `math_textbook_mapping.json`

#### Scenario: Mapping structure validation

- **WHEN** JSON file is written
- **THEN** each mapping record SHALL have: kp_uri, textbook_name, chapter_name, inferred_grade