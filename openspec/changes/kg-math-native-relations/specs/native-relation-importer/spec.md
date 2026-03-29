## ADDED Requirements

### Requirement: Native relation import to Neo4j

The system SHALL import extracted native relations into Neo4j.

#### Scenario: Import RELATED_TO relations

- **WHEN** import script is executed
- **THEN** it SHALL import all RELATED_TO relations to Neo4j

#### Scenario: Import SUB_CATEGORY relations

- **WHEN** import script is executed
- **THEN** it SHALL import all SUB_CATEGORY relations to Neo4j

### Requirement: Node existence validation

The system SHALL validate that source and target nodes exist before creating relations.

#### Scenario: Skip relations with missing nodes

- **WHEN** a relation references a non-existent KnowledgePoint URI
- **THEN** the importer SHALL skip the relation and log a warning

#### Scenario: Log missing node statistics

- **WHEN** import process encounters missing nodes
- **THEN** the importer SHALL output statistics of skipped relations

### Requirement: Import validation

The system SHALL validate imported relation counts.

#### Scenario: Validate RELATED_TO count

- **WHEN** import is complete
- **THEN** validation script SHALL check RELATED_TO count equals expected value (9,870 minus skipped)

#### Scenario: Validate SUB_CATEGORY count

- **WHEN** import is complete
- **THEN** validation script SHALL check SUB_CATEGORY count equals expected value (328 minus skipped)

### Requirement: Import statistics output

The system SHALL output import statistics.

#### Scenario: Output import statistics

- **WHEN** import is complete
- **THEN** the script SHALL output: total imported, skipped (missing nodes), failed