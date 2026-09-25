# FlakeGuard API Documentation

## Overview

FlakeGuard provides a REST API for detecting, classifying, and remediating flaky tests.

**Base URL:** `http://localhost:8000/api`

## Endpoints

### Detection

#### POST `/detection/runs`
Create a new test run record.

**Request Body:**
```json
{
  "run_id": "string",
  "repository": "string",
  "branch": "string",
  "commit_sha": "string",
  "executions": [
    {
      "test_name": "string",
      "file_path": "string",
      "status": "passed|failed|skipped|error",
      "duration": 0.0,
      "error_message": "string"
    }
  ]
}
```

#### GET `/detection/runs`
List recent test runs.

**Query Parameters:**
- `limit` (int): Number of runs to return (default: 10)

#### GET `/detection/runs/{run_id}`
Get a specific test run.

#### POST `/detection/analyze`
Analyze test runs to detect flaky tests.

**Query Parameters:**
- `min_runs` (int): Minimum runs required (default: 3)

**Response:**
```json
{
  "detection_id": "string",
  "repository": "string",
  "analysis_period_start": "timestamp",
  "analysis_period_end": "timestamp",
  "total_test_runs": 5,
  "flaky_tests": [...],
  "detection_confidence": 0.85
}
```

### Classification

#### POST `/classification/classify`
Classify a flaky test to determine root cause.

**Request Body:**
```json
{
  "test_name": "string",
  "file_path": "string",
  "flake_rate": 0.0,
  "total_runs": 0,
  "recent_failures": ["string"]
}
```

**Response:**
```json
{
  "classification_id": "string",
  "test_name": "string",
  "root_cause": "timing|ordering|state_leakage|environment|...",
  "confidence": "high|medium|low",
  "evidence": [...],
  "reasoning": "string",
  "suggested_fix_area": "string"
}
```

#### GET `/classification/root-causes`
List all possible root cause types.

### Remediation

#### POST `/remediation/generate`
Generate fix suggestions for a classified test.

**Request Body:**
```json
{
  "classification_id": "string",
  "test_name": "string",
  "root_cause": "string",
  "evidence": [...]
}
```

**Response:**
```json
{
  "fix_id": "string",
  "suggestions": [
    {
      "suggestion_id": "string",
      "fix_type": "code_change|timeout_adjustment|...",
      "description": "string",
      "confidence": 0.0
    }
  ],
  "primary_suggestion_id": "string"
}
```

#### POST `/remediation/fixes/{fix_id}/apply`
Apply a specific fix suggestion.

**Request Body:**
```json
{
  "suggestion_id": "string"
}
```

### Audit & Quarantine

#### GET `/audit/quarantine`
List quarantined tests.

**Query Parameters:**
- `status` (string): Filter by status (active|under_review|resolved)

#### POST `/audit/quarantine`
Add a test to quarantine.

**Request Body:**
```json
{
  "test_name": "string",
  "file_path": "string",
  "reason": "string",
  "root_cause": "string"
}
```

#### PUT `/audit/quarantine/{quarantine_id}/status`
Update quarantine entry status.

**Request Body:**
```json
{
  "status": "active|under_review|resolved|removed",
  "notes": "string"
}
```

#### GET `/audit/quarantine/report`
Get comprehensive quarantine report.

#### GET `/audit/logs`
List audit logs.

**Query Parameters:**
- `action` (string): Filter by action type
- `entity_type` (string): Filter by entity type
- `limit` (int): Number of logs to return

### Metrics

#### GET `/metrics/summary`
Get overall metrics summary.

**Response:**
```json
{
  "total_flaky_tests": 15,
  "tests_quarantined": 8,
  "tests_fixed": 12,
  "average_time_to_fix": "2.5 days",
  "flake_rate": "3.2%",
  "resolution_rate": "85%"
}
```

#### GET `/metrics/root-causes`
Get breakdown of flaky tests by root cause.

#### GET `/metrics/trends`
Get flaky test trends over time.

**Query Parameters:**
- `days` (int): Number of days (default: 30)

## Error Responses

All endpoints may return the following error responses:

- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

**Error Format:**
```json
{
  "detail": "Error message"
}
```

## Rate Limiting

API requests are rate-limited to 100 requests per minute per IP.

## Authentication

Currently, the API does not require authentication. For production use, implement appropriate authentication mechanisms.
