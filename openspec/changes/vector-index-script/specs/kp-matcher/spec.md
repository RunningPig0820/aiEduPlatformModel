## ADDED Requirements

### Requirement: KPMatcher can load prebuilt vector index

The system SHALL allow KPMatcher to load prebuilt vector index from files instead of lazy initialization.

#### Scenario: Load prebuilt index
- **WHEN** user runs `python match_textbook_kp.py --use-prebuilt-index`
- **THEN** KPMatcher loads vector index from `output/vector_index/` directory

#### Scenario: Prebuilt index is missing
- **WHEN** user runs with `--use-prebuilt-index` but index files do not exist
- **THEN** system warns user and falls back to lazy initialization or difflib

#### Scenario: Prebuilt index is outdated
- **WHEN** neo4j_checksum in index metadata does not match current Neo4j data
- **THEN** system warns user and suggests running `build_vector_index.py`

### Requirement: KPMatcher can force build index

The system SHALL allow user to force rebuild index during matching.

#### Scenario: Force build during match
- **WHEN** user runs `python match_textbook_kp.py --force-build-index`
- **THEN** system rebuilds vector index before matching

### Requirement: KPMatcher can disable vector retrieval

The system SHALL allow user to disable vector retrieval and use difflib.

#### Scenario: Disable vector retrieval
- **WHEN** user runs `python match_textbook_kp.py --no-vector-retrieval`
- **THEN** KPMatcher uses difflib for candidate retrieval instead of vector search