## 1. Environment Setup

- [ ] 1.1 Create output directory for relation files (`output/relations/`)
- [ ] 1.2 Verify knowledge points exist in Neo4j (dependency on kg-math-knowledge-points change)

## 2. Native Relation Extraction Script

- [ ] 2.1 Create `extract_native_relations.py` with RDFLib setup
- [ ] 2.2 Implement TTL file parsing (`relations/math_relations.ttl`)
- [ ] 2.3 Implement relateTo extraction (expected: 9,870 relations)
- [ ] 2.4 Implement subCategory extraction (expected: 328 relations)
- [ ] 2.5 Implement relation type mapping (relateTo → RELATED_TO, subCategory → SUB_CATEGORY)
- [ ] 2.6 Implement bidirectional relation deduplication
- [ ] 2.7 Implement CSV output (`math_native_relations.csv`)
- [ ] 2.8 Add extraction statistics logging
- [ ] 2.9 Add command-line interface with input/output path options

## 3. Native Relation Import Script

- [ ] 3.1 Create `import_native_relations_to_neo4j.py` with Neo4j driver setup
- [ ] 3.2 Implement CSV file loading
- [ ] 3.3 Implement RELATED_TO relation creation (MATCH source/target nodes first)
- [ ] 3.4 Implement SUB_CATEGORY relation creation
- [ ] 3.5 Implement node existence validation (skip if node missing)
- [ ] 3.6 Implement import statistics output (imported, skipped, failed)
- [ ] 3.7 Add command-line interface with Neo4j connection options
- [ ] 3.8 Add progress logging

## 4. Data Validation Script

- [ ] 4.1 Create `validate_native_relations.py`
- [ ] 4.2 Implement RELATED_TO count validation (expected: 9,870 minus skipped)
- [ ] 4.3 Implement SUB_CATEGORY count validation (expected: 328 minus skipped)
- [ ] 4.4 Implement validation report output
- [ ] 4.5 Add exit codes (0: success, 1: failure)

## 5. Testing

- [ ] 5.1 Write unit tests for `extract_native_relations.py` (mock TTL parsing)
- [ ] 5.2 Write unit tests for `import_native_relations_to_neo4j.py` (mock Neo4j driver)
- [ ] 5.3 Write unit tests for bidirectional deduplication logic
- [ ] 5.4 Create integration test script (extract → import → validate)
- [ ] 5.5 Verify all tests pass with `pytest`

## 6. Documentation

- [ ] 6.1 Add inline docstrings to all functions
- [ ] 6.2 Update README.md with native relation workflow