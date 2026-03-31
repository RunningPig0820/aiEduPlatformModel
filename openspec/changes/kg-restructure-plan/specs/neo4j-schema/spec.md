## MODIFIED Requirements

### Requirement: Neo4j schema initialization

The system SHALL provide a script to initialize Neo4j schema with defined node labels, relationships, indexes, and constraints for knowledge graph storage.

#### Scenario: Create node labels successfully

- **WHEN** the schema initialization script is executed against a running Neo4j instance
- **THEN** the following node labels SHALL be created: Subject, Stage, Grade, Textbook, Chapter, KnowledgePoint, TextbookKnowledgePoint

## ADDED Requirements

### Requirement: TextbookKnowledgePoint node definition

The system SHALL define TextbookKnowledgePoint node for storing textbook-specific knowledge point information.

#### Scenario: TextbookKnowledgePoint properties defined

- **WHEN** TextbookKnowledgePoint node is created
- **THEN** it SHALL support the following properties: id (STRING), name (STRING), chapter_id (STRING), matched_kp_id (STRING), confidence (FLOAT), status (STRING)

### Requirement: Textbook-Chapter relationship types

The system SHALL define relationship types for textbook-chapter hierarchy.

#### Scenario: HAS_CHAPTER relationship type defined

- **WHEN** the schema initialization script is executed
- **THEN** HAS_CHAPTER relationship type SHALL be available for Textbook → Chapter hierarchy

### Requirement: Knowledge point mapping relationship types

The system SHALL define relationship types for knowledge point mapping.

#### Scenario: USES_KNOWLEDGE_POINT relationship type defined

- **WHEN** the schema initialization script is executed
- **THEN** USES_KNOWLEDGE_POINT relationship type SHALL be available for Chapter → TextbookKnowledgePoint

#### Scenario: MAPPED_TO relationship type defined

- **WHEN** the schema initialization script is executed
- **THEN** MAPPED_TO relationship type SHALL be available for TextbookKnowledgePoint → KnowledgePoint