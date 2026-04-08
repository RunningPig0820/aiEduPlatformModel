## ADDED Requirements

### Requirement: State database initialization

The system SHALL provide MySQL database schema for state management.

#### Scenario: Create database and tables

- **WHEN** the initialization script is executed
- **THEN** it SHALL create database `ai_edu_kg` with tables: processing_state, llm_cache, cost_tracking, chapter_state, subbatch_state, failed_batches

#### Scenario: Create progress view

- **WHEN** database is initialized
- **THEN** it SHALL create view `progress_view` for progress querying

### Requirement: Chapter state management

The system SHALL provide StateDB class for chapter-level state management.

#### Scenario: Get chapter status

- **WHEN** `get_chapter_status(chapter_id)` is called
- **THEN** it SHALL return the current status (pending/processing/completed/failed/skipped)

#### Scenario: Mark chapter processing

- **WHEN** `mark_chapter_processing(chapter_id)` is called
- **THEN** it SHALL update status to 'processing' and set started_at timestamp

#### Scenario: Mark chapter completed

- **WHEN** `mark_chapter_completed(chapter_id)` is called
- **THEN** it SHALL update status to 'completed' and set completed_at timestamp

#### Scenario: Mark chapter failed

- **WHEN** `mark_chapter_failed(chapter_id, error)` is called
- **THEN** it SHALL update status to 'failed' with error message

#### Scenario: Skip chapter

- **WHEN** `skip_chapter(chapter_id, reason)` is called
- **THEN** it SHALL update status to 'skipped' with reason

### Requirement: Subbatch state management

The system SHALL provide subbatch-level state management.

#### Scenario: Check subbatch completion

- **WHEN** `is_subbatch_completed(batch_id)` is called
- **THEN** it SHALL return True if status is 'completed'

#### Scenario: Mark subbatch completed

- **WHEN** `mark_subbatch_completed(batch_id, cache_key, result_file)` is called
- **THEN** it SHALL update status, cache_key, and result_file

### Requirement: LLM cache management

The system SHALL provide LLM response caching.

#### Scenario: Get cached response

- **WHEN** `get_cached_response(cache_key)` is called
- **THEN** it SHALL return cached response if exists, None otherwise

#### Scenario: Save cache

- **WHEN** `save_cache(cache_key, provider, model, batch_uris, response, tokens, cost)` is called
- **THEN** it SHALL insert or update the cache record

### Requirement: Progress querying

The system SHALL provide progress querying capabilities.

#### Scenario: Get progress

- **WHEN** `get_progress(subject, version)` is called
- **THEN** it SHALL return total_chapters, completed_chapters, processing_chapters, failed_chapters, progress_percent

#### Scenario: Get failed chapters

- **WHEN** `get_failed_chapters(subject, version)` is called
- **THEN** it SHALL return list of failed chapters with error messages