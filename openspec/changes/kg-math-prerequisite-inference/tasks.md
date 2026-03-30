## 1. Environment Setup

- [ ] 1.1 Verify knowledge points exist in Neo4j (dependency on kg-math-native-relations change)
- [ ] 1.2 Verify native relations exist in Neo4j
- [ ] 1.3 Add prerequisite_inference scene to LLM Gateway config

## 2. Teaches-Before Inference Script

- [ ] 2.1 Create `infer_teaches_before.py`
- [ ] 2.2 Implement chapter-based sequence inference (within chapter only)
- [ ] 2.3 Implement knowledge point order extraction from textbook data
- [ ] 2.4 Implement CSV output (`math_teaches_before.csv`)
- [ ] 2.5 Add statistics logging (total inferred, per chapter counts)
- [ ] 2.6 Add command-line interface

## 3. Definition Dependency Extraction Script

- [ ] 3.1 Create `extract_definition_deps.py`
- [ ] 3.2 Implement definition text loading from final data JSON
- [ ] 3.3 Implement knowledge point name matching in definitions
- [ ] 3.4 Implement subject-specific filtering (only match math knowledge points)
- [ ] 3.5 Implement minimum match length filter (≥3 characters)
- [ ] 3.6 Implement CSV output (`math_definition_deps.csv`)
- [ ] 3.7 Add statistics logging (total extracted, coverage)
- [ ] 3.8 Add command-line interface

## 4. LLM Prerequisite Inference Script

- [ ] 4.1 Create `infer_prerequisites_llm.py`
- [ ] 4.2 Implement LLM Gateway integration
- [ ] 4.3 Implement prompt template (distinguish teaching order vs learning dependency)
- [ ] 4.4 Implement GLM-4-flash model call
- [ ] 4.5 Implement DeepSeek model call
- [ ] 4.6 Implement multi-model voting logic
- [ ] 4.7 Implement confidence threshold classification (≥0.8 → PREREQUISITE, <0.8 → PREREQUISITE_CANDIDATE)
- [ ] 4.8 Implement batch processing (configurable batch size)
- [ ] 4.9 Implement rate limiting and retry logic
- [ ] 4.10 Implement CSV output (`math_llm_prereq.csv`)
- [ ] 4.11 Add progress logging (processed count, LLM call count)
- [ ] 4.12 Add cost estimation logging
- [ ] 4.13 Add command-line interface with batch size and rate limit options

## 5. Prerequisite Fusion Script

- [ ] 5.1 Create `fuse_prerequisites.py`
- [ ] 5.2 Implement definition dependencies loading
- [ ] 5.3 Implement LLM inference results loading
- [ ] 5.4 Implement relation fusion logic (merge multiple evidence sources)
- [ ] 5.5 Implement deduplication by source-target pair
- [ ] 5.6 Implement EduKG standard relation generation (PREREQUISITE_ON)
- [ ] 5.7 Implement confidence aggregation
- [ ] 5.8 Implement CSV output (`math_final_prereq.csv`)
- [ ] 5.9 Add fusion statistics logging
- [ ] 5.10 Add command-line interface

## 6. Prerequisite Import Script

- [ ] 6.1 Create `import_prereq_to_neo4j.py` with Neo4j driver setup
- [ ] 6.2 Implement TEACHES_BEFORE relations import
- [ ] 6.3 Implement PREREQUISITE relations import
- [ ] 6.4 Implement PREREQUISITE_CANDIDATE relations import
- [ ] 6.5 Implement PREREQUISITE_ON relations import
- [ ] 6.6 Implement batch import using UNWIND Cypher
- [ ] 6.7 Add progress logging

## 7. DAG Validation Script

- [ ] 7.1 Create `validate_dag.py`
- [ ] 7.2 Implement cycle detection in PREREQUISITE relations
- [ ] 7.3 Implement cycle count reporting
- [ ] 7.4 Implement cycle-involved knowledge points listing
- [ ] 7.5 Implement quality metrics calculation (coverage rate, average chain length, confidence distribution)
- [ ] 7.6 Add validation report output
- [ ] 7.7 Add exit codes (0: success/no cycles, 1: failure/cycles detected)

## 8. Testing

- [ ] 8.1 Write unit tests for `infer_teaches_before.py` (test chapter sequence logic)
- [ ] 8.2 Write unit tests for `extract_definition_deps.py` (test name matching)
- [ ] 8.3 Write unit tests for `infer_prerequisites_llm.py` (mock LLM Gateway)
- [ ] 8.4 Write unit tests for voting logic
- [ ] 8.5 Write unit tests for `fuse_prerequisites.py` (test fusion logic)
- [ ] 8.6 Write unit tests for DAG validation logic
- [ ] 8.7 Create integration test script (all scripts → validate)
- [ ] 8.8 Verify all tests pass with `pytest`

## 9. Documentation

- [ ] 9.1 Add inline docstrings to all functions
- [ ] 9.2 Update README.md with prerequisite inference workflow
- [ ] 9.3 Document LLM prompt template and voting logic