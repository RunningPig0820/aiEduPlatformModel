## ADDED Requirements

### Requirement: Prerequisite relation import to Neo4j

The system SHALL import inferred prerequisite relations into Neo4j.

#### Scenario: Import TEACHES_BEFORE relations

- **WHEN** import script is executed
- **THEN** it SHALL import all TEACHES_BEFORE relations

#### Scenario: Import PREREQUISITE relations

- **WHEN** import script is executed
- **THEN** it SHALL import all PREREQUISITE relations

#### Scenario: Import PREREQUISITE_CANDIDATE relations

- **WHEN** import script is executed
- **THEN** it SHALL import all PREREQUISITE_CANDIDATE relations

#### Scenario: Import PREREQUISITE_ON relations

- **WHEN** import script is executed
- **THEN** it SHALL import all PREREQUISITE_ON relations (EduKG standard)

### Requirement: DAG validation

The system SHALL validate that PREREQUISITE relations form a valid DAG (no cycles).

#### Scenario: Validate no cycles

- **WHEN** import is complete
- **THEN** validation script SHALL check no cycles exist in PREREQUISITE relations

#### Scenario: Report cycle count

- **WHEN** cycles are detected
- **THEN** validation script SHALL output cycle count and involved knowledge points

### Requirement: Import validation

The system SHALL validate imported relation counts.

#### Scenario: Validate relation counts

- **WHEN** import is complete
- **THEN** validation script SHALL check all relation types counts match expected values

### Requirement: Quality metrics

The system SHALL calculate and report quality metrics.

#### Scenario: Report quality metrics

- **WHEN** validation is complete
- **THEN** the script SHALL output: coverage rate, average chain length, confidence distribution