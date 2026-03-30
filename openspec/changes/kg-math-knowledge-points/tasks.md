## 1. Environment Setup

- [ ] 1.1 Add RDFLib dependency to requirements.txt (`rdflib>=6.0.0`)
- [ ] 1.2 Create output directory for intermediate files (`scripts/kg_construction/output/`)
- [ ] 1.3 Verify Neo4j schema exists (dependency on kg-neo4j-schema change)

## 2. TTL Data Cleaning Script

- [ ] 2.1 Create `clean_math_data.py` with RDFLib setup
- [ ] 2.2 Implement TTL file parsing (`ttl/math.ttl`)
- [ ] 2.3 Implement Unicode label decoding
- [ ] 2.4 Implement knowledge point extraction (uri, name, description, type)
- [ ] 2.5 Implement type mapping (rdf:type → 中文类型名)
- [ ] 2.6 Implement deduplication by URI
- [ ] 2.7 Implement invalid data filtering (missing uri/name)
- [ ] 2.8 Implement JSON output (`math_knowledge_points.json`)
- [ ] 2.9 Add type coverage validation (≥70%)
- [ ] 2.10 Add command-line interface with input/output path options
- [ ] 2.11 Add logging for extraction statistics

## 3. Textbook Info Extraction Script

- [ ] 3.1 Create `extract_textbook_info.py` with RDFLib setup
- [ ] 3.2 Implement main.ttl parsing for textbook entities
- [ ] 3.3 Implement textbook-grade mapping table
- [ ] 3.4 Implement label matching algorithm (knowledge point → chapter)
- [ ] 3.5 Implement grade inference logic
- [ ] 3.6 Implement matching coverage validation (≥80%)
- [ ] 3.7 Implement JSON output (`math_textbook_mapping.json`)
- [ ] 3.8 Add command-line interface with input/output path options
- [ ] 3.9 Add logging for matching statistics

## 4. Data Merge Script

- [ ] 4.1 Create `merge_math_data.py`
- [ ] 4.2 Implement URI-based merging logic
- [ ] 4.3 Implement grade/chapter field filling
- [ ] 4.4 Implement final data structure (all required fields)
- [ ] 4.5 Implement JSON output (`math_final_data.json`)
- [ ] 4.6 Add command-line interface with input files options
- [ ] 4.7 Add validation for merged data completeness

## 5. Neo4j Import Script

- [ ] 5.1 Create `import_math_kp_to_neo4j.py` with Neo4j driver setup
- [ ] 5.2 Implement hierarchy nodes creation (Subject, Stage, Grade, Textbook, Chapter)
- [ ] 5.3 Implement batch import using UNWIND Cypher
- [ ] 5.4 Implement HAS_KNOWLEDGE_POINT relationships creation
- [ ] 5.5 Implement transaction-based import (rollback on failure)
- [ ] 5.6 Add command-line interface with Neo4j connection options
- [ ] 5.7 Add progress logging (imported count)
- [ ] 5.8 Implement import statistics output (node counts, relationship counts)

## 6. Performance Index Creation (数据导入后执行)

- [ ] 6.1 Create `create_kp_indexes.py` for post-import index creation
- [ ] 6.2 Implement single-field indexes (name, uri, subject, grade)
- [ ] 6.3 Implement composite index (subject + grade)
- [ ] 6.4 Add `--dry-run` option for preview
- [ ] 6.5 Add index verification (check all indexes are online)
- [ ] 6.6 Add logging for index creation progress
- [ ] 6.7 Update import script to call index creation after data import

**索引创建 Cypher**:
```cypher
// 单字段索引
CREATE INDEX IF NOT EXISTS kp_name_idx FOR (n:KnowledgePoint) ON (n.name)
CREATE INDEX IF NOT EXISTS kp_uri_idx FOR (n:KnowledgePoint) ON (n.uri)
CREATE INDEX IF NOT EXISTS kp_subject_idx FOR (n:KnowledgePoint) ON (n.subject)
CREATE INDEX IF NOT EXISTS kp_grade_idx FOR (n:KnowledgePoint) ON (n.grade)

// 复合索引
CREATE INDEX IF NOT EXISTS kp_subject_grade_idx FOR (n:KnowledgePoint) ON (n.subject, n.grade)
```

## 7. Data Validation Script

- [ ] 7.1 Create `validate_math_import.py`
- [ ] 7.2 Implement node count validation (expected: 4,490)
- [ ] 7.3 Implement URI uniqueness validation
- [ ] 7.4 Implement required fields validation (name, uri not null)
- [ ] 7.5 Implement type coverage validation (≥70%)
- [ ] 7.6 Implement index online validation (all 5 indexes online)
- [ ] 7.7 Implement validation report output
- [ ] 7.8 Add exit codes (0: success, 1: failure)

## 8. Testing

- [ ] 8.1 Write unit tests for `clean_math_data.py` (mock TTL parsing)
- [ ] 8.2 Write unit tests for `extract_textbook_info.py` (mock matching)
- [ ] 8.3 Write unit tests for `merge_math_data.py` (test merging logic)
- [ ] 8.4 Write unit tests for `import_math_kp_to_neo4j.py` (mock Neo4j driver)
- [ ] 8.5 Write unit tests for `create_kp_indexes.py` (mock index creation)
- [ ] 8.6 Create integration test script (clean → extract → merge → import → create indexes → validate)
- [ ] 8.7 Verify all tests pass with `pytest`

## 9. Documentation

- [ ] 9.1 Add inline docstrings to all functions
- [ ] 9.2 Update README.md with math data cleaning workflow
- [ ] 9.3 Add sample output files for reference