## ADDED Requirements

### Requirement: Parse textbook JSON data
The system SHALL parse textbook JSON files from `edukg/data/textbook/math/renjiao/` directory.

#### Scenario: Parse middle school textbook
- **WHEN** system parses `middle/grade7/shang.json`
- **THEN** system extracts grade "七年级", semester "上册", and all chapters with sections

#### Scenario: Parse primary school textbook
- **WHEN** system parses `primary/grade1/shang.json`
- **THEN** system extracts grade "一年级", semester "上册", and all chapters

#### Scenario: Handle missing file
- **WHEN** textbook file does not exist
- **THEN** system raises FileNotFoundError with clear message

### Requirement: Create chapter nodes
The system SHALL create `textbook_chapter` nodes in Neo4j from parsed textbook data.

#### Scenario: Create chapter node with all attributes
- **WHEN** creating chapter for "人教版_数学_七年级_上册_第一章_有理数"
- **THEN** node has name, publisher, subject, grade, semester, chapter, order attributes

#### Scenario: Avoid duplicate chapters
- **WHEN** chapter node already exists with same name
- **THEN** system skips creation (MERGE behavior)

### Requirement: Import all textbooks
The system SHALL support batch import of all textbook files.

#### Scenario: Import all grades
- **WHEN** running import with `--all` flag
- **THEN** all 24 textbooks are imported (12 primary + 6 middle + 6 high)

#### Scenario: Import by stage
- **WHEN** running import with `--stage middle`
- **THEN** only middle school textbooks are imported

### Requirement: Query chapters by criteria
The system SHALL support querying chapters by grade, semester, publisher.

#### Scenario: Query by grade and semester
- **WHEN** querying chapters where grade="七年级" and semester="上册"
- **THEN** returns all chapters for 七年级上册

#### Scenario: Query by chapter name
- **WHEN** querying chapter by name "人教版_数学_七年级_上册_第一章_有理数"
- **THEN** returns single chapter node