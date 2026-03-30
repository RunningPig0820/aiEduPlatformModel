## ADDED Requirements

### Requirement: Neo4j schema initialization

The system SHALL provide a script to initialize Neo4j schema with defined node labels, relationships, indexes, and constraints for knowledge graph storage.

#### Scenario: Create node labels successfully

- **WHEN** the schema initialization script is executed against a running Neo4j instance
- **THEN** the following node labels SHALL be created: Subject, Stage, Grade, Textbook, Chapter, KnowledgePoint

#### Scenario: Create indexes for query performance

- **WHEN** the schema initialization script is executed
- **THEN** indexes SHALL be created for KnowledgePoint properties: name, uri, subject, grade, and compound index for (subject, grade)

#### Scenario: Create unique constraints

- **WHEN** the schema initialization script is executed
- **THEN** unique constraints SHALL be created for KnowledgePoint.uri and Subject.code

### Requirement: Relationship types definition

The system SHALL define relationship types in Neo4j schema without creating any relationship data.

#### Scenario: Hierarchy relationship types defined

- **WHEN** the schema initialization script is executed
- **THEN** the following hierarchy relationship types SHALL be available: HAS_STAGE, HAS_GRADE, USE_TEXTBOOK, HAS_CHAPTER, HAS_KNOWLEDGE_POINT

#### Scenario: Knowledge dependency relationship types defined

- **WHEN** the schema initialization script is executed
- **THEN** the following dependency relationship types SHALL be available: PREREQUISITE, TEACHES_BEFORE, PREREQUISITE_ON, PREREQUISITE_CANDIDATE

#### Scenario: Knowledge association relationship types defined

- **WHEN** the schema initialization script is executed
- **THEN** the following association relationship types SHALL be available: RELATED_TO, SUB_CATEGORY

### Requirement: KnowledgePoint node properties

The system SHALL define KnowledgePoint node with standardized properties.

#### Scenario: Core properties defined

- **WHEN** KnowledgePoint node is created
- **THEN** it SHALL support the following properties: uri (STRING), external_id (STRING), name (STRING), subject (STRING), stage (STRING), grade (STRING), chapter (STRING), type (STRING), difficulty (INTEGER), description (STRING), source (STRING)

#### Scenario: Property types validated

- **WHEN** a KnowledgePoint node is inserted with invalid property types
- **THEN** the insertion SHALL fail with type validation error

### Requirement: Reusability across subjects

The schema SHALL be reusable for all 9 subjects (math, physics, chemistry, biology, history, chinese, geography, politics, english).

#### Scenario: Schema shared across subjects

- **WHEN** schema is initialized once
- **THEN** all subsequent data imports for any subject SHALL use the same schema structure