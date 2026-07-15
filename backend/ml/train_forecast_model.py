"""
train_forecast_model.py
========================
Model 2: Attendance Percentage Forecast.

Predicts a student's projected semester-end attendance percentage from
current standing + rate-of-change, so faculty/students can see where a
student is trending toward, not just where they are today.

Target construction (avoiding trivial leakage):
    We do NOT simply predict the current attendance value from itself.
    Using the real 6-month (Jan-Jun) attendance series in
    `monthly_attendance.csv`, we fit a per (student, subject) linear trend
    (`numpy.polyfit`) and extrapolate it 2 months forward with added
    noise. That extrapolated value is the regression TARGET -- a genuine,
    trend-grounded forecast rather than a restatement of the input.

Features (deliberately kept inference-friendly -- computable from a
single snapshot, matching what the API/frontend can realistically supply):
    - current_attendance    : latest known attendance %
    - previous_attendance   : previous semester attendance %
    - leaves_taken
    - internal_marks
    - distance_km
    - trend_rate            : (current_attendance - previous_attendance) / 6
                               -- an inference-time-computable proxy for the
                               true monthly slope used to build the target.

Algorithms compared:
    - LinearRegression
    - RandomForestRegressor

Evaluation: MAE, RMSE, R^2.

Artifacts written:
    backend/ml/saved_models/forecast_model.pkl
    backend/ml/metrics/forecast_model_metrics.json
    backend/analysis/plots/forecast_actual_vs_predicted.png
    backend/analysis/plots/forecast_residuals.png
    backend/analysis/plots/forecast_model_comparison.png
    backend/analysis/plots/forecast_feature_importance.png

Usage:
    python train_forecast_model.py
"""

from __future__ import annotations

import json
import os
from typing import Any

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_DATASET_PATH = os.path.join(BACKEND_DIR, "dataset", "attendance_dataset.csv")
MONTHLY_DATASET_PATH = os.path.join(BACKEND_DIR, "dataset", "monthly_attendance.csv")

SAVED_MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_models")
METRICS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metrics")
PLOTS_DIR = os.path.join(BACKEND_DIR, "analysis", "plots")

os.makedirs(SAVED_MODELS_DIR, exist_ok=True)
os.makedirs(METRICS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

FORECAST_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "forecast_model.pkl")
METRICS_PATH = os.path.join(METRICS_DIR, "forecast_model_metrics.json")

FEATURE_COLUMNS = [
    "current_attendance",
    "previous_attendance",
    "leaves_taken",
    "internal_marks",
    "distance_km",
    "trend_rate",
]

MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
RANDOM_STATE = 42


# --------------------------------------------------------------------------
# Data loading / feature + target engineering
# --------------------------------------------------------------------------

def _fit_monthly_slope(row: pd.Series) -> float:
    """Fit a linear trend across the 6 monthly attendance points."""
    y = row[MONTH_ORDER].values.astype(float)
    x = np.arange(len(MONTH_ORDER))
    slope = np.polyfit(x, y, 1)[0]
    return float(slope)


def build_dataset(
    main_csv: str = MAIN_DATASET_PATH,
    monthly_csv: str = MONTHLY_DATASET_PATH,
    seed: int = RANDOM_STATE,
) -> pd.DataFrame:
    """
    Merge the main dataset with the monthly trend series and construct
    the forecast target via real trend extrapolation.
    """
    main_df = pd.read_csv(main_csv)
    monthly_df = pd.read_csv(monthly_csv)

    # Pivot monthly data to wide format: one row per (Student_ID, Subject)
    wide = monthly_df.pivot_table(
        index=["Student_ID", "Subject"], columns="Month", values="Attendance_Percentage"
    ).reset_index()
    wide = wide[["Student_ID", "Subject"] + MONTH_ORDER]  # enforce column order

    # Fit real monthly slope per (student, subject)
    wide["monthly_slope"] = wide.apply(_fit_monthly_slope, axis=1)

    merged = main_df.merge(wide[["Student_ID", "Subject", "monthly_slope"]], on=["Student_ID", "Subject"], how="inner")

    rng = np.random.default_rng(seed)

    df = pd.DataFrame(
        {
            "current_attendance": merged["Attendance_Percentage"],
            "previous_attendance": merged["Previous_Attendance_Percentage"],
            "leaves_taken": merged["Leaves_Taken"],
            "internal_marks": merged["Internal_Marks"],
            "distance_km": merged["Distance_KM"],
            # Inference-friendly proxy for rate of change (computable from a
            # single snapshot: current vs previous semester, spread over ~6 months)
            "trend_rate": (merged["Attendance_Percentage"] - merged["Previous_Attendance_Percentage"]) / 6.0,
        }
    )

    # Ground-truth target: extrapolate the REAL monthly slope 2 months
    # forward from the current value, with a little realistic noise.
    noise = rng.normal(0, 1.5, size=len(merged))
    target = merged["Attendance_Percentage"] + merged["monthly_slope"] * 2 + noise
    df["forecast_attendance_percentage"] = np.clip(target, 30, 100).round(2)

    return df


# --------------------------------------------------------------------------
# Training / Evaluation
# --------------------------------------------------------------------------

def train_models(X_train: pd.DataFrame, y_train: np.ndarray) -> dict[str, Any]:
    linear_model = LinearRegression()
    linear_model.fit(X_train, y_train)

    rf_model = RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        min_samples_leaf=8,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    rf_model.fit(X_train, y_train)

    return {"LinearRegression": linear_model, "RandomForestRegressor": rf_model}


