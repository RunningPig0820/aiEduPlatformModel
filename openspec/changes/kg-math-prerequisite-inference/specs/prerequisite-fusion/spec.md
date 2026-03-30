## ADDED Requirements

### Requirement: Prerequisite relation fusion

The system SHALL fuse multiple evidence sources to generate final prerequisite relations.

#### Scenario: Fuse definition dependencies

- **WHEN** definition dependencies are available
- **THEN** the fusion script SHALL include them in final relations

#### Scenario: Fuse LLM inference results

- **WHEN** LLM inference results are available
- **THEN** the fusion script SHALL include PREREQUISITE relations in final relations

#### Scenario: Keep PREREQUISITE_CANDIDATE

- **WHEN** LLM inference produces PREREQUISITE_CANDIDATE relations
- **THEN** the fusion script SHALL include them separately

### Requirement: EduKG standard relation

The system SHALL generate EduKG standard relation (PREREQUISITE_ON) alongside PREREQUISITE.

#### Scenario: Create PREREQUISITE_ON relations

- **WHEN** a PREREQUISITE relation is created
- **THEN** the fusion script SHALL also create PREREQUISITE_ON relation for EduKG compatibility

### Requirement: Deduplication

The system SHALL deduplicate relations from multiple sources.

#### Scenario: Deduplicate by source-target pair

- **WHEN** the same source-target pair appears in multiple evidence sources
- **THEN** the fusion script SHALL keep only one relation with highest confidence

### Requirement: CSV output format

The system SHALL output fused relations in CSV format.

#### Scenario: Output to CSV file

- **WHEN** fusion process is complete
- **THEN** the script SHALL write the result to `math_final_prereq.csv`

#### Scenario: CSV structure

- **WHEN** CSV file is written
- **THEN** each row SHALL have: source_uri, target_uri, relation_type, confidence, evidence_sources