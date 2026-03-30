## 1. Database Setup

- [ ] 1.1 Create database configuration template (`config/database.yaml`)
- [ ] 1.2 Create database initialization script (`scripts/init_database.py`)
- [ ] 1.3 Create database schema DDL file (`scripts/schema/mysql_schema.sql`)
- [ ] 1.4 Add PyMySQL dependency to requirements.txt
- [ ] 1.5 Add PyYAML dependency to requirements.txt

## 2. MySQL Connection Manager

- [ ] 2.1 Create `core/db_connection.py` with MySQLManager class
- [ ] 2.2 Implement connection pool configuration
- [ ] 2.3 Implement `get_connection()` context manager
- [ ] 2.4 Implement `transaction()` context manager
- [ ] 2.5 Add environment variable support for credentials

## 3. State Database Module

- [ ] 3.1 Create `core/state_db.py` with StateDB class
- [ ] 3.2 Implement chapter state methods (get_chapter_status, mark_chapter_*)
- [ ] 3.3 Implement subbatch state methods (is_subbatch_completed, mark_subbatch_*)
- [ ] 3.4 Implement LLM cache methods (get_cached_response, save_cache)
- [ ] 3.5 Implement progress query methods (get_progress, get_failed_chapters)
- [ ] 3.6 Implement cost tracking method (track_cost)
- [ ] 3.7 Add error handling and logging

## 4. Process Lock Module

- [ ] 4.1 Add portalocker dependency to requirements.txt
- [ ] 4.2 Create `core/process_lock.py` with ProcessLock class
- [ ] 4.3 Implement file-based lock (acquire, release)
- [ ] 4.4 Implement context manager support
- [ ] 4.5 Implement MySQLLock class for distributed scenarios
- [ ] 4.6 Add lock timeout and stale lock cleanup
- [ ] 4.7 Add cross-platform compatibility (Linux/macOS/Windows)

## 5. Cost Tracker Module

- [ ] 5.1 Create `core/cost_tracker.py` with CostTracker class
- [ ] 5.2 Implement cost accumulation (track_cost)
- [ ] 5.3 Implement cost threshold alerting
- [ ] 5.4 Implement cost report generation
- [ ] 5.5 Add cost display in progress output

## 6. Progress CLI

- [ ] 6.1 Create `show_progress.py` CLI script
- [ ] 6.2 Implement `--show-progress` command
- [ ] 6.3 Implement `--retry-failed` command
- [ ] 6.4 Implement `--skip-chapter` command
- [ ] 6.5 Implement `--cost-report` command

## 7. Testing

- [ ] 7.1 Write unit tests for MySQLManager
- [ ] 7.2 Write unit tests for StateDB
- [ ] 7.3 Write unit tests for ProcessLock
- [ ] 7.4 Write unit tests for CostTracker
- [ ] 7.5 Create integration test with test database
- [ ] 7.6 Verify all tests pass with `pytest`

## 8. Documentation

- [ ] 8.1 Add inline docstrings to all modules
- [ ] 8.2 Create README.md for `core/` module
- [ ] 8.3 Add usage examples in docstrings