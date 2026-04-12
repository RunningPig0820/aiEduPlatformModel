## ADDED Requirements

### Requirement: User can build vector index

The system SHALL provide a command-line script to build vector index for knowledge graph concepts.

#### Scenario: Build index successfully
- **WHEN** user runs `python build_vector_index.py`
- **THEN** system loads concepts from Neo4j, encodes them with embedding model, and saves index files to `output/vector_index/`

#### Scenario: Index files are created
- **WHEN** index building completes
- **THEN** system creates `kg_vectors.npy`, `kg_texts.json`, `kg_concepts.json`, and `index_meta.json`

#### Scenario: Index metadata is recorded
- **WHEN** index is saved
- **THEN** `index_meta.json` contains model_name, vector_dim, concept_count, created_at, and neo4j_checksum

### Requirement: User can check index status

The system SHALL provide a command to check existing index status.

#### Scenario: Check index status
- **WHEN** user runs `python build_vector_index.py --status`
- **THEN** system displays model_name, concept_count, created_at, and whether index is valid

#### Scenario: Index is outdated
- **WHEN** neo4j_checksum in metadata does not match current Neo4j data
- **THEN** system warns user that index is outdated and suggests rebuilding

### Requirement: User can force rebuild index

The system SHALL provide a command to force rebuild index.

#### Scenario: Force rebuild
- **WHEN** user runs `python build_vector_index.py --force`
- **THEN** system rebuilds index even if existing index appears valid

### Requirement: User can specify model

The system SHALL allow user to specify embedding model.

#### Scenario: Use custom model
- **WHEN** user runs `python build_vector_index.py --model BAAI/bge-large-zh`
- **THEN** system uses specified model instead of default `bge-small-zh-v1.5`