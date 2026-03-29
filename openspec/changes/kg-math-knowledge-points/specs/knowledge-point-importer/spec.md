## ADDED Requirements

### Requirement: Knowledge point data merging

The system SHALL merge cleaned knowledge point data with textbook mapping data.

#### Scenario: Merge by URI

- **WHEN** knowledge point data and textbook mapping data are merged
- **THEN** the merger SHALL join records by kp_uri field

#### Scenario: Fill grade information

- **WHEN** a knowledge point has matching textbook record
- **THEN** the merger SHALL fill grade field with inferred_grade value

#### Scenario: Fill chapter information

- **WHEN** a knowledge point has matching textbook record
- **THEN** the merger SHALL fill chapter field with chapter_name value

### Requirement: Final data output

The system SHALL output merged data in JSON format ready for Neo4j import.

#### Scenario: Output to JSON file

- **WHEN** merging process is complete
- **THEN** the script SHALL write the result to `math_final_data.json`

#### Scenario: Final data structure

- **WHEN** JSON file is written
- **THEN** each knowledge point SHALL have all required fields: uri, external_id, name, subject, stage, grade, chapter, type, difficulty, description, source

### Requirement: Neo4j batch import

The system SHALL import merged data into Neo4j using batch operations.

#### Scenario: Import hierarchy structure

- **WHEN** import script is executed
- **THEN** it SHALL first create hierarchy nodes: Subject, Stage, Grade, Textbook, Chapter

#### Scenario: Import knowledge points

- **WHEN** hierarchy nodes are created
- **THEN** it SHALL import all KnowledgePoint nodes with all properties

#### Scenario: Create HAS_KNOWLEDGE_POINT relationships

- **WHEN** knowledge points are imported
- **THEN** it SHALL create HAS_KNOWLEDGE_POINT relationships from Chapter to KnowledgePoint

### Requirement: Import validation

The system SHALL validate imported data completeness.

#### Scenario: Validate node count

- **WHEN** import is complete
- **THEN** validation script SHALL check KnowledgePoint count equals expected value (4,490)

#### Scenario: Validate URI uniqueness

- **WHEN** import is complete
- **THEN** validation script SHALL verify no duplicate URIs exist

#### Scenario: Validate required fields

- **WHEN** import is complete
- **THEN** validation script SHALL verify all nodes have non-null name and uri fields