## ADDED Requirements

### Requirement: MySQL table stores unmatched knowledge points

The system SHALL provide a MySQL table `textbook_kp_match_review` to store unmatched textbook knowledge points with their review status.

#### Scenario: Table schema created
- **WHEN** database migration runs
- **THEN** table `textbook_kp_match_review` exists with columns: id, textbook_kp_uri, textbook_kp_name, normalized_name, best_candidate_uri, best_candidate_name, candidate_list, confidence, review_status, reviewer_action, final_kg_uri, reviewer_id, review_time, created_at

#### Scenario: Review status enum values
- **WHEN** inserting a record
- **THEN** review_status accepts values: pending, approved, rejected, new_kp

### Requirement: Save unmatched data during matching

The system SHALL save unmatched knowledge points directly during the matching process in `match_textbook_kp.py`.

#### Scenario: Auto-save unmatched records
- **WHEN** match_textbook_kp.py completes matching
- **THEN** script automatically outputs unmatched_kps.json containing all records where matched=false

#### Scenario: Include candidate information
- **WHEN** saving unmatched records
- **THEN** each record includes textbook_kp_uri, textbook_kp_name, normalized_name, best_candidate_uri, best_candidate_name, similarity, confidence, reason

#### Scenario: Output location
- **WHEN** saving unmatched records
- **THEN** file is saved to same output directory as matches_kg_relations.json

### Requirement: Import data to MySQL

The system SHALL provide a script to import unmatched data into MySQL.

#### Scenario: Batch insert records
- **WHEN** running import_to_mysql.py
- **THEN** all 308 unmatched records inserted into textbook_kp_match_review with review_status=pending

#### Scenario: Handle duplicate URIs
- **WHEN** textbook_kp_uri already exists in table
- **THEN** script skips insert and logs warning