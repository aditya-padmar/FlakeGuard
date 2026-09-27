# IBM Bob AI Assistant Session Logs

This directory contains exported reports and logs from IBM Bob autonomous agents utilized in FlakeGuard.

## Overview

FlakeGuard integrates specialized IBM Bob subagents to perform deep root cause analysis and automated remediation for flaky tests:
- **Timing & Concurrency Agent**: Analyzes AST frames, wall-clock drift, and race conditions.
- **Order Dependency Agent**: Traces test execution order, state mutations, and test pollution.
- **State Leakage Agent**: Detects un-evicted caches (e.g. Redis, in-memory singletons) and database residue.
- **Environment & Async I/O Agent**: Measures latency spikes, socket deadlines, and transient failures.

## Contents

- `SESSION_LOG.md`: Comprehensive historical diagnostic verdicts, subagent score breakdowns, and AST evidence records across multiple test suite evaluations.

*Note: Per hackathon security guidelines, credentials and raw environment tokens are filtered via `.bobignore`.*
