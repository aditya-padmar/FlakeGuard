# 🛡️ FlakeGuard

> **Autonomous AI-Powered Flaky Test Detection, Root-Cause Classification & Automated Remediation**  
> *Engineered with IBM Bob AI Assistant for the Watsonx Hackathon*

---

## 📌 Executive Summary

Flaky tests are one of the costliest bottlenecks in modern continuous integration pipelines—wasting thousands of developer hours, delaying pull request merges, and eroding confidence in automated test suites. 

**FlakeGuard** is an end-to-end, multi-agent AI system that:
1. **Detects** non-deterministic test failures across repeated execution matrices with adaptive statistical variance scoring.
2. **Diagnoses** root causes via specialized IBM Bob AST subagents (Timing Drift, Concurrency Races, Order Dependencies, State Leakage, and Async I/O deadlines).
3. **Remediates** source code by automatically generating targeted AST diff patches, validated against live test harnesses.
4. **Quarantines & Tracks** unstable tests with automated CI lifecycles, health scores, and metrics dashboards.

---

## 🏛️ System Architecture

FlakeGuard is organized into 4 autonomous backend services orchestrated by FastAPI and integrated with an enterprise React TypeScript dashboard:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FlakeGuard System                                    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   ┌────────────────────────┐      ┌────────────────────────┐      ┌─────────────────┐  │
│   │   Frontend Dashboard   │      │    FastAPI Backend     │      │   IBM Bob AI    │  │
│   │   (React + TypeScript) │────▶ │     (Port 8000)        │◀────▶│  Subagents      │  │
│   └────────────────────────┘      └────────────────────────┘      └─────────────────┘  │
│                                                │                                       │
│                ┌───────────────────────────────┼───────────────────────────────┐       │
│                ▼                               ▼                               ▼       │
│     ┌─────────────────────┐         ┌─────────────────────┐         ┌───────────────┐  │
│     │ F1: Test Harness    │         │ F2: Bob Classifier  │         │ F3: Remedy    │  │
│     │ • Multi-run matrix  │         │ • Timing & Races    │         │ • AST Patcher │  │
│     │ • Git repo ingest   │         │ • Order Dependency  │         │ • Patch Diffs │  │
│     │ • Pytest / Polyglot │         │ • State Leakage     │         │ • Evidence    │  │
│     └─────────────────────┘         └─────────────────────┘         └───────────────┘  │
│                                                │                                       │
│                                                ▼                                       │
│                                     ┌─────────────────────┐                            │
│                                     │ F4: Polyglot Auditor│                            │
│                                     │ • CI Log Parser     │                            │
│                                     │ • Quarantine Engine │                            │
│                                     │ • Health Metrics    │                            │
│                                     └─────────────────────┘                            │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start Guide (Localhost Setup)

Follow these step-by-step instructions to clone, configure, and launch FlakeGuard locally.

### 📋 Prerequisites

