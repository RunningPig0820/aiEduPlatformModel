# knowledge-graph-core Specification

## Purpose
TBD - created by archiving change integrate-edukg-knowledge-graph. Update Purpose after archive.
## Requirements
### Requirement: Neo4j Connection Management

The system SHALL provide a Neo4j connection manager that supports connection pooling, automatic reconnection, and health checks.

#### Scenario: Successful connection establishment
- **WHEN** the application starts with valid Neo4j credentials
- **THEN** the system SHALL establish a connection pool to Neo4j

#### Scenario: Connection failure handling
- **WHEN** Neo4j is unavailable
- **THEN** the system SHALL log the error and retry with exponential backoff
- **AND** the system SHALL return a clear error message to the caller

#### Scenario: Health check endpoint
- **WHEN** a health check is requested
- **THEN** the system SHALL return Neo4j connection status

---

### Requirement: TTL File Import

The system SHALL support importing EDUKG TTL (RDF Turtle) files into Neo4j using the n10s plugin.

#### Scenario: Successful TTL import
- **WHEN** a valid TTL file is provided for import
- **THEN** the system SHALL parse and import all entities and relationships into Neo4j
- **AND** the system SHALL log the number of imported entities

#### Scenario: Invalid TTL file handling
- **WHEN** an invalid or corrupted TTL file is provided
- **THEN** the system SHALL reject the import and return an error message

#### Scenario: Incremental import
- **WHEN** importing data for a specific subject (e.g., math)
- **THEN** the system SHALL only import entities for that subject

---

### Requirement: Entity Query by URI

The system SHALL support querying knowledge graph entities by URI.

#### Scenario: Query existing entity
- **WHEN** querying an entity by its URI
- **THEN** the system SHALL return the entity's label, properties, and relationships

#### Scenario: Query non-existent entity
- **WHEN** querying a URI that does not exist
- **THEN** the system SHALL return a 404 response

---

### Requirement: Entity Query by Label

The system SHALL support fuzzy search for entities by label (name).

#### Scenario: Exact match search
- **WHEN** searching for entities with an exact label
- **THEN** the system SHALL return all matching entities

#### Scenario: Fuzzy match search
- **WHEN** searching for entities with a partial label
- **THEN** the system SHALL return entities with similar labels (fuzzy matching)

#### Scenario: Subject-filtered search
- **WHEN** searching within a specific subject (e.g., math)
- **THEN** the system SHALL only return entities from that subject

---

### Requirement: Relationship Query

The system SHALL support querying relationships for a given entity.

#### Scenario: Query outgoing relationships
- **WHEN** querying outgoing relationships for an entity
- **THEN** the system SHALL return all entities connected via outgoing edges

#### Scenario: Query incoming relationships
- **WHEN** querying incoming relationships for an entity
- **THEN** the system SHALL return all entities connected via incoming edges

#### Scenario: Query by relationship type
- **WHEN** querying a specific relationship type (e.g., SUBCLASS_OF)
- **THEN** the system SHALL filter results by that relationship type

---

### Requirement: Subject Hierarchy Query

The system SHALL support querying the class/subject hierarchy.

#### Scenario: Query subject classes
- **WHEN** querying classes for a subject (e.g., math)
- **THEN** the system SHALL return all class nodes for that subject

#### Scenario: Query class hierarchy
- **WHEN** querying the hierarchy under a class
- **THEN** the system SHALL return parent and child classes

---

### Requirement: Configuration Management

The system SHALL load Neo4j connection settings from environment variables.

#### Scenario: Load from environment
- **WHEN** the application starts
- **THEN** the system SHALL read NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD from environment

#### Scenario: Missing configuration
- **WHEN** required environment variables are not set
- **THEN** the system SHALL raise a clear configuration error

