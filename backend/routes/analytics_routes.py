"""
routes/analytics_routes.py
=============================
Powers the Analytics page: attendance distribution, department/semester/
subject comparisons, monthly trend, correlation matrix, feature
importance, and side-by-side ML model comparison tables.

Design choice: rather than recomputing correlation/EDA statistics from
scratch on every request (expensive over 20k+ rows), this route reads the
precomputed artifacts written by `analysis/eda.py` and the `ml/train_*`
scripts, and combines them with a few cheap live DB aggregates (via the
same helpers used by faculty_routes, kept DRY). Re-run those scripts to
refresh the analytics data after the dataset changes materially.
"""

from __future__ import annotations

import json
import os
from typing import List

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import Student, get_db
from models import (
    AnalyticsOverviewOut,
    CorrelationPair,
    FeatureImportanceEntry,
    ModelComparisonEntry,
    MonthlyTrendPoint,
)
from routes.faculty_routes import _department_stats, _subject_stats
import ml.predict as predict_module

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS_DIR = os.path.join(BACKEND_DIR, "analysis")
METRICS_DIR = os.path.join(BACKEND_DIR, "ml", "metrics")

EDA_SUMMARY_PATH = os.path.join(ANALYSIS_DIR, "eda_summary.json")
RISK_METRICS_PATH = os.path.join(METRICS_DIR, "risk_model_metrics.json")
FORECAST_METRICS_PATH = os.path.join(METRICS_DIR, "forecast_model_metrics.json")

MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _load_json(path: str, label: str) -> dict:
    if not os.path.exists(path):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{label} artifact not found. Run the corresponding generation script in backend/ first.",
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _flatten_correlation_matrix(corr_dict: dict) -> List[CorrelationPair]:
    """
    Flatten the nested {feature: {feature: value}} correlation dict from
    eda_summary.json into the upper triangle only (excluding the diagonal),
    since correlation is symmetric and self-correlation is always 1.0.
    """
    features = list(corr_dict.keys())
    pairs = []
    for i, feat_a in enumerate(features):
        for feat_b in features[i + 1:]:
            value = corr_dict[feat_a].get(feat_b)
            if value is not None:
                pairs.append(CorrelationPair(feature_a=feat_a, feature_b=feat_b, correlation=round(float(value), 3)))
    return pairs


def _attendance_distribution(db: Session) -> List[float]:
    """
    Bucket every student's overall attendance % into 10 fixed-width bins
    (0-10, 10-20, ..., 90-100) and return the bin counts, which is a
    compact representation a bar/histogram chart can render directly.
    """
    values = [v for (v,) in db.query(Student.overall_attendance_percentage).all() if v is not None]
    if not values:
        return [0.0] * 10
    counts, _ = np.histogram(values, bins=10, range=(0, 100))
    return [float(c) for c in counts]


def _risk_model_comparison(risk_metrics: dict) -> List[ModelComparisonEntry]:
    entries = []
    for m in risk_metrics.get("models", []):
        entries.append(
            ModelComparisonEntry(
                model_name=m["model_name"],
                accuracy=m.get("accuracy"),
                precision=m.get("precision"),
                recall=m.get("recall"),
                f1_score=m.get("f1_score"),
            )
        )
    return entries


def _forecast_model_comparison(forecast_metrics: dict) -> List[ModelComparisonEntry]:
    entries = []
    for m in forecast_metrics.get("models", []):
        entries.append(
            ModelComparisonEntry(
                model_name=m["model_name"],
                mae=m.get("mae"),
                rmse=m.get("rmse"),
                r2_score=m.get("r2_score"),
            )
        )
    return entries


def _feature_importance() -> List[FeatureImportanceEntry]:
    """Pull live feature importances from the already-loaded risk model."""
    try:
        bundle = predict_module._registry.risk_bundle
    except FileNotFoundError:
        return []
    model = bundle["model"]
    columns = bundle["feature_columns"]
    if not hasattr(model, "feature_importances_"):
        return []
    return [
        FeatureImportanceEntry(feature=col, importance=round(float(imp), 4))
        for col, imp in sorted(zip(columns, model.feature_importances_), key=lambda x: -x[1])
    ]


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@router.get("/overview", response_model=AnalyticsOverviewOut)
def get_analytics_overview(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsOverviewOut:
    """Single aggregate payload powering the entire Analytics page."""
    eda_summary = _load_json(EDA_SUMMARY_PATH, "EDA summary")
    risk_metrics = _load_json(RISK_METRICS_PATH, "Risk model metrics")
    forecast_metrics = _load_json(FORECAST_METRICS_PATH, "Forecast model metrics")

    monthly_trend = [
        MonthlyTrendPoint(month=m, attendance_percentage=eda_summary["monthly_avg_attendance"].get(m, 0.0))
        for m in MONTH_ORDER
        if m in eda_summary.get("monthly_avg_attendance", {})
    ]

    return AnalyticsOverviewOut(
        attendance_distribution=_attendance_distribution(db),
        department_comparison=_department_stats(db),
        semester_comparison={str(k): v for k, v in eda_summary.get("semester_avg_attendance", {}).items()},
        subject_comparison=_subject_stats(db),
        monthly_trend_overall=monthly_trend,
        correlation_matrix=_flatten_correlation_matrix(eda_summary.get("correlation_matrix", {})),
        feature_importance=_feature_importance(),
        risk_model_comparison=_risk_model_comparison(risk_metrics),
        forecast_model_comparison=_forecast_model_comparison(forecast_metrics),
    )


@router.get("/summary")
def get_raw_eda_summary(current_user=Depends(get_current_user)) -> dict:
    """Return the raw EDA summary JSON as-is, for advanced/debug frontend use."""
    return _load_json(EDA_SUMMARY_PATH, "EDA summary")
