"""
predict.py
==========
Unified inference module. Loads the three trained model bundles produced
by train_model.py / train_forecast_model.py / train_segmentation_model.py
exactly once (at import time), and exposes simple, typed functions that
`routes/prediction_routes.py` calls to serve predictions over the API.

Also implements the rule-based AI recommendation generator described in
the spec (e.g. "Attend next 5 classes continuously", "High risk of
detention", subject-specific advice, etc).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

import joblib
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Paths / model loading
# --------------------------------------------------------------------------

ML_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_MODELS_DIR = os.path.join(ML_DIR, "saved_models")

RISK_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "risk_model.pkl")
FORECAST_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "forecast_model.pkl")
SEGMENTATION_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "segmentation_model.pkl")


class ModelRegistry:
    """
    Lazily-loaded, process-wide singleton holding all three model bundles
    so we only pay the joblib deserialization cost once per server process
    rather than on every request.
    """

    def __init__(self) -> None:
        self._risk_bundle: Optional[dict] = None
        self._forecast_bundle: Optional[dict] = None
        self._segmentation_bundle: Optional[dict] = None

    @property
    def risk_bundle(self) -> dict:
        if self._risk_bundle is None:
            self._risk_bundle = self._load(RISK_MODEL_PATH, "risk")
        return self._risk_bundle

    @property
    def forecast_bundle(self) -> dict:
        if self._forecast_bundle is None:
            self._forecast_bundle = self._load(FORECAST_MODEL_PATH, "forecast")
        return self._forecast_bundle

    @property
    def segmentation_bundle(self) -> dict:
        if self._segmentation_bundle is None:
            self._segmentation_bundle = self._load(SEGMENTATION_MODEL_PATH, "segmentation")
        return self._segmentation_bundle

    @staticmethod
    def _load(path: str, label: str) -> dict:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"{label} model not found at {path}. "
                f"Run the corresponding training script in backend/ml/ first."
            )
        return joblib.load(path)


_registry = ModelRegistry()


# --------------------------------------------------------------------------
# Input container
# --------------------------------------------------------------------------

@dataclass
class StudentFeatures:
    """
    Canonical feature snapshot used across all three models. This is the
    single input shape the rest of the app (routes, recommendation engine)
    needs to construct, regardless of which model(s) will consume it.
    """
    current_attendance: float
    previous_attendance: float
    leaves_taken: int
    internal_marks: int
    distance_km: float
    monthly_attendance: float  # most recent month's attendance %


# --------------------------------------------------------------------------
# Model 1: Risk classification
# --------------------------------------------------------------------------

def predict_risk(features: StudentFeatures) -> dict:
    """
    Predict risk level (Low / Medium / High Risk) using the saved best
    classifier (Decision Tree or Random Forest, whichever won training).

    Returns:
        dict with keys: risk_level, model_used, confidence
    """
    bundle = _registry.risk_bundle
    model = bundle["model"]
    label_encoder = bundle["label_encoder"]
    feature_columns = bundle["feature_columns"]

    row = pd.DataFrame([{
        "current_attendance": features.current_attendance,
        "previous_attendance": features.previous_attendance,
        "leaves_taken": features.leaves_taken,
        "internal_marks": features.internal_marks,
        "distance_km": features.distance_km,
        "monthly_attendance": features.monthly_attendance,
    }])[feature_columns]

    pred_encoded = model.predict(row)[0]
    risk_level = label_encoder.inverse_transform([pred_encoded])[0]

    confidence = None
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(row)[0]
        confidence = round(float(np.max(proba)), 4)

    return {
        "risk_level": risk_level,
        "model_used": bundle["model_name"],
        "confidence": confidence,
    }


# --------------------------------------------------------------------------
# Model 2: Attendance forecast
# --------------------------------------------------------------------------

def predict_forecast(features: StudentFeatures) -> dict:
    """
    Predict projected semester-end attendance percentage.

    Returns:
        dict with keys: forecast_attendance_percentage, model_used
    """
    bundle = _registry.forecast_bundle
    model = bundle["model"]
    feature_columns = bundle["feature_columns"]

    trend_rate = (features.current_attendance - features.previous_attendance) / 6.0

    row = pd.DataFrame([{
        "current_attendance": features.current_attendance,
        "previous_attendance": features.previous_attendance,
        "leaves_taken": features.leaves_taken,
        "internal_marks": features.internal_marks,
        "distance_km": features.distance_km,
        "trend_rate": trend_rate,
    }])[feature_columns]

    forecast = float(model.predict(row)[0])
    forecast = round(float(np.clip(forecast, 0, 100)), 2)

    return {
        "forecast_attendance_percentage": forecast,
        "model_used": bundle["model_name"],
    }


# --------------------------------------------------------------------------
# Model 3: Student segmentation
# --------------------------------------------------------------------------

def predict_segment(
    avg_attendance: float,
    avg_leaves: float,
    avg_internal_marks: float,
    distance_km: float,
) -> str:
    """
    Predict which behavioural segment (Excellent / Average / Critical) a
    student's aggregate profile belongs to.
    """
    bundle = _registry.segmentation_bundle
    model = bundle["model"]
    scaler = bundle["scaler"]
    feature_columns = bundle["feature_columns"]
    label_mapping = bundle["cluster_label_mapping"]

    row = pd.DataFrame([{
        "avg_attendance": avg_attendance,
        "avg_leaves": avg_leaves,
        "avg_internal_marks": avg_internal_marks,
        "distance_km": distance_km,
    }])[feature_columns]

    scaled = scaler.transform(row)
    cluster_raw = int(model.predict(scaled)[0])

    # label_mapping keys may be int or str depending on (de)serialization path
    segment = label_mapping.get(cluster_raw, label_mapping.get(str(cluster_raw), "Average"))
    return segment


# --------------------------------------------------------------------------
# AI Recommendation Engine (rule-based)
# --------------------------------------------------------------------------

def generate_ai_recommendations(
    features: StudentFeatures,
    risk_level: str,
    forecast_attendance: float,
    segment: str,
    weakest_subject: Optional[str] = None,
) -> List[str]:
    """
    Generate human-readable, actionable recommendations from the combined
    model outputs. Rule-based (not another ML model) so the advice stays
    transparent, predictable, and easy to justify to end users.
    """
    tips: List[str] = []

    # --- Attendance threshold warnings ---
    if features.current_attendance < 75:
        classes_short = max(0, int(np.ceil((75 - features.current_attendance) / 2)))
        tips.append(
            f"Your attendance is below the 75% requirement. "
            f"Attend your next {max(classes_short, 5)} classes continuously to recover."
        )
    elif features.current_attendance < 80:
        tips.append("You're just above the minimum requirement — a few more absences could put you at risk.")

    # --- Forecast-based warning ---
    if forecast_attendance < 75 <= features.current_attendance:
        tips.append("Your attendance may drop below 75% if the current trend continues. Act now to stay safe.")
    elif forecast_attendance < features.current_attendance - 3:
        tips.append("Your projected attendance is trending downward. Consider reducing avoidable absences.")

    # --- Trend-based encouragement ---
    trend_rate = features.current_attendance - features.previous_attendance
    if trend_rate > 3:
        tips.append("Great progress — you are improving compared to last semester. Keep up the momentum!")
    elif trend_rate < -3:
        tips.append("Your attendance has declined compared to last semester. Try to identify what changed.")

    # --- Risk-level specific advice ---
    if risk_level == "High Risk":
        tips.append("You are at high risk of detention. Please speak with your faculty advisor as soon as possible.")
    elif risk_level == "Medium Risk":
        tips.append("You're in the medium risk zone — consistent attendance over the next few weeks will help.")
    else:
        tips.append("You're in the low risk zone. Maintain your current attendance habits.")

    # --- Leaves-specific advice ---
    if features.leaves_taken >= 10:
        tips.append("You've taken a high number of leaves this term. Limit further leaves unless necessary.")

    # --- Internal marks + attendance correlation nudge ---
    if features.internal_marks < 50 and features.current_attendance < 75:
        tips.append("Low attendance is likely affecting your internal marks. Improving one will help the other.")

    # --- Segment-specific framing ---
    if segment == "Critical":
        tips.append("Your overall profile places you in the Critical segment — prioritize attendance recovery this month.")
    elif segment == "Excellent":
        tips.append("You're in the Excellent segment among your peers. Keep it up!")

    # --- Subject-specific advice ---
    if weakest_subject:
        tips.append(f"'{weakest_subject}' has your lowest attendance — focus extra effort there.")

    # De-duplicate while preserving order, cap list length for UI readability
    seen = set()
    unique_tips = []
    for tip in tips:
        if tip not in seen:
            seen.add(tip)
            unique_tips.append(tip)

    return unique_tips[:6]


# --------------------------------------------------------------------------
# Combined convenience function
# --------------------------------------------------------------------------

def get_full_prediction(
    features: StudentFeatures,
    avg_leaves: Optional[float] = None,
    avg_internal_marks: Optional[float] = None,
    weakest_subject: Optional[str] = None,
) -> dict:
    """
    Run all three models for a single student snapshot and return a
    combined payload matching the `PredictionOut` API schema.
    """
    risk_result = predict_risk(features)
    forecast_result = predict_forecast(features)

    segment = predict_segment(
        avg_attendance=features.current_attendance,
        avg_leaves=avg_leaves if avg_leaves is not None else features.leaves_taken,
        avg_internal_marks=avg_internal_marks if avg_internal_marks is not None else features.internal_marks,
        distance_km=features.distance_km,
    )

    recommendations = generate_ai_recommendations(
        features=features,
        risk_level=risk_result["risk_level"],
        forecast_attendance=forecast_result["forecast_attendance_percentage"],
        segment=segment,
        weakest_subject=weakest_subject,
    )

    return {
        "predicted_risk_level": risk_result["risk_level"],
        "risk_model_used": risk_result["model_used"],
        "risk_confidence": risk_result["confidence"],
        "forecast_attendance_percentage": forecast_result["forecast_attendance_percentage"],
        "forecast_model_used": forecast_result["model_used"],
        "cluster_segment": segment,
        "ai_recommendations": recommendations,
    }


if __name__ == "__main__":
    # Simple smoke test using representative values
    sample = StudentFeatures(
        current_attendance=68.0,
        previous_attendance=74.0,
        leaves_taken=11,
        internal_marks=45,
        distance_km=18.5,
        monthly_attendance=65.0,
    )
    result = get_full_prediction(sample, avg_leaves=11, avg_internal_marks=45)
    import json
    print(json.dumps(result, indent=2))
