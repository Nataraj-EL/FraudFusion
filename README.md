# FraudFusion — Explainable Fraud Detection Platform

FraudFusion is a unified, explainable fraud-detection platform designed to aggregate multiple signal domains into a single, transparent **0–100 Risk Score**, actionable **Risk Band**, recommended action, human-readable explanation, automated **STR (Suspicious Transaction Report)** draft, and export options (JSON, CSV, HTML, PDF).

---

## 🏛️ System Architecture

FraudFusion is designed around a modular, deterministic risk pipeline:

```
[ Data Ingestion & Validation ] ──> [ Signal Engines ] ──> [ Risk Engine ] ──> [ Report & STR Service ] ──> [ UI & Export ]
  ├── Adaptive Friction (JSON)        ├── AF1, AF2, AF3      ├── AF Subscore (45%)    ├── Human Risk Report         ├── Interactive UI
  ├── Fund Flow (CSV)                 ├── FF1, FF2, FF3      ├── FF Subscore (35%)    ├── STR Draft (High/Critical) ├── JSON Export
  └── Phishing Events (JSON)          └── PH1, PH2, PH3      ├── PH Subscore (20%)    └── Evidence & Identifiers   ├── CSV Export
                                                             └── 0-100 Score & Band                                └── HTML/PDF Report
```

### Module Directory Structure

```
FraudFusion/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/            # Ingestion, Health, Config, Signals, Risk & Reports endpoints
│   │   │       ├── config.py
│   │   │       ├── health.py
│   │   │       ├── ingest.py   # File upload & batch query endpoints
│   │   │       ├── reports.py  # [NEW] Report generation, download & export endpoints
│   │   │       ├── risk.py     # Unified Risk Score API endpoint
│   │   │       └── signals.py  # Signal engine evaluation endpoint
│   │   ├── core/               # Config (YAML), SQLite DB, logging, error handling
│   │   ├── schemas/            # Pydantic schemas (Transactions, Ingestion, Signals, Risk, Reports)
│   │   │   └── report.py       # [NEW] RiskReport & STRDraft Pydantic schemas
│   │   ├── services/
│   │   │   ├── parsers/        # Modular parsers (AF JSON, FF CSV, PH JSON)
│   │   │   ├── signals/        # Independent signal evaluation engines (AF, FF, PH)
│   │   │   ├── report_service.py # [NEW] Report builder, STR generator & JSON/CSV/HTML export
│   │   │   ├── risk_engine.py  # Consolidated scoring & decision engine
│   │   │   ├── ingestion.py    # Ingestion orchestrator service
│   │   │   ├── validator.py    # Strict record validation & logging
│   │   │   └── persistence.py  # SQLite database repository (Ingestion & Reports)
│   │   └── main.py             # Thin FastAPI entry point
│   ├── config/
│   │   └── risk_config.yaml    # Configurable signal group weights, factor weights, and risk bands
│   ├── tests/                  # Comprehensive Pytest suite (53+ tests)
│   ├── .env.example            # Environment template
│   ├── pyproject.toml          # Pytest & Ruff configuration
│   └── requirements.txt        # Pinned backend dependencies (Python 3.13)
├── frontend/
│   ├── src/
│   │   ├── components/         # ReportExportModal, RiskAssessmentView, SignalInspector, IngestionPanel
│   │   ├── index.css           # Minimalist financial security UI design system
│   │   └── App.jsx             # Tabbed application shell
│   ├── package.json            # Pinned React + Vite dependencies
│   └── vite.config.js
├── .env.example
└── README.md
```

---

## 🧮 Consolidated Risk Scoring & Formulas

FraudFusion evaluates three independent signal domains and consolidates them into a unified 0–100 risk score without black-box models or generic LLMs. All weights and band boundaries are externalized in `backend/config/risk_config.yaml`.

$$\text{Consolidated Risk Score} = (\text{AF Subscore} \times 0.45) + (\text{FF Subscore} \times 0.35) + (\text{PH Subscore} \times 0.20)$$

---

## ⚙️ Risk Bands & Recommended Actions

Boundaries and actions are loaded dynamically from `backend/config/risk_config.yaml`:

| Score Range | Risk Band | Recommended Action | Action Description | STR Status |
|---|---|---|---|---|
| **0 – 20** | `Very Low` | `ALLOW` | Approve transaction without friction | `NOT_REQUIRED` |
| **21 – 40** | `Low` | `MONITOR` | Log transaction for background monitoring | `NOT_REQUIRED` |
| **41 – 60** | `Medium` | `CHALLENGE` | Require step-up 2FA/biometric verification | `NOT_REQUIRED` |
| **61 – 80** | `High` | `HOLD` | Pause transfer for compliance reviewer approval | `DRAFT_GENERATED` |
| **81 – 100** | `Critical` | `BLOCK_AND_REPORT` | Decline transfer & trigger STR draft | `DRAFT_GENERATED` |

---

## 📄 Explainable Reporting & STR Draft Generation

FraudFusion automatically converts completed risk assessments into human-readable compliance reports and regulatory drafts:

1. **Human-Readable Risk Report**:
   - Transaction & subject identifiers (`account_id`, `recipient_id`, `amount`, `currency`, `channel`, `payment_method`).
   - Consolidated score, risk band classification, and recommended action.
   - Subscores for Adaptive Friction, Fund Flow, and Phishing.
   - Triggered risk factor audit with plain-language math explanations.
   - Supporting evidence and raw metadata.

2. **Automated STR Draft Generation**:
   - Generated **ONLY** for `High` (61–80) and `Critical` (81–100) risk classifications.
   - For `Very Low`, `Low`, and `Medium` risk transactions, STR generation is skipped (`str_status: "NOT_REQUIRED"`).
   - Includes structured narrative sections: Subject & Transaction Identifiers, Composite Risk Scores, Anomaly Narrative & Evidence, and Regulatory Mandate Disclaimer.
   - Clearly labeled as `[DRAFT]` (unfiled) requiring compliance officer authorization prior to regulatory submission.

3. **Multi-Format Export Support**:
   - **JSON**: Full structured report object for automated downstream integration.
   - **CSV**: Concise summary table row for spreadsheet or database ingestion.
   - **HTML / PDF**: Standalone styled compliance report document optimized for printing and PDF saving.

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python**: `3.13+`
- **Node.js**: `v22+` / `npm 10+`

### 1. Backend Setup & Local Server

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Linux/macOS

# Install pinned dependencies
pip install -r requirements.txt

# Run FastAPI development server
uvicorn app.main:app --reload --port 8000
```
- API Documentation (Swagger): `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/v1/health`
- Config Endpoint: `http://127.0.0.1:8000/api/v1/config`
- Consolidated Risk Score API: `POST http://127.0.0.1:8000/api/v1/risk-score`
- Report Generation API: `POST http://127.0.0.1:8000/api/v1/reports/generate`
- Report Lookup API: `GET http://127.0.0.1:8000/api/v1/reports/{transaction_id}`
- Report Download API: `GET http://127.0.0.1:8000/api/v1/reports/{transaction_id}/download?format=json|csv|html|pdf`

#### API Usage Examples (`curl`)

##### Generate Report & STR Draft
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction": {
      "transaction_id": "TX-RPT-8801",
      "account_id": "ACC-SENDER-88",
      "recipient_id": "ACC-RECV-99",
      "amount": 3500.0,
      "currency": "USD",
      "channel": "MOBILE_APP"
    },
    "custom_metrics": {
      "device_fingerprint_changed": true,
      "distance_km": 1500.0,
      "retained_balance": 0.0,
      "total_sent": 3500.0,
      "domain_age_days": 10.0,
      "local_listing": "blacklist"
    }
  }'
```

##### Download HTML/PDF Compliance Report
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/reports/TX-RPT-8801/download?format=html" \
  -o "report_TX-RPT-8801.html"
```

---

### 2. Frontend Setup & Local Shell

```bash
cd frontend

# Install pinned dependencies
npm install

# Start Vite development server
npm run dev
```
- Frontend Application Shell: `http://127.0.0.1:5173`

---

## 🧪 Testing, Linting & Verification

### Backend Automated Testing (`pytest`)
```bash
cd backend
.venv/bin/pytest
```

### Backend Linting (`ruff`)
```bash
cd backend
.venv/bin/ruff check .
```

### Frontend Production Build
```bash
cd frontend
npm run build
```

---

## 📌 Milestone Status

