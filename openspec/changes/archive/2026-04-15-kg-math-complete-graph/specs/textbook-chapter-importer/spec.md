## ADDED Requirements

### Requirement: Import Textbook nodes to Neo4j

The system SHALL import Textbook nodes to Neo4j.

#### Scenario: Import all textbooks
- **WHEN** the system imports textbook data
- **THEN** 24 Textbook nodes are created with properties: id, name, stage, grade, semester, publisher

#### Scenario: Prevent duplicate textbooks
- **WHEN** a Textbook with the same id already exists
- **THEN** the system skips creation and logs a warning

### Requirement: Import Chapter nodes to Neo4j

The system SHALL import Chapter nodes to Neo4j.

#### Scenario: Import all chapters
- **WHEN** the system imports chapter data
- **THEN** approximately 300 Chapter nodes are created with properties: id, name, order

### Requirement: Create HAS_CHAPTER relationships

The system SHALL create HAS_CHAPTER relationships between Textbook and Chapter.

#### Scenario: Link chapters to textbook
- **WHEN** a Chapter belongs to a Textbook
- **THEN** a HAS_CHAPTER relationship is created from Textbook to Chapter

### Requirement: Create chapter hierarchy

The system SHALL create chapter hierarchy when sections exist.

#### Scenario: Create section as sub-chapter
- **WHEN** a chapter has sections
- **THEN** each section is created as a Chapter node with HAS_CHAPTER relationship to parent chapter