# entity-linking Specification

## Purpose
TBD - created by archiving change integrate-edukg-knowledge-graph. Update Purpose after archive.
## Requirements
### Requirement: Text Entity Recognition

The system SHALL recognize knowledge point entities from Chinese text using jieba segmentation and dictionary matching.

#### Scenario: Recognize single entity
- **WHEN** text contains a known knowledge point (e.g., "一元二次方程")
- **THEN** the system SHALL identify the entity and return its URI

#### Scenario: Recognize multiple entities
- **WHEN** text contains multiple knowledge points
- **THEN** the system SHALL identify all entities with their positions

#### Scenario: No entities found
- **WHEN** text contains no known knowledge points
- **THEN** the system SHALL return an empty result list

---

### Requirement: Subject-Context Entity Linking

The system SHALL support entity linking within a specific subject context.

#### Scenario: Link with subject context
- **WHEN** entity linking is performed with a specified subject (e.g., math)
- **THEN** the system SHALL only match entities from that subject

#### Scenario: Cross-subject disambiguation
- **WHEN** a term exists in multiple subjects (e.g., "函数" in math and programming)
- **THEN** the system SHALL use the subject context to disambiguate

---

### Requirement: Entity Position Tracking

The system SHALL return the character positions of recognized entities in the original text.

#### Scenario: Position accuracy
- **WHEN** an entity is recognized
- **THEN** the system SHALL return the start and end character indices

#### Scenario: Multiple occurrences
- **WHEN** an entity appears multiple times in the text
- **THEN** the system SHALL return all occurrence positions

---

### Requirement: Dictionary Management

The system SHALL support loading custom entity dictionaries per subject.

#### Scenario: Load subject dictionary
- **WHEN** the entity linker is initialized for a subject
- **THEN** the system SHALL load the corresponding dictionary into jieba

#### Scenario: Dictionary format
- **WHEN** a dictionary file is provided
- **THEN** the system SHALL support format: `entity_label 1` (jieba dict format)

---

### Requirement: Entity Context Enrichment

The system SHALL optionally enrich recognized entities with their knowledge graph context.

#### Scenario: Enrich with properties
- **WHEN** entity enrichment is requested
- **THEN** the system SHALL return entity properties from Neo4j

#### Scenario: Enrich with relationships
- **WHEN** entity enrichment is requested
- **THEN** the system SHALL return 1-hop neighbor entities

---

### Requirement: AI Chat Integration

The system SHALL provide entity linking results suitable for AI chat context injection.

#### Scenario: Format for LLM context
- **WHEN** entity linking is called from chat API
- **THEN** the system SHALL return a formatted context string for LLM prompt

#### Scenario: Batch text processing
- **WHEN** multiple text segments need entity linking
- **THEN** the system SHALL support batch processing for efficiency