Ensure you have the following installed on your machine:
- **Git**: [Download Git](https://git-scm.com/)
- **Python**: `3.10+` (tested on 3.10, 3.11, 3.12, 3.14) — [Download Python](https://www.python.org/)
- **Node.js**: `18.0+` & **npm**: `9.0+` — [Download Node.js](https://nodejs.org/)

---

### Step 1: Clone the Repository

Open your terminal or PowerShell and clone the official repository:

```bash
git clone https://github.com/aditya-padmar/FlakeGuard.git
cd FlakeGuard
```

---

### Step 2: Backend Setup (FastAPI & AI Engine)

1. **Create and activate a virtual environment**:

   **Windows (PowerShell):**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   **macOS / Linux:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Navigate to folder and Install backend dependencies**:
   ```bash
   cd FlakeGuard
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   # On macOS / Linux:
   cp .env.example .env

   # On Windows (PowerShell):
   Copy-Item .env.example .env
   ```
   *(Edit `.env` to configure optional custom API keys or ports; defaults work out of the box for local testing).*

4. **Start the FastAPI Backend Server**:
   ```bash
   python backend/main.py
   ```
   - **Backend API**: `http://localhost:8000`
   - **Interactive API Docs (Swagger UI)**: `http://localhost:8000/docs`
   - **Alternative Docs (ReDoc)**: `http://localhost:8000/redoc`

---

### Step 3: Frontend Setup (React Dashboard)

In a **new terminal window/tab**:

1. **Navigate to the frontend directory**:
   ```bash
   cd FlakeGuard/frontend
   ```

2. **Install frontend dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   - **Web Application**: `http://localhost:5173`

---

### Step 4: Verify Localhost Operation

1. Open your browser and navigate to **`http://localhost:5173`**.
2. **Ingest a Test Suite (Choose Either Method)**:
   - **Option A — 🐙 GitHub Repository (Cloud Scan)**:
     - Stay on the **GitHub Repository** tab.
     - Enter any target repository (e.g. `aditya-padmar/FlakeGuard` or your repo).
     - Select branch (e.g. `main` or `frontend`) and choose Public or Private (with optional GitHub Personal Access Token).
     - Adjust execution passes (e.g. `5 runs`) and click **🚀 Clone & Analyze with Bob Agent**.
   - **Option B — 📁 Upload Test Suite (Local Archive / File Scan)**:
     - Switch to the **Upload Test Suite** tab.
     - Drag & drop a `.zip` archive of your test suite (for example, right-click and zip the included `sample-repo` directory into `sample-repo.zip`) or upload individual `.py` test files directly.
     - Adjust execution passes (e.g. `5 runs`) and click **⚡ Unpack & Run Bob Analysis**.
3. **Inspect Subagent Classification & Diagnostics**:
   - As the test matrix executes, FlakeGuard identifies non-deterministic tests with variance scoring.
   - Click on any detected flaky test to view the root-cause diagnosis from the 4 IBM Bob subagents (Timing Drift, Concurrency Races, State Leakage, Order Dependency).
4. **Generate & Apply Remediation**:
   - Review the auto-generated code diff patch.
   - Click **Apply Fix** to patch source code, or click **Quarantine Test** to isolate the unstable test so CI builds remain green.
   - Navigate to the **Audit & Metrics** tab to review test health trends, quarantine statuses, and CI logs.

---

## 📂 Project Structure

```
FlakeGuard/
├── bob_sessions/          # Official IBM Bob session screenshots, token metrics, and logs
│   ├── README.md          # Index of team member tasks, tokens, and Bobcoins spent
│   ├── SESSION_LOG.md     # Subagent diagnostic execution verdicts & logs
│   └── *.png              # 10 verified Bob IDE task summary screenshots
├── backend/               # FastAPI backend and AI microservices
│   ├── api/routes/        # REST endpoints (detection, classification, remediation, audit)
│   ├── auditor/           # Polyglot CI log parsing and quarantine lifecycle
│   ├── bob/               # IBM Bob subagents (Timing, Leakage, Concurrency, Order)
│   ├── harness/           # Multi-run test matrix execution engine and git clone bridge
│   ├── models/            # Pydantic schemas and domain models
│   ├── remediation/       # AST diff generator, strategy selector, evidence validator
│   └── main.py            # Application entrypoint (port 8000)
├── frontend/              # Modern React + TypeScript SPA
│   ├── src/components/    # Ingestion, Dashboard, Classification, Quarantine, and Remediation views
│   ├── src/services/      # Typed API client with auto-fallback and health check
│   └── vite.config.ts     # Vite build and proxy configuration
├── sample-repo/           # Reference repository with reproducible flaky test patterns
├── data/                  # Storage for run histories, classifications, and metrics
├── docs/                  # In-depth architectural guides and API documentation
├── .bobignore             # Security filter preventing credential leaks to AI assistants
├── SECURITY.MD            # Watsonx Hackathon security compliance guide
├── requirements.txt       # Python backend dependencies
└── package.json           # Frontend dependency manifest
```

---

## 🤖 IBM Bob AI Assistant Sessions & Eligibility Evidence

FlakeGuard was designed, developed, and optimized using the **IBM Bob AI Assistant**. Per the IBM Watsonx Hackathon eligibility requirements (Rule 2), verified session summary screenshots and autonomous logs are documented in [`bob_sessions/`](bob_sessions/):

| Team Member | Primary Roles & Responsibilities | Key Bob Tasks & Milestones | Bobcoins Used |
| :--- | :--- | :--- | :---: |
| **Aditya** | System Architect & Integration Lead | Bob IDE Enterprise configuration, budget management, API bridging |
| **Ajay** | Remediation & Evidence Engine | F2 evidence validator, state leakage logic, polyglot audit fixes (20 files) |
| **Akash** | Fullstack & Sync Lead | Frontend/backend route integration, branch synchronization, bug fixes (10 files) |
| **Jostan** | Ingestion & Harness Lead | Archive zip upload validation, git scanning service, remediation route verification |
| **Nikhil** | Environment & Documentation Lead | Dependency environments, main branch merges, presentation prompt formulation |

👉 **Full catalog, token context lengths, and task IDs are documented in [`bob_sessions/README.md`](bob_sessions/README.md)**.

---

## 🔒 Security & Compliance

FlakeGuard adheres strictly to the IBM Watsonx Hackathon security guidelines:
- **Zero Exposed Credentials**: Protected by [`.bobignore`](.bobignore) and [`.gitignore`](.gitignore).
- **Environment Isolation**: Private personal access tokens and keys are never hardcoded or sent across public routes.
- **Security Guide**: Review [`SECURITY.MD`](SECURITY.MD) for full compliance instructions.

---

## 👥 FlakeGuard Team
- **Aditya**
- **Ajay**
- **Akash**
- **Jostan**
- **Nikhil**

---

## 📄 License & Attribution

This project is licensed under the MIT License. Developed in conjunction with the IBM Bob AI Assistant platform.
