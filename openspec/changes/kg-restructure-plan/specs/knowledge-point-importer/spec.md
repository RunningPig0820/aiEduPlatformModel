## MODIFIED Requirements

### Requirement: Neo4j batch import

The system SHALL import merged data into Neo4j using batch operations.

#### Scenario: Import hierarchy structure

- **WHEN** import script is executed
- **THEN** it SHALL first create hierarchy nodes: Subject, Stage, Grade, Textbook, Chapter, TextbookKnowledgePoint

#### Scenario: Create USES_KNOWLEDGE_POINT relationships

- **WHEN** TextbookKnowledgePoint nodes are imported
- **THEN** it SHALL create USES_KNOWLEDGE_POINT relationships from Chapter to TextbookKnowledgePoint

#### Scenario: Create MAPPED_TO relationships

- **WHEN** TextbookKnowledgePoint has matched_kp_id
- **THEN** it SHALL create MAPPED_TO relationship to KnowledgePoint

## ADDED Requirements

### Requirement: LLM knowledge point matching

The system SHALL use LLM to match textbook knowledge points with SPARQL knowledge points when names differ.

#### Scenario: Batch match by chapter

- **WHEN** matching knowledge points for a chapter
- **THEN** the system SHALL send a single LLM request with all knowledge points from that chapter

#### Scenario: Return match results with confidence

- **WHEN** the LLM returns match results
- **THEN** each result includes matched_kp_id, matched_kp_name, and confidence score (0-1)

### Requirement: Match confidence classification

The system SHALL classify matches by confidence score.

#### Scenario: High confidence match

- **WHEN** confidence >= 0.9
- **THEN** status SHALL be set to "auto_mapped" and MAPPED_TO relationship created

#### Scenario: Medium confidence match

- **WHEN** confidence is between 0.7 and 0.9
- **THEN** status SHALL be set to "needs_review"

#### Scenario: Low confidence match

- **WHEN** confidence < 0.7
- **THEN** status SHALL be set to "no_match"

### Requirement: Local textbook JSON parsing

The system SHALL parse local textbook JSON files from the crawler.

#### Scenario: Parse all 24 textbooks

- **WHEN** textbook parser is executed
- **THEN** it SHALL parse all JSON files from primary/middle/high directories

#### Scenario: Extract chapter and knowledge point structure

- **WHEN** textbook JSON is parsed
- **THEN** it SHALL extract stage, grade, semester, chapters, and knowledge_points