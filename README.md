# Smart Attendance Pattern Analyzer

An AI-powered web application that analyzes student attendance, predicts attendance risk, forecasts future attendance, and provides actionable insights for both students and faculty.

Built to demonstrate the complete machine learning lifecycle: data generation → preprocessing → EDA → feature engineering → model training/evaluation → model serving → full-stack product.

![Architecture Overview](docs/diagrams/architecture.png)

---

## Features

### For Students
- Overall + subject-wise attendance breakdown
- Monthly attendance trend chart
- On-demand AI prediction: risk level, semester-end forecast, behavioural segment
- Personalized, rule-based recommendations ("attend your next 5 classes", "high risk of detention", etc.)
- Downloadable attendance report (PDF or CSV)

### For Faculty
- Institution-wide stats: total students, below-75% count, highest/lowest/average attendance
- Department and subject comparisons
- Top-10 defaulters, improving vs. declining students
- Risk distribution (Low / Medium / High) via the signature Risk Ledger Strip
- Student lookup by code, or "what-if" prediction with manual feature values
- Exportable class/department report (PDF or CSV)

### Machine Learning (3 models, 2 algorithms each, compared head-to-head)
| Model | Task | Algorithms Compared | Result |
|---|---|---|---|
| 1. Risk Classification | Low / Medium / High Risk | Decision Tree vs. **Random Forest** | 96.8% accuracy, F1 0.968 |
| 2. Attendance Forecast | Predict semester-end % | Linear Regression vs. **Random Forest Regressor** | R² 0.963, MAE 2.36 |
| 3. Student Segmentation | Excellent / Average / Critical | **K-Means** (k=3) | Silhouette 0.334 |

All three models are trained on a realistic, synthetically-generated dataset of **5,000 students** and **22,535 attendance records** across 6 departments, 8 semesters, and 30 subjects — see [`backend/dataset/DATA_DICTIONARY.md`](backend/dataset/DATA_DICTIONARY.md).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS + Recharts + Axios |
| Backend | FastAPI + Python 3.11+ |
| Machine Learning | scikit-learn, pandas, NumPy, joblib |
| Database | SQLite + SQLAlchemy ORM |
| Authentication | JWT (python-jose) + bcrypt password hashing |
| Reports | fpdf2 (PDF), built-in csv (CSV) |
| API Docs | Auto-generated Swagger/OpenAPI at `/docs` |

---

## Project Structure

```
smart-attendance-analyzer/
├── backend/
│   ├── app.py                  # FastAPI entrypoint
│   ├── database.py              # SQLAlchemy models + seeding
│   ├── models.py                 # Pydantic schemas
│   ├── auth.py                    # JWT + password hashing + RBAC
│   ├── routes/                     # auth, student, faculty, prediction, analytics, export
│   ├── ml/                          # train_model.py, train_forecast_model.py,
│   │                                 train_segmentation_model.py, predict.py, saved_models/, metrics/
│   ├── analysis/                    # eda.py + generated plots/
│   ├── dataset/                     # generate_dataset.py + generated CSVs
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/                   # Login, Register, Home, StudentDashboard, FacultyDashboard,
│       │                             PredictionPage, AnalyticsPage, Settings, Profile
│       ├── components/               # Card, Badge, Navbar, Sidebar, Loader, RiskLedgerStrip, EmptyState
│       ├── charts/                    # Line, Bar, Pie, Radar, Heatmap, GenericBar (Recharts)
│       ├── hooks/                      # useAuth, useTheme
│       ├── layouts/                     # AuthLayout, AppLayout
│       └── services/                    # api.ts (Axios client)
├── docs/                                # This documentation set
└── README.md
```

---

## Quick Start

See [`docs/INSTALLATION.md`](docs/INSTALLATION.md) for full step-by-step setup. Short version:

```bash
# 1. Backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

python dataset/generate_dataset.py     # generate the synthetic dataset
python database.py                      # create + seed the SQLite DB
python ml/train_model.py                 # train risk classification model
python ml/train_forecast_model.py         # train forecast regression model
python ml/train_segmentation_model.py      # train K-Means segmentation model
python analysis/eda.py                      # generate EDA charts

uvicorn app:app --reload                     # http://localhost:8000  (docs at /docs)

# 2. Frontend (new terminal)
cd frontend
npm install
cp .env.example .env
npm run dev                                    # http://localhost:5173
```

**Demo logins** (created automatically by the seeding script):

| Role | Username | Password |
|---|---|---|
| Student | `stu00001` | `student123` |
| Faculty | `fac0001` | `faculty123` |
| Admin | `admin` | `admin123` |

---

## Documentation

- [Installation Guide](docs/INSTALLATION.md) — detailed setup for backend + frontend
- [API Documentation](docs/API_DOCUMENTATION.md) — every endpoint, request/response shape
- [Architecture, ER Diagram & Flowchart](docs/ARCHITECTURE.md)
- [Project Report](docs/PROJECT_REPORT.md) — methodology, model results, design decisions
- [Data Dictionary](backend/dataset/DATA_DICTIONARY.md) — dataset column reference

---

## License

This is an educational/portfolio project. Free to use and adapt for learning purposes.
