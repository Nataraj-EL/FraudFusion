# FraudFusion — Explainable Fraud Detection Platform

FraudFusion is a unified, explainable fraud-detection platform designed to aggregate multiple signal domains into a single, transparent **0–100 Risk Score**, actionable **Risk Band**, recommended action, human-readable explanation, and automated **STR (Suspicious Transaction Report)** output.

---

## 🏛️ System Architecture

FraudFusion is designed around a modular, deterministic risk pipeline:

```
[ Data Ingestion & Validation ] ──> [ Signal Evaluation Engines ] ──> [ Composite Scoring Engine ] ──> [ STR & UI Output ]
  ├── Adaptive Friction (JSON)          ├── Adaptive Friction (AF1, AF2, AF3)
  ├── Fund Flow (CSV)                   ├── Fund Flow (FF1, FF2, FF3)
  └── Phishing Events (JSON)            └── Phishing Signals (PH1, PH2, PH3)
```

### Module Directory Structure

```
FraudFusion/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/            # Ingestion, Health, Config & Signals endpoints
│   │   │       ├── config.py
│   │   │       ├── health.py
│   │   │       ├── ingest.py  # File upload & batch query endpoints
│   │   │       └── signals.py # [NEW] Signal engine evaluation endpoint
│   │   ├── core/              # Config (YAML), SQLite DB, logging, error handling
│   │   ├── schemas/           # Pydantic schemas (Transactions, Ingestion, Signals)
│   │   ├── services/
│   │   │   ├── parsers/       # Modular parsers (AF JSON, FF CSV, PH JSON)
│   │   │   ├── signals/       # [NEW] Independent signal evaluation engines
│   │   │   │   ├── adaptive_friction.py (AF1, AF2, AF3)
│   │   │   │   ├── fund_flow.py         (FF1, FF2, FF3)
│   │   │   │   └── phishing.py          (PH1, PH2, PH3)
│   │   │   ├── ingestion.py   # Ingestion orchestrator service
│   │   │   ├── validator.py   # Strict record validation & logging
│   │   │   ├── persistence.py # SQLite database repository
│   │   │   └── base.py
│   │   └── main.py            # Thin FastAPI entry point
│   ├── config/
│   │   └── risk_config.yaml   # Configurable signal group & individual factor weights
│   ├── tests/                 # Comprehensive Pytest suite (38+ tests)
│   ├── .env.example           # Environment template
│   ├── pyproject.toml         # Pytest & Ruff configuration
│   └── requirements.txt       # Pinned backend dependencies (Python 3.13)
├── frontend/
│   ├── src/
│   │   ├── components/        # Header, SystemStatus, RiskConfigCard, IngestionPanel, SignalInspector
│   │   ├── index.css          # Minimalist financial security UI design system
│   │   └── App.jsx            # Tabbed application shell
│   ├── package.json           # Pinned React + Vite dependencies
│   └── vite.config.js
├── .env.example
└── README.md
```

---

## 🧮 Fraud Signal Engines & Mathematical Formulas

FraudFusion evaluates three independent signal domains without hiding formulas inside generic utilities. All individual factor weights are externalized in `backend/config/risk_config.yaml`.

### 1. Adaptive Friction (`AF`) Engine
Group Weight: `0.45`
- **AF1 (Device Fingerprint Delta)**: `1.0` if OS, browser, IP address, or user-agent differs from stored fingerprint, else `0.0`. (Weight: `0.50`)
- **AF2 (Geo Distance)**: `min(distanceKm / 1500.0, 1.0)`. (Weight: `0.30`)
- **AF3 (Amount vs Historical Mean)**: `max(0.0, min((amount - mean) / mean, 1.0))`. (Weight: `0.20`)

### 2. Fund Flow (`FF`) Engine
Group Weight: `0.35`
- **FF1 (Balanced Flow Ratio)**: `smaller(InDegree, OutDegree) / larger(InDegree, OutDegree)`. Returns `0.0` if larger is 0. (Weight: `0.45`)
- **FF2 (Near-zero Retained Balance)**: `1.0 - (RemainingBalance / TotalSent)`. Returns `0.0` if total_sent is 0. Clipped to `[0.0, 1.0]`. (Weight: `0.30`)
- **FF3 (Short Holding Time)**: `max(0.0, min(1.0, 1.0 - (HoldingMinutes / 60.0)))`. (Weight: `0.25`)

### 3. Phishing (`PH`) Engine
Group Weight: `0.20`
- **PH1 (Domain Age)**: `max(0.0, min(1.0, 1.0 - (age_days / 180.0)))`. (Weight: `0.40`)
- **PH2 (Certificate Quality)**: `1.0` if `selfSigned` is True OR `validity_days < 30`, else `0.0`. (Weight: `0.30`)
- **PH3 (Blacklist Hit)**: `1.0` if `localListing == "blacklist"`, else `0.0`. (Weight: `0.30`)

---

## ⚙️ Risk Engine Configuration

Signal group weights and factor weights are configured in `backend/config/risk_config.yaml`:

- **Signal Groups**:
  - `AF`: 45% composite weight
  - `FF`: 35% composite weight
  - `PH`: 20% composite weight
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
- Signal Evaluation API: `POST http://127.0.0.1:8000/api/v1/signals/evaluate`

#### API Signal Evaluation Usage Example (`curl`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/signals/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction": {
      "transaction_id": "TX-1001",
      "account_id": "ACC-101",
      "recipient_id": "ACC-202",
      "amount": 2500.0,
      "currency": "USD"
    },
    "custom_metrics": {
      "distance_km": 1200.0,
      "historical_mean_amount": 1000.0,
      "in_degree": 10,
      "out_degree": 10,
      "domain_age_days": 18.0
    }
  }'
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
- **Milestone 2 Ingestion & Validation**: Modular input parsers (AF JSON, FF CSV, PH JSON), strict validation, structured errors, SQLite audit persistence, `/api/v1/ingest` endpoints.
- **Milestone 3 Explainable Signal Engines (Completed)**: Independent AF (AF1-3), FF (FF1-3), and PH (PH1-3) signal evaluation engines with field-specific explanations, externalized YAML factor weights, `POST /api/v1/signals/evaluate` endpoint, and Signal Inspector UI.
- **Future Milestones**: Consolidated composite scoring engine (0-100 score, risk bands, actions), STR generator, interactive evaluation dashboard.