- **Milestone 1 Foundation**: Project structure, PyYAML config, Pydantic schemas, logging, health check, unit test harness, minimalist UI shell.
- **Milestone 2 Ingestion & Validation**: Modular input parsers (AF JSON, FF CSV, PH JSON), strict validation, structured errors, SQLite audit persistence, `/api/v1/ingest` endpoints.
- **Milestone 3 Explainable Signal Engines**: Independent AF (AF1-3), FF (FF1-3), and PH (PH1-3) signal evaluation engines with field-specific explanations, externalized YAML factor weights, `POST /api/v1/signals/evaluate` endpoint, and Signal Inspector UI.
- **Milestone 4 Unified Risk Scoring & Decision Engine**: Consolidated 0–100 risk score, dynamic risk bands and recommended actions, deterministic explainability summary, `POST /api/v1/risk-score` endpoint, and minimal Risk Assessment UI.
- **Milestone 5 Explainable Reporting & Export**: Modular report service, deterministic STR draft generation for High/Critical bands, JSON/CSV/HTML/PDF exports, SQLite report persistence, `GET /api/v1/reports/{id}` & download endpoints, and interactive Report/Export UI modal.
- **Milestone 6 RBAC & Audit Trail (Completed)**: Role-based access control (Viewer, Analyst, Admin), lightweight local authentication with salted PBKDF2-HMAC-SHA256 password hashing, signed bearer session tokens, append-only SQLite `audit_logs` table, role-aware API authorization, login/audit views, and security dashboard.

---

## 🔐 Role-Based Access Control (RBAC) & Authentication

FraudFusion implements a lightweight, local authentication & authorization layer designed for security compliance without external infrastructure overhead.

### Default Development Users

On application startup, the platform automatically seeds three pre-configured development users if they do not already exist:

| Role | Email | Default Password | Granted Permissions |
|---|---|---|---|
| **Viewer** | `viewer@fraudfusion.io` | `ViewerPass123!` | Read-only access: view transactions, scores, and reports. |
| **Analyst** | `analyst@fraudfusion.io` | `AnalystPass123!` | All Viewer capabilities + evaluate risk, generate reports, generate STR drafts, and export reports. |
| **Admin** | `admin@fraudfusion.io` | `AdminPass123!` | All Analyst capabilities + manage users/roles + query tamper-evident audit logs. |

### Authentication Architecture
- **Password Hashing**: Salted `PBKDF2-HMAC-SHA256` with 100,000 iterations using Python's standard `hashlib`.
- **Session Tokens**: Cryptographically signed bearer tokens generated via `HMAC-SHA256` using externalized `JWT_SECRET_KEY` and `JWT_ALGORITHM`.
- **API Authorization**: Thin FastAPI dependencies (`require_roles(["admin"])`) enforce role constraints on all sensitive routes.

---

## 📜 Append-Only Audit Trail

FraudFusion captures all critical compliance and operational actions in a tamper-evident, append-only SQLite table (`audit_logs`).

### Audited Actions
- `USER_LOGIN`: User authentication attempts (success/failure)
- `INGEST_TRANSACTIONS`: Data file ingestion and batch parsing
- `EVALUATE_RISK`: Execution of the Unified Risk Scoring Engine
- `GENERATE_REPORT`: Creation of compliance risk reports
- `GENERATE_STR`: Automated drafting of Suspicious Transaction Reports (STRs)
- `VIEW_REPORT`: Inspection of transaction reports
- `EXPORT_REPORT`: Exporting risk assessments (JSON, CSV, HTML, PDF)
- `VIEW_AUDIT_LOGS`: Admin retrieval of audit trail records
- `CREATE_USER` / `LIST_USERS`: Admin user management operations

### Audit Record Schema
Each audit record captures:
- `timestamp`: ISO-8601 formatted UTC timestamp
- `user`: Account email of the executing user
- `role`: Role of the user at the time of execution (`viewer`, `analyst`, `admin`)
- `action`: Specific domain action executed
- `resource_type`: Type of resource accessed (`TRANSACTION`, `RISK_ENGINE`, `REPORT`, `AUDIT_LOG`, `USER`)
- `transaction_id`: Associated transaction ID (when applicable)
- `status`: Outcome (`SUCCESS`, `FAILURE`, `UNAUTHORIZED`)
- `metadata`: Supplemental details (e.g. risk score, export format, user created)

