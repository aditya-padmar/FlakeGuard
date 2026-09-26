# Quarantined Tests

This file tracks tests that have been quarantined due to flakiness.

## Active Quarantines

| Test | Reason | Quarantined Date | Runs Until Review |
|------|--------|------------------|-------------------|
| test_worker_thread_race | Timing issue | 2024-01-15 | 10 |
| test_expects_clean_inventory | State leakage | 2024-01-20 | 8 |

## Resolved Quarantines

| Test | Reason | Resolved Date | Fix Applied |
|------|--------|---------------|-------------|
| test_depends_on_retry_limit | Order dependency | 2024-01-10 | Added proper test ordering and fixture isolation |

## Quarantine Policy

Tests are quarantined after 3 consecutive flaky failures. They are reviewed every 10 runs or when a fix is proposed.
