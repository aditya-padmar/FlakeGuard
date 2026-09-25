# Quarantined Tests

This file tracks tests that have been quarantined due to flakiness.

## Active Quarantines

| Test | Reason | Quarantined Date | Runs Until Review |
|------|--------|------------------|-------------------|
| test_timing_dependent | Timing issue | 2024-01-15 | 10 |
| test_shared_state | State leakage | 2024-01-20 | 8 |

## Resolved Quarantines

| Test | Reason | Resolved Date | Fix Applied |
|------|--------|---------------|-------------|
| test_async_order | Race condition | 2024-01-10 | Added proper async await |

## Quarantine Policy

Tests are quarantined after 3 consecutive flaky failures. They are reviewed every 10 runs or when a fix is proposed.
