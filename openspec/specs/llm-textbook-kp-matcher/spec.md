# llm-textbook-kp-matcher Specification

## ADDED Requirements

### Requirement: Match textbook knowledge points with Neo4j knowledge points

The system SHALL match textbook knowledge points with KnowledgePoint nodes in Neo4j using LLM.

#### Scenario: Batch match by chapter
- **WHEN** the system matches knowledge points for a chapter
- **THEN** the system sends a single LLM request with all knowledge points from that chapter

#### Scenario: Return match results with confidence
- **WHEN** the LLM returns match results
- **THEN** each result includes matched_kp_id, matched_kp_name, and confidence score (0-1)

### Requirement: Use free LLM model

The system SHALL use free LLM model for matching.

#### Scenario: Use GLM-4-flash model
- **WHEN** the system performs matching
- **THEN** the system uses GLM-4-flash model via LLM Gateway

### Requirement: Support resume from interruption

The system SHALL support resume from interruption using StateDB.

#### Scenario: Resume after interruption
- **WHEN** the system is interrupted during matching
- **THEN** the system can resume from the last processed chapter on restart

### Requirement: Output match results to CSV

The system SHALL output match results to CSV file.

#### Scenario: Output match results
- **WHEN** matching is complete
- **THEN** the system outputs `textbook_kp_matches.csv` with columns: chapter_id, kp_name, matched_kp_id, confidence, status

### Requirement: Categorize match by confidence

The system SHALL categorize matches by confidence score.

#### Scenario: High confidence match
- **WHEN** confidence >= 0.9
- **THEN** status is set to "auto_mapped"

#### Scenario: Medium confidence match
- **WHEN** confidence is between 0.7 and 0.9
- **THEN** status is set to "needs_review"

#### Scenario: Low confidence match
- **WHEN** confidence < 0.7
- **THEN** status is set to "no_match"
