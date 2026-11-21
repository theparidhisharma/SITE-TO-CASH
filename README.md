# Site-to-Cash

AI-powered commercial change intelligence for construction subcontractors. Converts informal construction-site instructions (voice notes, text, and photos) into contract-aware, evidence-backed potential variation cases.

> **Current Status:** Phase 7 — Commercial guardrails, independent source-grounding validation, AI reliability tests, upload/secret security hardening, and 14-step synthetic E2E verification complete. See [CHECKLIST.md](./CHECKLIST.md) and [STATUS.md](./STATUS.md).

## Prototype Security & Authentication Notice

> [!WARNING]
> **Not production-ready for multi-customer confidential data:** Authentication, session tokens, and user/tenant RBAC are **not implemented** in this prototype. API endpoints scope records using caller-supplied `project_id` parameters and fail closed on cross-project resource IDs, but an unauthenticated caller who knows or guesses a `project_id` and IDs is not blocked by an identity layer. Add real authentication and tenant authorization before hosting confidential or multi-organization data.

## Non-Negotiable Commercial Guardrails

1. **No fabricated data:** Never invent rates, quantities, contract clauses, or approvals.
2. **Mandatory source references:** Every extracted contract clause or BOQ match must cite its exact document, page/clause or sheet/row, and verbatim excerpt.
3. **Deterministic calculations:** All monetary quantities, rates, and subtotals are computed in deterministic Python (`Decimal`), never by an LLM.
4. **AI suggestions vs. human decisions:** AI outputs are explicitly tagged `ai_suggestion` and require Quantity Surveyor (QS) review/confirmation (`human_qs_decision`) before becoming confirmed commercial records.
5. **Labelled demo data:** Sample contracts, BOQs, and cases are only used when explicitly flagged `is_demo=true` and badged **DEMO DATA**.
6. **No hardcoded secrets:** API keys (such as `GEMINI_API_KEY`) live strictly in `.env` or environment / Secret Manager variables.

## Minimal Architecture

```text
+-----------------------------------+
|   Frontend (React + TypeScript)   |
|   Vite dev server (:5173)         |
|   Proxy /api -> :8000             |
+-----------------+-----------------+
                  | HTTP / JSON
                  v
+-----------------------------------+
|     Backend (Python + FastAPI)    |
|     /api/health, /documents,      |
|     /cases, /assessments,         |
|     /review, /report, /dashboard  |
+--------+-----------------+--------+
         |                 |
         v                 v
+----------------+  +------------------------+
| Services       |  | Storage Abstractions   |
| - Doc Parser   |  | FileStore +            |
| - Gemini Ext.  |  +-----------+------------+
| - Retrieval &  |              |
|   Assess (Ph4) |      +-------+-------+
| - Calc   (Ph5) |      |               |
| - Report (Ph6) |      v               v
| - Lc/Dash(Ph6) | Local FS / JSON   (Phase 8 GCP)
| - Ground/(Ph7) | backend/data/     GCS + Firestore
|   Security     |
```

## Folder Structure

```text
site-to-cash/
├── .env.example
├── .gitignore
├── CHECKLIST.md
├── README.md
├── STATUS.md
├── backend/
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── assessments.py
│   │   │       ├── cases.py
│   │   │       ├── documents.py
│   │   │       ├── health.py
│   │   │       ├── reports.py
│   │   │       └── reviews.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── calculator.py
│   │   │   ├── document_parser.py
│   │   │   ├── gemini_client.py
│   │   │   ├── grounding.py
│   │   │   ├── lifecycle.py
│   │   │   ├── report_generator.py
│   │   │   ├── retrieval.py
│   │   │   └── security.py
│   │   └── storage/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       └── local.py
│   └── tests/
│       ├── __init__.py
│       ├── test_assessments.py
│       ├── test_documents.py
│       ├── test_health.py
│       ├── test_instructions.py
│       ├── test_phase7_e2e_workflow.py
│       ├── test_phase7_guardrails_and_security.py
│       ├── test_reports_and_register.py
│       └── test_reviews.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── styles.css
│       ├── vite-env.d.ts
│       ├── api/
│       │   └── client.ts
│       ├── components/
│       │   ├── AssessmentTab.tsx
│       │   ├── InstructionTab.tsx
│       │   ├── QsReviewTab.tsx
│       │   └── RegisterTab.tsx
│       └── types/
│           └── domain.ts
└── samples/
    ├── README.md
    ├── demo_boq_sample.xlsx
    └── demo_subcontract_sample.pdf
```

