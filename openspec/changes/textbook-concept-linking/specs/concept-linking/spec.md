## ADDED Requirements

### Requirement: Exact match concept
The system SHALL match textbook knowledge points to existing Concept by exact label match.

#### Scenario: Exact label match
- **WHEN** textbook knowledge point "一元一次方程" matches Concept label "一元一次方程"
- **THEN** match result has type "exact" and confidence 1.0

#### Scenario: No exact match
- **WHEN** textbook knowledge point "正数和负数的概念" has no exact match
- **THEN** match result has type "none" and proceeds to fuzzy matching

### Requirement: Fuzzy match concept with LLM
The system SHALL use LLM for semantic matching when exact match fails.

#### Scenario: LLM semantic match
- **WHEN** textbook knowledge point "正数和负数的概念" has no exact match
- **AND** LLM determines it relates to Concept "正数"
- **THEN** match result has type "fuzzy" and confidence 0.8

#### Scenario: LLM no match
- **WHEN** LLM cannot find related Concept
- **THEN** match result has type "none" and confidence 0.0

### Requirement: Generate matching report
The system SHALL output a matching report with all results.

#### Scenario: Report contains all matches
- **WHEN** matching completes
- **THEN** report contains:
  - total textbook knowledge points
  - matched count with details
  - unmatched count with details
  - match rate percentage

#### Scenario: Report saved to file
- **WHEN** matching completes
- **THEN** report is saved to `kp_matching_result.json`

### Requirement: Create CONTAINS relationship
The system SHALL create `CONTAINS` relationship between Chapter and Concept after confirmation.

#### Scenario: Create relationship for matched concept
- **WHEN** user confirms match for "一元一次方程"
- **THEN** system creates `Chapter -[:CONTAINS]-> Concept` relationship

#### Scenario: Skip unconfirmed matches
- **WHEN** match is not confirmed
- **THEN** no relationship is created

### Requirement: Handle missing concepts
The system SHALL identify concepts that exist in textbook but not in Neo4j.

#### Scenario: List missing concepts
- **WHEN** matching completes
- **THEN** system outputs list of concepts that need to be created

#### Scenario: Support creating missing concept
- **WHEN** user confirms creating new Concept "凑十法"
- **THEN** system creates Concept node with label "凑十法"