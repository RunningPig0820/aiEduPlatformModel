## ADDED Requirements

### Requirement: Query existing concepts from Neo4j
The system SHALL query all existing Concept nodes for comparison.

#### Scenario: Get all concept labels
- **WHEN** starting comparison
- **THEN** system queries:
  ```cypher
  MATCH (c:Concept) RETURN c.label as label
  ```

#### Scenario: Handle Neo4j connection error
- **WHEN** Neo4j connection fails
- **THEN** system raises Neo4jConnectionError with retry suggestion

### Requirement: Compare extracted knowledge points
The system SHALL compare extracted knowledge points with existing concepts.

#### Scenario: Exact match
- **WHEN** extracted KP "一元一次方程" equals Concept label "一元一次方程"
- **THEN** result: {"status": "matched", "concept_label": "一元一次方程"}

#### Scenario: Partial match
- **WHEN** extracted KP contains Concept label or vice versa
- **THEN** result: {"status": "partial_match", "confidence": 0.7}

#### Scenario: No match (new concept)
- **WHEN** extracted KP has no match
- **THEN** result: {"status": "new", "suggested_types": ["数学概念"]}

### Requirement: Generate comparison report
The system SHALL generate detailed comparison report.

#### Scenario: Report statistics
- **WHEN** comparison completes
- **THEN** report includes:
  - total_extracted: number of extracted KPs
  - matched_count: exact/partial matches
  - new_count: concepts not in EduKG
  - match_rate: percentage

#### Scenario: Report details by stage
- **WHEN** generating report
- **THEN** report groups results by:
  - 学段 (第一学段 likely has most "new" items)
  - 领域

#### Scenario: Save report to JSON
- **WHEN** report generation completes
- **THEN** system saves to `kp_comparison_report.json`

### Requirement: Generate TTL output
The system SHALL generate TTL format for knowledge points.

#### Scenario: Define TTL namespace
- **WHEN** generating TTL
- **THEN** namespace follows pattern:
  - Base: `http://edukg.org/curriculum/math#`
  - Types: `curriculum:KnowledgePoint`

#### Scenario: Create TTL triples
- **WHEN** generating TTL for knowledge point "凑十法"
- **THEN** output includes:
  ```turtle
  curriculum:凑十法 a curriculum:KnowledgePoint ;
    curriculum:label "凑十法" ;
    curriculum:belongsToStage curriculum:第一学段 ;
    curriculum:belongsToDomain curriculum:数与代数 .
  ```

#### Scenario: Skip TTL if requested
- **WHEN** config.skip_ttl = True
- **THEN** system only generates JSON output