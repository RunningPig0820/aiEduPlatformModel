## ADDED Requirements

### Requirement: LLM recommends match candidates

The system SHALL provide an API endpoint to recommend EduKG match candidates for a given textbook knowledge point.

#### Scenario: API endpoint exists
- **WHEN** calling POST /api/kp-match/recommend
- **THEN** endpoint accepts request body with textbook_kp_name and normalized_name

#### Scenario: Return top 5 candidates
- **WHEN** LLM recommendation succeeds
- **THEN** response contains top 5 candidates sorted by confidence

#### Scenario: Candidate response format
- **WHEN** returning candidates
- **THEN** each candidate includes: kg_uri, kg_name, similarity, confidence, reason

### Requirement: Reuse existing matching logic

The system SHALL reuse KPMatcher vector retrieval and LLM voting logic for recommendations.

#### Scenario: Use prebuilt vector index
- **WHEN** recommending candidates
- **THEN** system uses existing bge-small-zh-v1.5 vector index

#### Scenario: Apply dual model voting
- **WHEN** evaluating candidates
- **THEN** system applies GLM-4-flash + DeepSeek voting for confidence score

### Requirement: Handle recommendation errors

The system SHALL handle LLM call failures gracefully.

#### Scenario: LLM timeout fallback
- **WHEN** LLM call exceeds 30 seconds
- **THEN** system returns vector similarity only without voting confidence

#### Scenario: Empty candidates response
- **WHEN** no candidates found above threshold
- **THEN** system returns empty candidate list with reason="no_match_found"