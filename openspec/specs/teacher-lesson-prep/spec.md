# teacher-lesson-prep Specification

## Purpose
TBD - created by archiving change integrate-edukg-knowledge-graph. Update Purpose after archive.
## Requirements
### Requirement: Knowledge Point Recommendation

The system SHALL recommend related knowledge points for lesson preparation.

#### Scenario: Recommend by topic
- **WHEN** a teacher enters a topic (e.g., "二次函数")
- **THEN** the system SHALL recommend related knowledge points

#### Scenario: Recommend by chapter
- **WHEN** a teacher selects a chapter
- **THEN** the system SHALL return all knowledge points in that chapter

#### Scenario: Recommend prerequisites
- **WHEN** planning a lesson on a knowledge point
- **THEN** the system SHALL suggest prerequisite knowledge points to review

---

### Requirement: Related Content Discovery

The system SHALL discover related educational content from the knowledge graph.

#### Scenario: Find related exercises
- **WHEN** a teacher queries exercises for a knowledge point
- **THEN** the system SHALL return exercise entities linked to that point

#### Scenario: Find related materials
- **WHEN** a teacher queries reading materials
- **THEN** the system SHALL return material entities related to the knowledge point

---

### Requirement: Difficulty Assessment

The system SHALL provide difficulty assessment for knowledge points based on graph properties.

#### Scenario: Calculate difficulty
- **WHEN** querying a knowledge point
- **THEN** the system SHALL estimate difficulty based on:
  - Number of prerequisites
  - Depth in hierarchy
  - Number of related concepts

#### Scenario: Difficulty-aware recommendation
- **WHEN** recommending content for a grade level
- **THEN** the system SHALL filter by estimated difficulty

---

### Requirement: Cross-Reference Discovery

The system SHALL discover cross-subject references for interdisciplinary teaching.

#### Scenario: Find cross-subject connections
- **WHEN** querying a knowledge point
- **THEN** the system SHALL find related points in other subjects

#### Scenario: Interdisciplinary lesson suggestion
- **WHEN** planning an interdisciplinary lesson
- **THEN** the system SHALL suggest knowledge points from multiple subjects

---

### Requirement: Teaching Sequence Optimization

The system SHALL suggest optimal teaching sequence based on knowledge graph structure.

#### Scenario: Sequence by prerequisites
- **WHEN** a teacher requests teaching sequence for a set of knowledge points
- **THEN** the system SHALL order points respecting prerequisite relationships

#### Scenario: Parallel teaching suggestions
- **WHEN** knowledge points have no dependency
- **THEN** the system SHALL suggest they can be taught in parallel

---

### Requirement: Student Weakness Analysis

The system SHALL analyze student weaknesses based on knowledge graph and progress data.

#### Scenario: Identify weak areas
- **WHEN** analyzing a student's progress
- **THEN** the system SHALL identify knowledge points with low scores

#### Scenario: Suggest remedial content
- **WHEN** weaknesses are identified
- **THEN** the system SHALL recommend review materials and exercises

#### Scenario: Class-wide weakness analysis
- **WHEN** a teacher requests class analysis
- **THEN** the system SHALL aggregate weakness data across students

