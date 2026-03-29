## ADDED Requirements

### Requirement: Schema validation script

The system SHALL provide a validation script to verify that Neo4j schema is correctly created and ready for data import.

#### Scenario: Verify node labels exist

- **WHEN** the validation script is executed
- **THEN** it SHALL check that all 6 node labels exist: Subject, Stage, Grade, Textbook, Chapter, KnowledgePoint

#### Scenario: Verify indexes exist

- **WHEN** the validation script is executed
- **THEN** it SHALL check that all required indexes are created and online

#### Scenario: Verify constraints exist

- **WHEN** the validation script is executed
- **THEN** it SHALL check that all unique constraints are created and active

### Requirement: Validation report output

The validation script SHALL output a detailed report of schema status.

#### Scenario: Success report

- **WHEN** all schema elements are correctly created
- **THEN** the validation script SHALL output a success report with counts of labels, indexes, and constraints

#### Scenario: Failure report

- **WHEN** any schema element is missing or invalid
- **THEN** the validation script SHALL output a failure report listing missing elements and exit with non-zero status

### Requirement: Validation exit code

The validation script SHALL return appropriate exit codes for CI/CD integration.

#### Scenario: Success exit code

- **WHEN** validation passes
- **THEN** the script SHALL exit with code 0

#### Scenario: Failure exit code

- **WHEN** validation fails
- **THEN** the script SHALL exit with code 1

### Requirement: Idempotent validation

The validation script SHALL be idempotent and safe to run multiple times.

#### Scenario: Repeated validation

- **WHEN** validation script is executed multiple times
- **THEN** each execution SHALL produce the same result without modifying the schema