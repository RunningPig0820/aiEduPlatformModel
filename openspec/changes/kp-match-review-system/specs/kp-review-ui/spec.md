## ADDED Requirements

### Requirement: Review page displays pending items

The system SHALL provide a Web page displaying pending review items from MySQL.

#### Scenario: Load pending items
- **WHEN** reviewer opens review page
- **THEN** page displays all records where review_status=pending

#### Scenario: Display item details
- **WHEN** showing a pending item
- **THEN** page shows: textbook_kp_name, normalized_name, best_candidate_name, confidence

### Requirement: Reviewer can approve match

The system SHALL allow reviewer to approve a recommended match.

#### Scenario: Confirm best candidate
- **WHEN** reviewer clicks "Confirm" button
- **THEN** review_status updated to approved, final_kg_uri set to best_candidate_uri

#### Scenario: Select alternative candidate
- **WHEN** reviewer selects a different candidate from list
- **THEN** review_status updated to approved, final_kg_uri set to selected candidate URI

### Requirement: Reviewer can reject match

The system SHALL allow reviewer to reject a match and optionally create new knowledge point.

#### Scenario: Reject without new KP
- **WHEN** reviewer clicks "Reject" button
- **THEN** review_status updated to rejected, final_kg_uri remains empty

#### Scenario: Create new knowledge point
- **WHEN** reviewer clicks "Create New" button
- **THEN** review_status updated to new_kp, final_kg_uri set to newly generated URI

### Requirement: Record reviewer actions

The system SHALL record who performed each review action.

#### Scenario: Save reviewer info
- **WHEN** any review action submitted
- **THEN** reviewer_id and review_time saved to record