# FlakeGuard

AI-powered flaky test detection, classification, and remediation system.

## Overview

FlakeGuard helps development teams identify, classify, and fix flaky tests automatically. It uses AI agents to analyze test failures and provide actionable remediation suggestions.

## Features

- **Test Detection**: Identifies flaky tests across multiple runs
- **Root Cause Classification**: Classifies failures by type (timing, ordering, leakage, environment)
- **Automated Remediation**: Generates fix suggestions and code diffs
- **Quarantine Management**: Tracks quarantined tests and their status
- **Metrics Dashboard**: Visualize flaky test trends and remediation progress

## Project Structure

- `backend/` - Python FastAPI backend with AI agents
- `frontend/` - React TypeScript dashboard
- `sample-repo/` - Example repository with flaky tests for testing
- `data/` - Storage for runs, classifications, fixes, and metrics
- `scripts/` - Utility scripts for running detection and pipelines
- `docs/` - Documentation and architecture guides

## Quick Start

1. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   ```

4. Run the backend:
   ```bash
   python backend/main.py
   ```

5. Run the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

## Documentation

See `docs/architecture.md` for system architecture and `docs/api.md` for API documentation.
