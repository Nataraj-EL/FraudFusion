# FraudFusion — Explainable Fraud Detection Platform

FraudFusion is a unified, explainable fraud-detection platform designed to aggregate multiple signal domains into a single, transparent **0–100 Risk Score**, actionable **Risk Band**, recommended action, human-readable explanation, and automated **STR (Suspicious Transaction Report)** output.

---

## 🏛️ System Architecture

FraudFusion is designed around a modular, deterministic risk pipeline:

```
[ Synthetic Ingestion ] ──> [ Signal Extraction ] ──> [ Composite Scoring Engine ] ──> [ STR & UI Output ]
                                ├── Adaptive Friction (AF: 45%)
                                ├── Fund Flow (FF: 35%)
                                └── Phishing Signals (PH: 20%)
```

### Module Directory Structure

```
FraudFusion/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/            # Health & frontend-safe configuration endpoints
│   │   ├── core/              # Config management (YAML), logging, custom error handling
│   │   ├── schemas/           # Pydantic schemas (Transactions, Signals, Risk Assessments)
│   │   ├── services/          # Reserved pipeline service interfaces (Ingestion, Scoring)
│   │   └── main.py            # Thin FastAPI application entry point
│   ├── config/
│   │   └── risk_config.yaml   # Configurable signal group weights and 0–100 risk bands
│   ├── tests/                 # Pytest suite (Config loading, weight validation, schemas, endpoints)
│   ├── .env.example           # Environment template
│   ├── pyproject.toml         # Pytest & Ruff configuration
│   └── requirements.txt       # Pinned backend dependencies (Python 3.13)
├── frontend/
│   ├── src/
│   │   ├── components/        # Header, SystemStatus, RiskConfigCard
│   │   ├── index.css          # Minimalist financial security UI design system
│   │   └── App.jsx            # Application shell
│   ├── package.json           # Pinned React + Vite dependencies
│   └── vite.config.js
├── .env.example
└── README.md
```

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

## 📌 Current Milestone Scope

- **Included in Milestone 1 Foundation**:
  - Clean modular directory layout (`app/api`, `app/core`, `app/schemas`, `app/services`).
  - PyYAML configuration management with weight-sum and risk-band boundary validation.
  - Pydantic data schemas for transactions, signal factors (clipped 0–1), signal groups, and risk assessments.
  - Minimalistic React + Vite frontend application shell with clean financial security aesthetic.
  - Structured logging and domain error handling.
  - Comprehensive unit test suite with 100% pass rate.
  - Pinned dependency manifests and zero lint errors.
- **Excluded (Future Milestones)**: Complete fraud scoring rules, synthetic data generator, STR report generator, and interactive evaluation dashboard.
