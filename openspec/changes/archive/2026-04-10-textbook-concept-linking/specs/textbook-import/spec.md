## ADDED Requirements

### Requirement: Parse textbook JSON data
The system SHALL parse textbook JSON files and generate chapter structure file.

#### Scenario: Parse middle school textbook
- **WHEN** system parses textbook JSON file
- **THEN** system extracts grade, semester, chapters, and knowledge points

#### Scenario: Generate textbook_chapters.json
- **WHEN** parsing completes
- **THEN** system saves result to `textbook_chapters.json` with structure:
  ```json
  {
    "chapters": [
      {
        "name": "人教版_数学_七年级_上册_第一章_有理数",
        "publisher": "人教版",
        "subject": "数学",
        "grade": "七年级",
        "semester": "上册",
        "chapter": "第一章有理数",
        "order": 1,
        "knowledge_points": ["有理数", "数轴", "相反数"]
      }
    ]
  }
  ```

#### Scenario: Handle missing file
- **WHEN** textbook file does not exist
- **THEN** system raises FileNotFoundError with clear message

### Requirement: No Neo4j import
The system SHALL NOT import data to Neo4j automatically.

#### Scenario: Output file only
- **WHEN** parsing completes
- **THEN** only generates `textbook_chapters.json`, no Neo4j import

#### Scenario: Manual import later
- **WHEN** user wants to import
- **THEN** user manually runs import script after confirming data