# textbook-data-parser Specification

## ADDED Requirements

### Requirement: Parse textbook JSON files

The system SHALL parse textbook JSON files from the local filesystem.

#### Scenario: Parse middle school grade 7 textbook
- **WHEN** the system parses `textbook/math/renjiao/middle/grade7/shang.json`
- **THEN** the system extracts stage="middle", grade="七年级", semester="上册"

#### Scenario: Parse primary school textbook
- **WHEN** the system parses `textbook/math/renjiao/primary/grade1/shang.json`
- **THEN** the system extracts stage="primary", grade="一年级", semester="上册"

### Requirement: Extract chapter and knowledge point structure

The system SHALL extract chapter and knowledge point structure from textbook JSON.

#### Scenario: Extract chapter with knowledge points
- **WHEN** the system processes a textbook JSON with chapter "有理数" containing knowledge points
- **THEN** the system extracts chapter_name, chapter_order, section_name, and knowledge_points array

### Requirement: Output standardized textbook data

The system SHALL output standardized JSON data for all textbooks.

#### Scenario: Output all 24 textbooks
- **WHEN** the system completes parsing all textbook JSON files
- **THEN** the system outputs a single `textbook_data.json` with 24 textbooks, each containing chapters and knowledge points

### Requirement: Handle missing or invalid data

The system SHALL handle missing or invalid data gracefully.

#### Scenario: Skip invalid JSON file
- **WHEN** the system encounters a malformed JSON file
- **THEN** the system logs an error and continues processing other files

#### Scenario: Handle empty knowledge points array
- **WHEN** a section has empty knowledge_points array
- **THEN** the system records the section without knowledge points