def evaluate_model(model: Any, model_name: str, X_test: pd.DataFrame, y_test: np.ndarray) -> dict[str, Any]:
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = r2_score(y_test, y_pred)

    return {
        "model_name": model_name,
        "mae": round(float(mae), 4),
        "rmse": round(rmse, 4),
        "r2_score": round(float(r2), 4),
    }


def plot_actual_vs_predicted(model: Any, model_name: str, X_test: pd.DataFrame, y_test: np.ndarray) -> None:
    y_pred = model.predict(X_test)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(y_test, y_pred, alpha=0.15, s=10, color="#2563eb")
    lims = [min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())]
    ax.plot(lims, lims, color="red", linestyle="--", lw=1.5, label="Perfect prediction")
    ax.set_xlabel("Actual Forecast Attendance %")
    ax.set_ylabel("Predicted Forecast Attendance %")
    ax.set_title(f"Actual vs Predicted — {model_name}")
    ax.legend()
    fig.tight_layout()

    out_path = os.path.join(PLOTS_DIR, f"forecast_actual_vs_predicted_{model_name.lower()}.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_residuals(model: Any, model_name: str, X_test: pd.DataFrame, y_test: np.ndarray) -> None:
    y_pred = model.predict(X_test)
    residuals = y_test - y_pred

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.hist(residuals, bins=40, color="#2563eb", edgecolor="white")
    ax.axvline(0, color="red", linestyle="--", lw=1.5)
    ax.set_xlabel("Residual (Actual - Predicted)")
    ax.set_ylabel("Frequency")
    ax.set_title(f"Residual Distribution — {model_name}")
    fig.tight_layout()

    out_path = os.path.join(PLOTS_DIR, f"forecast_residuals_{model_name.lower()}.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_model_comparison(all_metrics: list[dict[str, Any]]) -> None:
    names = [m["model_name"] for m in all_metrics]
    mae_vals = [m["mae"] for m in all_metrics]
    rmse_vals = [m["rmse"] for m in all_metrics]
    r2_vals = [m["r2_score"] for m in all_metrics]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, vals, title, color in zip(
        axes, [mae_vals, rmse_vals, r2_vals], ["MAE (lower better)", "RMSE (lower better)", "R² (higher better)"],
        ["#f59e0b", "#dc2626", "#16a34a"]
    ):
        bars = ax.bar(names, vals, color=color)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, v, f"{v:.3f}", ha="center", va="bottom", fontsize=8)
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=20)

    fig.suptitle("Forecast Model Comparison")
    fig.tight_layout()

    out_path = os.path.join(PLOTS_DIR, "forecast_model_comparison.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_feature_importance(model: Any, feature_names: list[str]) -> None:
    if not hasattr(model, "feature_importances_"):
        return
    importances = model.feature_importances_
    order = np.argsort(importances)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(np.array(feature_names)[order], importances[order], color="#16a34a")
    ax.set_xlabel("Importance")
    ax.set_title("Feature Importance — RandomForestRegressor (Forecast)")
    fig.tight_layout()

    out_path = os.path.join(PLOTS_DIR, "forecast_feature_importance.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------
# Main pipeline
# --------------------------------------------------------------------------

def main() -> None:
    print("Building forecast dataset (merging monthly trend + main dataset)...")
    df = build_dataset()
    print(f"  Built {len(df):,} rows with features: {FEATURE_COLUMNS}")

    X = df[FEATURE_COLUMNS]
    y = df["forecast_attendance_percentage"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)
    print(f"  Train: {len(X_train):,} rows | Test: {len(X_test):,} rows")

    print("\nTraining models...")
    models = train_models(X_train, y_train)

    all_metrics = []
    for name, model in models.items():
        print(f"  Evaluating {name}...")
        metrics = evaluate_model(model, name, X_test, y_test)
        all_metrics.append(metrics)
        plot_actual_vs_predicted(model, name, X_test, y_test)
        plot_residuals(model, name, X_test, y_test)

    plot_model_comparison(all_metrics)
    plot_feature_importance(models["RandomForestRegressor"], FEATURE_COLUMNS)

    # Select best model by R^2 (higher = better fit)
    best_metrics = max(all_metrics, key=lambda m: m["r2_score"])
    best_model_name = best_metrics["model_name"]
    best_model = models[best_model_name]
    print(f"\nBest model selected: {best_model_name} "
          f"(R2={best_metrics['r2_score']}, MAE={best_metrics['mae']}, RMSE={best_metrics['rmse']})")

    bundle = {
        "model": best_model,
        "model_name": best_model_name,
        "feature_columns": FEATURE_COLUMNS,
    }
    joblib.dump(bundle, FORECAST_MODEL_PATH)
    print(f"Saved best model bundle -> {FORECAST_MODEL_PATH}")

    summary = {
        "best_model": best_model_name,
        "feature_columns": FEATURE_COLUMNS,
        "models": all_metrics,
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved metrics -> {METRICS_PATH}")

    print("\n=== Model Comparison ===")
    for m in all_metrics:
        print(f"  {m['model_name']:22s} | MAE: {m['mae']:.4f} | RMSE: {m['rmse']:.4f} | R2: {m['r2_score']:.4f}")


if __name__ == "__main__":
    main()
