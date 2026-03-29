## ADDED Requirements

### Requirement: Teaches-before inference

The system SHALL infer TEACHES_BEFORE relations based on textbook chapter sequence.

#### Scenario: Infer within chapter

- **WHEN** knowledge points belong to the same chapter
- **THEN** the system SHALL infer TEACHES_BEFORE relations based on their order in the chapter

#### Scenario: Skip cross-chapter inference

- **WHEN** knowledge points belong to different chapters
- **THEN** the system SHALL NOT infer TEACHES_BEFORE relations across chapters

### Requirement: CSV output format

The system SHALL output inferred TEACHES_BEFORE relations in CSV format.

#### Scenario: Output to CSV file

- **WHEN** inference process is complete
- **THEN** the script SHALL write the result to `math_teaches_before.csv`

#### Scenario: CSV structure

- **WHEN** CSV file is written
- **THEN** each row SHALL have: source_uri, target_uri, chapter_name, order_position