## 1. Environment Setup

- [ ] 1.1 Create scripts directory `ai-edu-ai-service/scripts/kg_construction/`
- [ ] 1.2 Add Neo4j Python driver dependency to requirements.txt (`neo4j>=5.0.0`)
- [ ] 1.3 Create Neo4j connection configuration in `config/settings.py`

## 2. main.ttl 按学科拆分脚本

- [ ] 2.1 Create `split_main_ttl.py` with RDFLib setup
- [ ] 2.2 Implement URI prefix detection for each subject (`instance/{subject}#`)
- [ ] 2.3 Implement entity grouping by subject (biology, chemistry, chinese, geo, history, math, physics, politics)
- [ ] 2.4 Implement TTL header extraction (prefix definitions)
- [ ] 2.5 Implement per-subject TTL file generation
- [ ] 2.6 Create output directory `edukg/split/`
- [ ] 2.7 Add command-line interface with input/output path options
- [ ] 2.8 Add logging for split statistics (entities per subject)
- [ ] 2.9 Add validation: check total entities match original file

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
└── main-politics.ttl
```

## 3. Schema Creation Script

- [ ] 3.1 Create `create_neo4j_schema.py` with Neo4j connection setup
- [ ] 3.2 Implement node label creation (Subject, Stage, Grade, Textbook, Chapter, KnowledgePoint)
- [ ] 3.3 Implement unique constraints ONLY (KnowledgePoint.uri, Subject.code)
- [ ] 3.4 ~~Implement index creation~~ → **移到 kg-math-knowledge-points 数据导入后执行**
- [ ] 3.5 Add command-line interface with `--dry-run` option
- [ ] 3.6 Add logging for each schema operation

## 4. Schema Validation Script

- [ ] 4.1 Create `validate_schema.py` with Neo4j connection setup
- [ ] 4.2 Implement node labels verification (check all 6 labels exist)
- [ ] 4.3 ~~Implement indexes verification~~ → **移到 kg-math-knowledge-points 验证**
- [ ] 4.4 Implement constraints verification (check all constraints are active)
- [ ] 4.5 Implement validation report output (success/failure with counts)
- [ ] 4.6 Implement exit codes (0 for success, 1 for failure)
- [ ] 4.7 Add command-line interface

## 5. Testing

- [ ] 5.1 Write unit tests for `split_main_ttl.py` (test URI detection, entity grouping)
- [ ] 5.2 Write unit tests for `create_neo4j_schema.py` (test schema creation)
- [ ] 5.3 Write unit tests for `validate_schema.py` (test validation logic)
- [ ] 5.4 Create integration test script that runs split → schema creation → validation
- [ ] 5.5 Verify all tests pass with `pytest`

## 6. Documentation

- [ ] 6.1 Add inline docstrings to all functions
- [ ] 6.2 Create README.md in `scripts/kg_construction/` with usage instructions
- [ ] 6.3 Document the main.ttl split output structure