## Prerequisites

- **Python** 3.11+
- **Node.js** 20+ (verified with Node v22.13.1 / npm 10.9.2)
- **Google Gemini API Key** (needed starting Phase 3; optional during Phase 1)

## Local Setup & Run Instructions

### 1. Configure environment variables

Copy `.env.example` to `.env`:

**Windows PowerShell:**
```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

Fill in `GEMINI_API_KEY` in `.env` when ready for Phase 3+. Leave `STORAGE_BACKEND=local` for local development.

### 2. Backend setup & run (FastAPI on port 8000)

**Windows PowerShell:**
```powershell
python -m venv backend\.venv
backend\.venv\Scripts\pip.exe install -r backend\requirements.txt
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

**macOS / Linux:**
```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/uvicorn app.main:app --app-dir backend --reload --port 8000
```

API health endpoint: `http://127.0.0.1:8000/api/health`

### 3. Frontend setup & run (React + Vite on port 5173)

In a second terminal from the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser. Vite proxies `/api/*` requests to `http://127.0.0.1:8000`.

### 4. Running Tests & Build Checks

**Backend tests (PowerShell):**
```powershell
backend\.venv\Scripts\python.exe -m pytest -c backend\pytest.ini backend\tests -v
```

**Backend tests (macOS / Linux):**
```bash
backend/.venv/bin/python -m pytest -c backend/pytest.ini backend/tests -v
```

**Frontend typecheck & build:**
```bash
cd frontend
npm run build
```


## Vercel deployment (multi-service)

The repository includes a root-level `vercel.json` that deploys two public services:

- `backend`: FastAPI application rooted at `backend/`, entrypoint `app.main:app`.
- `frontend`: Vite application rooted at `frontend/`.
- `/api` and `/api/*` are routed to the backend. All other paths are routed to the frontend.
- No private/internal service bindings are required. The frontend uses same-origin `/api/...` requests.

### Import into Vercel

1. Push this repository to GitHub.
2. In Vercel, import the repository.
3. Select the **Services** framework/preset if prompted and keep the project root at the repository root (`./`).
4. Add `GEMINI_API_KEY` in the Vercel project's Environment Variables for each environment where AI features should run. Do not commit secrets or `.env`.
5. Deploy.

The frontend's `VITE_API_BASE_URL` may remain unset because requests use same-origin `/api` routes.

### Important persistence and security limitations

> [!WARNING]
> This repository is a prototype and is **not ready for confidential multi-customer production data**. Authentication, session tokens, and user/tenant RBAC are not implemented. Do not expose sensitive customer contracts, project records, or commercial documents to an untrusted public deployment.

The backend's local JSON/file storage is not durable on Vercel. The deployment-specific default uses `/tmp/site-to-cash` so writes do not target the read-only function bundle, but `/tmp` is temporary, can be cleared, and is not shared durable storage across function instances. Records and uploaded files may disappear or be unavailable on later requests.

`STORAGE_BACKEND=gcp` is not a ready-to-use persistence option in this repository; the GCS/Firestore adapter is not implemented. Before relying on this deployment for real records, implement and configure durable object storage and database adapters, then add authentication and tenant-level authorization. Do not treat the `/tmp` fallback as a production data solution.

### Deployment checks

Run locally before deploying:

```bash
cd frontend
npm install
npm run build
cd ..
```

```bash
python -m venv .venv
# Activate the virtual environment, then:
pip install -r backend/requirements.txt
python -m pytest -c backend/pytest.ini backend/tests -v
```

