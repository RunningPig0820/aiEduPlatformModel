## 1. Environment Setup

- [x] 1.1 Create scripts directory `edukg/scripts/kg_construction/`
- [x] 1.2 Add Neo4j Python driver dependency to requirements.txt (`neo4j>=5.0.0`)
- [x] 1.3 Create Neo4j connection configuration in `config/settings.py`

## 2. main.ttl 按学科拆分脚本

- [x] 2.1 Create `split_main_ttl.py` with RDFLib setup
- [x] 2.2 Implement URI prefix detection for each subject (`instance/{subject}#`)
- [x] 2.3 Implement entity grouping by subject (biology, chemistry, chinese, geo, history, math, physics, politics)
- [x] 2.4 Implement TTL header extraction (prefix definitions)
- [x] 2.5 Implement per-subject TTL file generation
- [x] 2.6 Create output directory `edukg/split/`
- [x] 2.7 Add command-line interface with input/output path options
- [x] 2.8 Add logging for split statistics (entities per subject)
- [x] 2.9 Add validation: check total entities match original file

**输出文件**:
```
edukg/split/
├── main-biology.ttl
├── main-chemistry.ttl
├── main-chinese.ttl
├── main-geo.ttl
├── main-history.ttl
├── main-math.ttl
├── main-physics.ttl
├── main-politics.ttl
└── main-unknown.ttl
```

## 2.5. material.ttl 按学科拆分脚本

- [x] 2.5.1 Create `split_material_ttl.py` with RDFLib setup
- [x] 2.5.2 Implement textbook entity detection (URI matches `textbook#I{N}`)
- [x] 2.5.3 Implement subject keyword extraction from textbook name (P4 property)
- [x] 2.5.4 Define subject keyword mapping ("数学" → math, "物理" → physics, etc.)
- [x] 2.5.5 Implement entity grouping by extracted subject
- [x] 2.5.6 Handle related entities (chapters) - group with parent textbook via relation propagation
- [x] 2.5.7 Implement per-subject TTL file generation
- [x] 2.5.8 Add command-line interface with input/output path options
- [x] 2.5.9 Add logging for split statistics (textbooks per subject)
- [x] 2.5.10 Add validation: check total triples match original file

**输出文件**:
```
edukg/split/
├── material-math.ttl
├── material-physics.ttl
├── material-chemistry.ttl
├── material-biology.ttl
├── material-history.ttl
├── material-geo.ttl
├── material-chinese.ttl
├── material-english.ttl
├── material-politics.ttl
└── material-unknown.ttl
```

## 3. Schema Creation Script

- [x] 3.1 Create `create_neo4j_schema.py` with Neo4j connection setup
- [x] 3.2 Implement node label creation (Subject, Stage, Grade, Textbook, Chapter, KnowledgePoint)
- [x] 3.3 Implement unique constraints ONLY (KnowledgePoint.uri, Subject.code, Textbook.isbn)
- [x] 3.4 ~~Implement index creation~~ → **移到 kg-math-knowledge-points 数据导入后执行**
- [x] 3.5 Add command-line interface with `--dry-run` option
- [x] 3.6 Add logging for each schema operation

## 4. Schema Validation Script

- [x] 4.1 Create `validate_schema.py` with Neo4j connection setup
- [x] 4.2 Implement node labels verification (check all 6 labels exist)
- [x] 4.3 ~~Implement indexes verification~~ → **移到 kg-math-knowledge-points 验证**
- [x] 4.4 Implement constraints verification (check all 3 constraints are active)
- [x] 4.5 Implement validation report output (success/failure with counts)
- [x] 4.6 Implement exit codes (0 for success, 1 for failure)
- [x] 4.7 Add command-line interface

## 5. Testing

- [x] 5.1 Write unit tests for `split_main_ttl.py` (test URI detection, entity grouping)
- [x] 5.2 Write unit tests for `split_material_ttl.py` (test subject keyword extraction, textbook grouping)
- [x] 5.3 Write unit tests for `create_neo4j_schema.py` (test schema creation)
- [x] 5.4 Write unit tests for `validate_schema.py` (test validation logic)
- [x] 5.5 Create integration test script that runs split → schema creation → validation
- [x] 5.6 Verify all tests pass with `pytest`

## 6. Documentation

- [x] 6.1 Add inline docstrings to all functions
- [x] 6.2 Create README.md in `scripts/kg_construction/` with usage instructions
- [x] 6.3 Document the main.ttl split output structure
- [x] 6.4 Document the material.ttl split output structure