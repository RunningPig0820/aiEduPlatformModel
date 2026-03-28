# knowledge-visualization Specification

## Purpose
TBD - created by archiving change integrate-edukg-knowledge-graph. Update Purpose after archive.
## Requirements
### Requirement: Knowledge Tree Output

The system SHALL generate hierarchical knowledge tree data for a subject.

#### Scenario: Generate subject tree
- **WHEN** requesting a knowledge tree for a subject (e.g., math)
- **THEN** the system SHALL return a tree structure with classes and entities

#### Scenario: Tree depth control
- **WHEN** requesting a knowledge tree with depth parameter
- **THEN** the system SHALL limit the tree to the specified depth

#### Scenario: Tree node format
- **WHEN** generating tree nodes
- **THEN** each node SHALL include: id, label, type (class/entity), children

---

### Requirement: Entity Graph Output

The system SHALL generate graph data (nodes and edges) for visualization.

#### Scenario: Generate entity graph
- **WHEN** requesting graph data for an entity
- **THEN** the system SHALL return nodes and edges for N-hop neighbors

#### Scenario: Graph format compatibility
- **WHEN** generating graph data
- **THEN** the system SHALL support D3.js and ECharts formats

#### Scenario: Edge direction
- **WHEN** generating graph data
- **THEN** the system SHALL include edge direction and type

---

### Requirement: Student Progress Tracking

The system SHALL track and visualize student learning progress on knowledge points.

#### Scenario: Initialize student progress
- **WHEN** a new student is registered
- **THEN** the system SHALL initialize progress tracking for the student

#### Scenario: Update learning progress
- **WHEN** a student masters a knowledge point
- **THEN** the system SHALL record the progress with status, score, and timestamp

#### Scenario: Query student progress
- **WHEN** requesting a student's progress for a subject
- **THEN** the system SHALL return mastered, in-progress, and not-started entities

---

### Requirement: Progress Visualization Data

The system SHALL generate progress visualization data combining knowledge tree with student progress.

#### Scenario: Generate progress tree
- **WHEN** requesting a student's progress tree
- **THEN** the system SHALL return the subject tree with progress status on each node

#### Scenario: Progress statistics
- **WHEN** requesting progress statistics
- **THEN** the system SHALL return: total, mastered, in-progress, not-started counts

#### Scenario: Learning path recommendation
- **WHEN** requesting next recommended knowledge points
- **THEN** the system SHALL suggest entities based on prerequisites and current progress

---

### Requirement: Prerequisite Chain

The system SHALL support prerequisite relationships for learning path generation.

#### Scenario: Query prerequisites
- **WHEN** querying prerequisites for a knowledge point
- **THEN** the system SHALL return all prerequisite entities

#### Scenario: Learning path generation
- **WHEN** generating a learning path
- **THEN** the system SHALL order knowledge points by prerequisite dependencies

---

### Requirement: Multi-Subject Progress

The system SHALL support progress tracking across multiple subjects.

#### Scenario: Cross-subject overview
- **WHEN** requesting a student's overall progress
- **THEN** the system SHALL return progress summary for all subjects

#### Scenario: Subject-specific progress
- **WHEN** requesting progress for a specific subject
- **THEN** the system SHALL return detailed progress for that subject only

