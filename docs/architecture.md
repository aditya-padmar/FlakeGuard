# FlakeGuard Architecture

## Overview

FlakeGuard is an AI-powered system for detecting, classifying, and remediating flaky tests. It combines rule-based analysis with LLM-powered intelligence to automatically identify root causes and suggest fixes.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FlakeGuard System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │  Frontend   │    │   Backend    │    │   AI Agent   │     │
│  │  (React)    │───▶│  (FastAPI)   │◀──▶│    (Bob)     │     │
│  └─────────────┘    └──────────────┘    └──────────────┘     │
│                            │                                     │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Core Components                        │  │
│  ├──────────────┬──────────────┬───────────────┬───────────┤  │
│  │   Harness    │   Bob AI     │  Remediation  │  Auditor  │  │
│  │   (Testing)  │   (Agent)    │  (Fixes)      │  (Track)  │  │
│  └──────────────┴──────────────┴───────────────┴───────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌────────────────────────┐
              │   Data Storage         │
              │   (JSON/SQLite)        │
              └────────────────────────┘
```

## Core Components

### 1. Test Harness (Member 2 - F1)

**Location:** `backend/harness/`

**Responsibility:** Executes tests and captures results.

**Components:**
- `runner.py` - Executes pytest and captures output
- `executor.py` - Orchestrates multiple test runs
- `analyzer.py` - Analyzes runs to detect flakiness

**How it works:**
1. Runs tests multiple times (default: 5)
2. Captures pass/fail status each run
3. Identifies tests with inconsistent results
4. Calculates flake rate and confidence

### 2. Bob AI Agent (Member 1 - F2)

**Location:** `backend/bob/`

**Responsibility:** Classifies flaky tests using specialized subagents.

**Components:**
- `agent.py` - Main agent coordinator
- `classifier.py` - Orchestrates classification
- `subagents/` - Specialized analyzers:
  - `timing.py` - Detects timing issues
  - `ordering.py` - Detects order dependencies
  - `leakage.py` - Detects state leakage
  - `environment.py` - Detects env dependencies

**How it works:**
1. Each subagent analyzes test code for its specialty
2. Subagents return scores and evidence
3. Classifier selects most likely root cause
4. Agent generates reasoning and fix suggestions

### 3. Remediation (Member 3 - F3)

**Location:** `backend/remediation/`

**Responsibility:** Generates fix suggestions and code diffs.

**Components:**
- `generator.py` - Creates fix suggestions
- `templates.py` - Common fix patterns
- `diff_generator.py` - Generates code diffs

**How it works:**
1. Takes classification as input
2. Selects appropriate fix template
3. Generates multiple suggestions
4. Creates code diffs where possible

### 4. Auditor (Member 3 - F4)

**Location:** `backend/auditor/`

**Responsibility:** Tracks actions and manages quarantine.

**Components:**
- `auditor.py` - Main audit logger
- `quarantine_parser.py` - Parses quarantine files
- `ci_parser.py` - Parses CI output

**How it works:**
1. Logs all actions (detection, classification, fixes)
2. Manages quarantine list
3. Tracks test status over time
4. Generates reports

### 5. API (Member 5)

**Location:** `backend/api/`

**Responsibility:** Exposes functionality via REST API.

**Endpoints:**
- `/api/detection` - Test detection endpoints
- `/api/classification` - Classification endpoints
- `/api/remediation` - Fix generation endpoints
- `/api/audit` - Audit and quarantine endpoints
- `/api/metrics` - Metrics and reporting

### 6. Frontend (Member 4 - F5)

**Location:** `frontend/`

**Responsibility:** Provides dashboard for visualization and interaction.

**Components:**
- `Dashboard.tsx` - Main dashboard view
- `TestInventory.tsx` - List of flaky tests
- `RootCauseChart.tsx` - Root cause visualization
- `MetricsPanel.tsx` - Key metrics display
- `FixViewer.tsx` - Fix suggestion viewer
- `QuarantineTable.tsx` - Quarantine management

## Data Flow

```
1. Test Execution
   CI/GitHub ──▶ Harness ──▶ Test Runs

2. Flaky Detection
   Test Runs ──▶ Analyzer ──▶ Flaky Tests

3. Classification
   Flaky Tests ──▶ Bob Agent ──▶ Classifications

4. Remediation
   Classifications ──▶ Fix Generator ──▶ Fixes

5. Tracking
   All Actions ──▶ Auditor ──▶ Audit Logs + Quarantine
```

## AI Agent Architecture (Bob)

```
Bob Agent
├── Classifier (Coordinator)
│   ├── Timing Subagent
│   │   └── Analyzes: sleeps, timeouts, timing assertions
│   ├── Ordering Subagent
│   │   └── Analyzes: shared fixtures, global state
│   ├── Leakage Subagent
│   │   └── Analyzes: mutable state, missing cleanup
│   └── Environment Subagent
│       └── Analyzes: network, env vars, randomness
│
└── LLM Integration
    ├── OpenAI (optional)
    └── Anthropic (optional)
```

## Root Cause Categories

1. **Timing** - Tests dependent on timing or have race conditions
2. **Ordering** - Tests dependent on execution order
3. **State Leakage** - Tests that leak state between executions
4. **Environment** - Tests dependent on external environment
5. **Network** - Tests with network-related flakiness
6. **Resource** - Tests with resource constraints
7. **Race Condition** - Tests with concurrent execution issues
8. **Floating Point** - Tests with precision issues
9. **Unknown** - Unclassified flakiness

## Data Storage

**Development:** JSON files in `data/` directory

**Production (Recommended):** SQLite or PostgreSQL

**Structure:**
- `data/runs/` - Test run results
- `data/classifications/` - Classification results
- `data/fixes/` - Generated fixes
- `data/metrics/` - Metrics data

## Security Considerations

1. **API Keys** - Store LLM API keys in environment variables
2. **Input Validation** - All API inputs are validated with Pydantic
3. **Rate Limiting** - Recommended for production deployment
4. **Authentication** - Implement for production use

## Deployment

### Development
```bash
# Backend
pip install -r requirements.txt
python backend/main.py

# Frontend
cd frontend
npm install
npm run dev
```

### Production
- Use Gunicorn/Uvicorn for backend
- Build frontend with `npm run build`
- Deploy with Docker or Kubernetes

## Extending the System

### Adding a New Subagent

1. Create file in `backend/bob/subagents/`
2. Implement `analyze()` method
3. Register in `backend/bob/classifier.py`
4. Add prompt in `backend/bob/prompts/`

### Adding New Fix Templates

1. Add template in `backend/remediation/templates.py`
2. Update `FixTemplates.TEMPLATES` dictionary
3. Add generator logic in `generator.py`

## Performance

- Detection: ~2-5 seconds per run
- Classification: ~1-3 seconds per test
- Fix Generation: ~1-2 seconds per test
- Memory: ~50-100MB baseline

## Monitoring

- Metrics API provides system health
- Audit logs track all actions
- Error tracking via standard Python logging
