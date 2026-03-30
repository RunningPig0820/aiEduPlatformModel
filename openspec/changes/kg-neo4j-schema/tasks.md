## 1. Environment Setup

- [ ] 1.1 Create scripts directory `ai-edu-ai-service/scripts/kg_construction/`
- [ ] 1.2 Add Neo4j Python driver dependency to requirements.txt (`neo4j>=5.0.0`)
- [ ] 1.3 Create Neo4j connection configuration in `config/settings.py`

## 2. Schema Creation Script

- [ ] 2.1 Create `create_neo4j_schema.py` with Neo4j connection setup
- [ ] 2.2 Implement node label creation (Subject, Stage, Grade, Textbook, Chapter, KnowledgePoint)
- [ ] 2.3 Implement unique constraints ONLY (KnowledgePoint.uri, Subject.code)
- [ ] 2.4 ~~Implement index creation~~ → **移到 kg-math-knowledge-points 数据导入后执行**
- [ ] 2.5 Add command-line interface with `--dry-run` option
- [ ] 2.6 Add logging for each schema operation

## 3. Schema Validation Script

- [ ] 3.1 Create `validate_schema.py` with Neo4j connection setup
- [ ] 3.2 Implement node labels verification (check all 6 labels exist)
- [ ] 3.3 ~~Implement indexes verification~~ → **移到 kg-math-knowledge-points 验证**
- [ ] 3.4 Implement constraints verification (check all constraints are active)
- [ ] 3.5 Implement validation report output (success/failure with counts)
- [ ] 3.6 Implement exit codes (0 for success, 1 for failure)
- [ ] 3.7 Add command-line interface

## 4. Testing

- [ ] 4.1 Write unit tests for `create_neo4j_schema.py` (test schema creation)
- [ ] 4.2 Write unit tests for `validate_schema.py` (test validation logic)
- [ ] 4.3 Create integration test script that runs schema creation then validation
- [ ] 4.4 Verify all tests pass with `pytest`

## 5. Documentation

- [ ] 5.1 Add inline docstrings to all functions
- [ ] 5.2 Create README.md in `scripts/kg_construction/` with usage instructions