# concept-linking Specification

## Purpose
TBD - created by archiving change textbook-concept-linking. Update Purpose after archive.
## Requirements
### Requirement: Exact match concept
The system SHALL match textbook knowledge points to existing Concept by exact label match (read-only from Neo4j).

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
The system SHALL output a matching report (no Neo4j relationship creation).

#### Scenario: Report contains all matches
- **WHEN** matching completes
- **THEN** report contains:
  - total textbook knowledge points
  - matched count with details
  - unmatched count with details
  - match rate percentage

#### Scenario: Report saved to file
- **WHEN** matching completes
- **THEN** report is saved to `matching_report.json`

### Requirement: No automatic relationship creation
The system SHALL NOT create CONTAINS relationship automatically.

#### Scenario: Output report only
- **WHEN** matching completes
- **THEN** only generates `matching_report.json`, no Neo4j relationship creation

#### Scenario: Manual confirmation required
- **WHEN** user wants to create relationships
- **THEN** user manually confirms matches and runs import script

### Requirement: Query Neo4j read-only
The system SHALL only query Neo4j for Concept labels, no write operations.

#### Scenario: Query all Concepts
- **WHEN** matching starts
- **THEN** system queries all Concept labels from Neo4j (read-only)

#### Scenario: No Neo4j modification
- **WHEN** matching completes
- **THEN** Neo4j data remains unchanged

