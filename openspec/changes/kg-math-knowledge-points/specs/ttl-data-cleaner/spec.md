## ADDED Requirements

### Requirement: TTL file parsing

The system SHALL provide a script to parse TTL (Turtle) RDF files and extract knowledge point entities.

#### Scenario: Parse math.ttl successfully

- **WHEN** the TTL parser script is executed against `ttl/math.ttl`
- **THEN** it SHALL extract all knowledge point entities (expected: 4,490 entities)

#### Scenario: Handle Unicode labels

- **WHEN** TTL file contains Unicode-encoded Chinese labels
- **THEN** the parser SHALL decode labels to readable Chinese characters

#### Scenario: Extract knowledge point properties

- **WHEN** a knowledge point entity is parsed
- **THEN** the parser SHALL extract the following properties: uri, name, description, type, subject

### Requirement: Data cleaning and standardization

The system SHALL clean and standardize extracted knowledge point data.

#### Scenario: Remove duplicate entities

- **WHEN** duplicate knowledge points with the same URI are found
- **THEN** the cleaner SHALL keep only one entity and discard duplicates

#### Scenario: Filter invalid entities

- **WHEN** knowledge points with missing required fields (uri, name) are found
- **THEN** the cleaner SHALL exclude these entities from the output

#### Scenario: Standardize property names

- **WHEN** knowledge point data is cleaned
- **THEN** all property names SHALL be standardized to English keys (uri, name, subject, type, etc.)

### Requirement: Type extraction

The system SHALL extract knowledge point type information from TTL data.

#### Scenario: Extract type from rdf:type

- **WHEN** a knowledge point has rdf:type annotation
- **THEN** the extractor SHALL map the type URI to Chinese type name (定义/性质/定理/公式/方法)

#### Scenario: Handle missing type

- **WHEN** a knowledge point has no type annotation
- **THEN** the extractor SHALL set type to null (未分类)

#### Scenario: Type coverage validation

- **WHEN** all knowledge points are processed
- **THEN** type coverage SHALL be at least 70% (entities with type field filled)

### Requirement: JSON output format

The system SHALL output cleaned data in JSON format.

#### Scenario: Output to JSON file

- **WHEN** cleaning process is complete
- **THEN** the script SHALL write the result to `math_knowledge_points.json`

#### Scenario: JSON structure validation

- **WHEN** JSON file is written
- **THEN** each knowledge point SHALL have: uri, name, subject, type, description fields