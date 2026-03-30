## ADDED Requirements

### Requirement: File-based process lock

The system SHALL provide file-based process lock using portalocker.

#### Scenario: Acquire lock successfully

- **WHEN** `ProcessLock.acquire()` is called and no other process holds the lock
- **THEN** it SHALL return True and write PID to lock file

#### Scenario: Acquire lock fails

- **WHEN** `ProcessLock.acquire()` is called and another process holds the lock
- **THEN** it SHALL return False

#### Scenario: Release lock

- **WHEN** `ProcessLock.release()` is called
- **THEN** it SHALL unlock and close the lock file

#### Scenario: Context manager support

- **WHEN** using `with ProcessLock(lock_file) as lock:`
- **THEN** it SHALL acquire lock on enter and release on exit

### Requirement: MySQL-based distributed lock

The system SHALL provide MySQL-based distributed lock.

#### Scenario: Acquire distributed lock

- **WHEN** `MySQLLock.acquire(lock_name)` is called
- **THEN** it SHALL insert a lock record with PID and hostname

#### Scenario: Lock conflict detection

- **WHEN** lock is already held by another process
- **THEN** it SHALL raise IntegrityError and return False

#### Scenario: Lock timeout

- **WHEN** lock has been held longer than timeout_seconds
- **THEN** it SHALL be automatically released and can be acquired

#### Scenario: Get lock info

- **WHEN** `get_lock_info(lock_name)` is called
- **THEN** it SHALL return PID, hostname, and acquired_at timestamp

### Requirement: Lock safety

The system SHALL prevent deadlocks and stale locks.

#### Scenario: Stale lock cleanup

- **WHEN** acquiring a lock
- **THEN** expired locks SHALL be cleaned up first

#### Scenario: Process crash recovery

- **WHEN** process crashes without releasing lock
- **THEN** lock SHALL be released after timeout