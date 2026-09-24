# FraudFusion — Explainable Fraud Detection Platform

FraudFusion is a unified, explainable fraud-detection platform designed to aggregate multiple signal domains into a single, transparent **0–100 Risk Score**, actionable **Risk Band**, recommended action, human-readable explanation, and automated **STR (Suspicious Transaction Report)** output.

---

## 🏛️ System Architecture

FraudFusion is designed around a modular, deterministic risk pipeline:

```
[ Data Ingestion & Validation ] ──> [ Signal Extraction ] ──> [ Composite Scoring Engine ] ──> [ STR & UI Output ]
  ├── Adaptive Friction (JSON)          ├── Adaptive Friction (AF: 45%)
  ├── Fund Flow (CSV)                   ├── Fund Flow (FF: 35%)
  └── Phishing Events (JSON)            └── Phishing Signals (PH: 20%)
```

### Module Directory Structure

```
FraudFusion/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/            # Ingestion, Health & Configuration endpoints
│   │   │       ├── config.py
│   │   │       ├── health.py
│   │   │       └── ingest.py  # File upload & batch query endpoints
│   │   ├── core/              # Config (YAML), SQLite DB, logging, error handling
│   │   ├── schemas/           # Pydantic schemas (Transactions, Ingestion, Signals)
│   │   ├── services/
│   │   │   ├── parsers/       # Modular parsers (AF JSON, FF CSV, PH JSON)
│   │   │   ├── ingestion.py   # Ingestion orchestrator service
│   │   │   ├── validator.py   # Strict record validation & logging
│   │   │   ├── persistence.py # SQLite database repository
│   │   │   └── base.py
│   │   └── main.py            # Thin FastAPI entry point
│   ├── config/
│   │   └── risk_config.yaml   # Configurable signal group weights and 0–100 risk bands
│   ├── tests/                 # Comprehensive Pytest suite (Parsers, Validation, Ingestion, API)
│   ├── .env.example           # Environment template
│   ├── pyproject.toml         # Pytest & Ruff configuration
│   └── requirements.txt       # Pinned backend dependencies (Python 3.13)
├── frontend/
│   ├── src/
│   │   ├── components/        # Header, SystemStatus, RiskConfigCard, IngestionPanel
│   │   ├── index.css          # Minimalist financial security UI design system
│   │   └── App.jsx            # Tabbed application shell
│   ├── package.json           # Pinned React + Vite dependencies
│   └── vite.config.js
├── .env.example
└── README.md
```

---

## 📥 Unified Data Ingestion & Validation Layer

FraudFusion ingests raw transaction and signal data from three primary source domains:

1. **Adaptive Friction (JSON)**: Session anomaly scores, biometric friction metrics, step-up authentication failures.
2. **Fund Flow (CSV)**: Account transfer logs, 24h velocity metrics, structuring indicators, mule scores.
3. **Phishing Events (JSON)**: Domain similarity scores, link urgency levels, credential harvesting flags.

### Key Ingestion Principles
- **Strict Validation**: Required fields (`transaction_id`, `account_id`, `recipient_id`, `amount > 0.0`) are enforced using Pydantic. Invalid records are rejected cleanly without silent fixes.
- **Structured Error Reporting**: Rejections return exact record index, reference ID, failing field, and specific reason.
- **Canonical Normalization**: All valid inputs are normalized into `CanonicalTransaction` models while preserving raw signal factors in `source_metadata`.
- **SQLite Audit Persistence**: Batches and validation errors are stored in SQLite (`data/fraud_fusion.db`).

---

## ⚙️ Risk Engine Configuration

Signal weights and score boundaries are strictly externalized in `backend/config/risk_config.yaml`:

- **Signal Group Weights**:
  - **Adaptive Friction (`AF`)**: `0.45` (45%)
  - **Fund Flow (`FF`)**: `0.35` (35%)
  - **Phishing (`PH`)**: `0.20` (20%)
- **Factor Clipping**: All individual signal factors are clipped to `[0.0, 1.0]`.
- **Risk Bands**:
  - `0–20`: **Very Low** (`ALLOW`)
  - `21–40`: **Low** (`MONITOR`)
  - `41–60`: **Medium** (`CHALLENGE`)
  - `61–80`: **High** (`HOLD`)
  - `81–100`: **Critical** (`BLOCK_AND_REPORT`)

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
- Ingest Upload API: `POST http://127.0.0.1:8000/api/v1/ingest/upload`

#### API Ingestion Usage Example (`curl`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/ingest/upload" \
  -F "file=@sample_fund_flow.csv" \
  -F "source_type=FUND_FLOW"
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

## 📌 Milestone Status & Scope

- **Milestone 1 Foundation**: Project structure, PyYAML config, Pydantic schemas, logging, health check, unit test harness, minimalist UI shell.
- **Milestone 2 Ingestion & Validation (Completed)**: Modular input parsers (AF JSON, FF CSV, PH JSON), strict Pydantic validation, structured error reporting, canonical transaction normalization, SQLite audit persistence, `/api/v1/ingest` endpoints, and UI upload experience.
- **Future Milestones**: Unified scoring engine, signal group evaluation (AF, FF, PH formulas), STR generator, interactive evaluation dashboard.
