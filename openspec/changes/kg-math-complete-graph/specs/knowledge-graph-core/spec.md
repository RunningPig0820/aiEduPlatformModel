## MODIFIED Requirements

### Requirement: Support TextbookKnowledgePoint node type

The knowledge graph core SHALL support the TextbookKnowledgePoint node type.

#### Scenario: Create TextbookKnowledgePoint node
- **WHEN** a TextbookKnowledgePoint node is created
- **THEN** it has properties: id, name, chapter_id, matched_kp_id, confidence, status

#### Scenario: Query TextbookKnowledgePoint by chapter
- **WHEN** a query requests knowledge points for a chapter
- **THEN** the system returns all TextbookKnowledgePoint nodes with USES_KNOWLEDGE_POINT relationship from that chapter

### Requirement: Support new relationship types

The knowledge graph core SHALL support the following new relationship types:

- HAS_CHAPTER: Textbook → Chapter
- USES_KNOWLEDGE_POINT: Chapter → TextbookKnowledgePoint
- MAPPED_TO: TextbookKnowledgePoint → KnowledgePoint

#### Scenario: Query learning path for knowledge point
- **WHEN** a query requests the learning path for a KnowledgePoint
- **THEN** the system can traverse MAPPED_TO ← TextbookKnowledgePoint ← Chapter ← Textbook to find the textbook context