## ADDED Requirements

### Requirement: Export reviewed results from MySQL

The system SHALL provide a script to export reviewed results from MySQL to JSON.

#### Scenario: Export approved matches
- **WHEN** running export_review_results.py
- **THEN** script outputs reviewed_matches.json with records where review_status=approved

#### Scenario: Include new KP records
- **WHEN** exporting reviewed results
- **THEN** script includes records where review_status=new_kp with generated URI

### Requirement: Import approved matches to Neo4j

The system SHALL create MATCHES_KG relations in Neo4j for approved matches.

#### Scenario: Create MATCHES_KG relation
- **WHEN** running import_matches_to_neo4j.py
- **THEN** Cypher creates (TextbookKP)-[:MATCHES_KG]->(Concept) relations

#### Scenario: Relation properties
- **WHEN** creating MATCHES_KG relation
- **THEN** relation includes properties: confidence, method="manual_review", reviewer_id, review_time

### Requirement: Import new knowledge points to Neo4j

The system SHALL create new Concept nodes for reviewer-created knowledge points.

#### Scenario: Create new Concept node
- **WHEN** review_status=new_kp
- **THEN** Cypher creates new Concept node with generated URI and label

#### Scenario: Create MATCHES_KG to new Concept
- **WHEN** new Concept created
- **THEN** also creates MATCHES_KG relation from TextbookKP to new Concept

### Requirement: Verify import results

The system SHALL verify Neo4j import results.

#### Scenario: Count imported relations
- **WHEN** import completes
- **THEN** script logs count of created MATCHES_KG relations

#### Scenario: Verify relation integrity
- **WHEN** verification runs
- **THEN** script confirms all exported records have corresponding Neo4j relations