## ADDED Requirements

### Requirement: Native relation extraction from TTL

The system SHALL provide a script to extract native relations (relateTo, subCategory) from TTL files.

#### Scenario: Extract relateTo relations

- **WHEN** the extraction script is executed against `relations/math_relations.ttl`
- **THEN** it SHALL extract all relateTo relations (expected: 9,870 relations)

#### Scenario: Extract subCategory relations

- **WHEN** the extraction script is executed
- **THEN** it SHALL extract all subCategory relations (expected: 328 relations)

#### Scenario: Decode relation URIs

- **WHEN** relation URIs contain Unicode encoding
- **THEN** the extractor SHALL decode URIs to readable format

### Requirement: Relation type mapping

The system SHALL map TTL relation predicates to Neo4j relation types correctly.

#### Scenario: Map relateTo to RELATED_TO

- **WHEN** a relateTo predicate is found
- **THEN** the extractor SHALL map it to RELATED_TO relation type

#### Scenario: Map subCategory to SUB_CATEGORY

- **WHEN** a subCategory predicate is found
- **THEN** the extractor SHALL map it to SUB_CATEGORY relation type

### Requirement: Bidirectional relation deduplication

The system SHALL deduplicate bidirectional relations to avoid redundancy.

#### Scenario: Deduplicate bidirectional relations

- **WHEN** both (A, B) and (B, A) relations exist
- **THEN** the extractor SHALL keep only one relation (A, B) or (B, A)

### Requirement: CSV output format

The system SHALL output extracted relations in CSV format.

#### Scenario: Output to CSV file

- **WHEN** extraction process is complete
- **THEN** the script SHALL write the result to `math_native_relations.csv`

#### Scenario: CSV structure validation

- **WHEN** CSV file is written
- **THEN** each row SHALL have: source_uri, target_uri, relation_type