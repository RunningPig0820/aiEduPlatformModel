## ADDED Requirements

### Requirement: Definition dependency extraction

The system SHALL extract prerequisite dependencies from knowledge point definition text.

#### Scenario: Match knowledge point names in definition

- **WHEN** a knowledge point definition contains other knowledge point names
- **THEN** the extractor SHALL create dependency relations

#### Scenario: Filter subject-specific matches

- **WHEN** matching knowledge point names
- **THEN** the extractor SHALL only match names within the same subject

#### Scenario: Set minimum match length

- **WHEN** a knowledge point name is shorter than 3 characters
- **THEN** the extractor SHALL skip matching to reduce noise

### Requirement: CSV output format

The system SHALL output extracted definition dependencies in CSV format.

#### Scenario: Output to CSV file

- **WHEN** extraction process is complete
- **THEN** the script SHALL write the result to `math_definition_deps.csv`

#### Scenario: CSV structure

- **WHEN** CSV file is written
- **THEN** each row SHALL have: source_uri, target_uri, matched_name, evidence_type