# Installation Guide

This guide walks through setting up the Smart Attendance Pattern Analyzer from a completely clean clone.

## Prerequisites

| Tool | Minimum Version | Check with |
|---|---|---|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |

---

## 1. Backend Setup

### 1.1 Create a virtual environment

```bash
cd backend
python -m venv venv
```

Activate it:
```bash
# macOS / Linux
source venv/bin/activate

# Windows (Command Prompt)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

### 1.2 Install dependencies

```bash
pip install -r requirements.txt
```

### 1.3 Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and, at minimum, set a real `JWT_SECRET_KEY` for anything beyond local development:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Paste the output as the value of `JWT_SECRET_KEY` in `.env`.

### 1.4 Generate the synthetic dataset

```bash
python dataset/generate_dataset.py
```
This creates `dataset/attendance_dataset.csv` (22,535 rows), `dataset/monthly_attendance.csv`, `dataset/students_master.csv`, and `dataset/DATA_DICTIONARY.md`. Takes a few seconds.

Optional flags:
```bash
python dataset/generate_dataset.py --num-students 8000 --seed 7
```

### 1.5 Initialize and seed the database

```bash
python database.py
```
This creates `attendance.db` (SQLite), creates all tables, and loads the generated CSVs — including auto-creating login accounts for every student and faculty member (see the printed credentials at the end of the command's output).

### 1.6 Train the machine learning models

Run each training script once (they save their model bundles to `ml/saved_models/` and metrics to `ml/metrics/`):

```bash
python ml/train_model.py                # Risk classification (Decision Tree vs Random Forest)
python ml/train_forecast_model.py        # Attendance forecast (Linear Regression vs RF Regressor)
python ml/train_segmentation_model.py     # Student segmentation (K-Means)
```

### 1.7 Generate EDA charts (optional but recommended)

```bash
python analysis/eda.py
```
Produces correlation matrix, distributions, and comparison charts in `analysis/plots/`, and `analysis/eda_summary.json` (consumed by the `/api/analytics/overview` endpoint).

### 1.8 Start the API server

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Visit:
- **http://localhost:8000/docs** — interactive Swagger UI
- **http://localhost:8000/health** — health check

---

## 2. Frontend Setup

Open a new terminal (leave the backend running).

### 2.1 Install dependencies

```bash
cd frontend
npm install
```

### 2.2 Configure environment variables

```bash
cp .env.example .env
```
Leave `VITE_API_BASE_URL` blank to use the Vite dev-server proxy (which forwards `/api` to `http://localhost:8000` — see `vite.config.ts`). Only set it explicitly if your backend runs somewhere other than `localhost:8000`.

### 2.3 Start the dev server

```bash
npm run dev
```

Visit **http://localhost:5173**.

### 2.4 Log in

Use one of the demo accounts created during database seeding:

| Role | Username | Password |
|---|---|---|
| Student | `stu00001` | `student123` |
| Faculty | `fac0001` | `faculty123` |
| Admin | `admin` | `admin123` |

(Any student ID from `STU00001` to `STU05000` / faculty code from `FAC0001` to `FAC0006` will work, following the same password pattern.)

---

## 3. Building for Production

### Frontend
```bash
cd frontend
npm run build
```
Outputs a static bundle to `frontend/dist/` — serve it with any static file host (Nginx, Vercel, Netlify, etc.), pointing `VITE_API_BASE_URL` at your deployed backend.

### Backend
Run behind a production ASGI setup, e.g.:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```
Set real values for `JWT_SECRET_KEY` and `CORS_ORIGINS` in `.env` before deploying.

---

## 4. Re-running the Pipeline

If you want a fresh dataset or want to retrain models after changing feature engineering:

```bash
# Regenerate data (overwrites existing CSVs)
python dataset/generate_dataset.py --seed 99

# Re-seed the DB from scratch (drops and reloads all tables)
python -c "from database import init_db, seed_database; init_db(); seed_database(force=True)"

# Retrain all three models
python ml/train_model.py
python ml/train_forecast_model.py
python ml/train_segmentation_model.py

# Refresh EDA charts
python analysis/eda.py
```

---

## 5. Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` on backend start | Ensure the virtual environment is activated and `pip install -r requirements.txt` completed without errors. |
| Frontend shows network errors on every page | Confirm the backend is running on port 8000 and check `vite.config.ts`'s proxy target matches. |
| Login fails with "Incorrect username or password" | Confirm you ran `python database.py` to seed accounts, and usernames are lowercase (e.g. `stu00001`, not `STU00001`). |
| Dashboards show no data | Confirm `dataset/generate_dataset.py` was run *before* `database.py`, and that `database.py`'s seeding step completed (check for "Seeding complete." in its output). |
| `/api/prediction/predict` returns a 503-style "model not found" error | Run all three `ml/train_*.py` scripts — the API loads `.pkl` bundles from `ml/saved_models/` on first use. |
