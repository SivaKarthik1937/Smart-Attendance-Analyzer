"""
train_model.py
===============
Model 1: Attendance Risk Classification.

Trains and compares two classifiers that predict a student's attendance
risk category (Low / Medium / High Risk) from behavioural features:

    Features:
        - Current Attendance %        (current_attendance)
        - Previous Semester Attendance % (previous_attendance)
        - Leaves Taken                (leaves_taken)
        - Internal Marks              (internal_marks)
        - Distance from College (km)  (distance_km)
        - Attendance Last Month %     (monthly_attendance)

    Target:
        - Risk_Label: Low Risk / Medium Risk / High Risk

Algorithms compared:
    - DecisionTreeClassifier
    - RandomForestClassifier

Evaluation:
    - Accuracy, Precision (weighted), Recall (weighted), F1-score (weighted)
    - Confusion matrix (saved as PNG)
    - Multi-class ROC curve + AUC (one-vs-rest, saved as PNG)
    - Feature importance (saved as PNG)

Artifacts written:
    backend/ml/saved_models/risk_model.pkl          -> best model bundle
    backend/ml/metrics/risk_model_metrics.json       -> comparison metrics
    backend/analysis/plots/risk_confusion_matrix.png
    backend/analysis/plots/risk_roc_curve.png
    backend/analysis/plots/risk_feature_importance.png

Usage:
    python train_model.py
"""

from __future__ import annotations

import json
import os
from typing import Any

import joblib
import matplotlib
matplotlib.use("Agg")  # headless rendering, no display required
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_curve,
    auc,
    classification_report,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, label_binarize
from sklearn.tree import DecisionTreeClassifier

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BACKEND_DIR, "dataset", "attendance_dataset.csv")

SAVED_MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_models")
METRICS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metrics")
PLOTS_DIR = os.path.join(BACKEND_DIR, "analysis", "plots")

os.makedirs(SAVED_MODELS_DIR, exist_ok=True)
os.makedirs(METRICS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

RISK_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "risk_model.pkl")
METRICS_PATH = os.path.join(METRICS_DIR, "risk_model_metrics.json")

FEATURE_COLUMNS = [
    "current_attendance",
    "previous_attendance",
    "leaves_taken",
    "internal_marks",
    "distance_km",
    "monthly_attendance",
]

RANDOM_STATE = 42


# --------------------------------------------------------------------------
# Data loading / feature engineering
# --------------------------------------------------------------------------

def load_and_prepare_data(csv_path: str = DATASET_PATH) -> tuple[pd.DataFrame, pd.Series]:
    """
    Load the raw dataset and engineer the feature matrix / target vector
    required for risk classification.
    """
    df = pd.read_csv(csv_path)

    feature_df = pd.DataFrame(
        {
            "current_attendance": df["Attendance_Percentage"],
            "previous_attendance": df["Previous_Attendance_Percentage"],
            "leaves_taken": df["Leaves_Taken"],
            "internal_marks": df["Internal_Marks"],
            "distance_km": df["Distance_KM"],
            "monthly_attendance": df["Monthly_Attendance"],
        }
    )
    target = df["Risk_Label"]

    return feature_df, target


# --------------------------------------------------------------------------
# Training
# --------------------------------------------------------------------------

def train_models(X_train: pd.DataFrame, y_train: np.ndarray) -> dict[str, Any]:
    """Train both candidate classifiers and return them keyed by name."""
    decision_tree = DecisionTreeClassifier(
        max_depth=8,
        min_samples_leaf=15,
        random_state=RANDOM_STATE,
    )
    decision_tree.fit(X_train, y_train)

    random_forest = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=8,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    random_forest.fit(X_train, y_train)

    return {
        "DecisionTree": decision_tree,
        "RandomForest": random_forest,
    }


# --------------------------------------------------------------------------
# Evaluation
# --------------------------------------------------------------------------

def evaluate_model(
    model: Any,
    model_name: str,
    X_test: pd.DataFrame,
    y_test: np.ndarray,
    class_names: list[str],
) -> dict[str, Any]:
    """Compute accuracy/precision/recall/F1 and a full classification report."""
    y_pred = model.predict(X_test)

    metrics = {
        "model_name": model_name,
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, average="weighted", zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, average="weighted", zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 4),
    }

    report = classification_report(
        y_test, y_pred, target_names=class_names, output_dict=True, zero_division=0
    )
    metrics["classification_report"] = report

    return metrics


def plot_confusion_matrix(model: Any, model_name: str, X_test: pd.DataFrame, y_test: np.ndarray, class_names: list[str]) -> None:
    """Render and save a confusion matrix heatmap for the given model."""
    y_pred = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred, labels=range(len(class_names)))

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=30, ha="right")
    ax.set_yticklabels(class_names)
    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("True Label")
    ax.set_title(f"Confusion Matrix — {model_name}")

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                     color="white" if cm[i, j] > cm.max() / 2 else "black")

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()

    out_path = os.path.join(PLOTS_DIR, f"risk_confusion_matrix_{model_name.lower()}.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_roc_curve(model: Any, model_name: str, X_test: pd.DataFrame, y_test: np.ndarray, class_names: list[str]) -> None:
    """
    Render and save a multi-class ROC curve (one-vs-rest) with per-class
    AUC plus a macro-average curve.
    """
    n_classes = len(class_names)
    y_test_bin = label_binarize(y_test, classes=range(n_classes))
    y_score = model.predict_proba(X_test)

    fpr, tpr, roc_auc = {}, {}, {}
    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], y_score[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])

    # Macro-average
    all_fpr = np.unique(np.concatenate([fpr[i] for i in range(n_classes)]))
    mean_tpr = np.zeros_like(all_fpr)
    for i in range(n_classes):
        mean_tpr += np.interp(all_fpr, fpr[i], tpr[i])
    mean_tpr /= n_classes
    macro_auc = auc(all_fpr, mean_tpr)

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    colors = ["#2563eb", "#f59e0b", "#dc2626"]
    for i, color in zip(range(n_classes), colors):
        ax.plot(fpr[i], tpr[i], color=color, lw=2,
                label=f"{class_names[i]} (AUC = {roc_auc[i]:.3f})")
    ax.plot(all_fpr, mean_tpr, color="black", lw=2, linestyle="--",
            label=f"Macro-average (AUC = {macro_auc:.3f})")
    ax.plot([0, 1], [0, 1], color="gray", lw=1, linestyle=":")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(f"ROC Curve (One-vs-Rest) — {model_name}")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()

    out_path = os.path.join(PLOTS_DIR, f"risk_roc_curve_{model_name.lower()}.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)

    return {"per_class_auc": {class_names[i]: round(float(roc_auc[i]), 4) for i in range(n_classes)},
            "macro_auc": round(float(macro_auc), 4)}


def plot_feature_importance(model: Any, model_name: str, feature_names: list[str]) -> None:
    """Render and save a horizontal bar chart of feature importances."""
    if not hasattr(model, "feature_importances_"):
        return

    importances = model.feature_importances_
    order = np.argsort(importances)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(np.array(feature_names)[order], importances[order], color="#2563eb")
    ax.set_xlabel("Importance")
    ax.set_title(f"Feature Importance — {model_name} (Risk Classification)")
    fig.tight_layout()

    out_path = os.path.join(PLOTS_DIR, "risk_feature_importance.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_accuracy_comparison(all_metrics: list[dict[str, Any]]) -> None:
    """Render and save a bar chart comparing accuracy across models."""
    names = [m["model_name"] for m in all_metrics]
    accuracies = [m["accuracy"] for m in all_metrics]

    fig, ax = plt.subplots(figsize=(5.5, 4))
    bars = ax.bar(names, accuracies, color=["#60a5fa", "#2563eb"])
    for bar, acc in zip(bars, accuracies):
        ax.text(bar.get_x() + bar.get_width() / 2, acc + 0.01, f"{acc:.3f}", ha="center", fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Accuracy")
    ax.set_title("Risk Classification — Model Accuracy Comparison")
    fig.tight_layout()

    out_path = os.path.join(PLOTS_DIR, "risk_accuracy_comparison.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------
# Main pipeline
# --------------------------------------------------------------------------

def main() -> None:
    print("Loading dataset...")
    X, y_raw = load_and_prepare_data()
    print(f"  Loaded {len(X):,} rows with features: {FEATURE_COLUMNS}")

    label_encoder = LabelEncoder()
    # Fix class order for readability: Low, Medium, High
    class_order = ["Low Risk", "Medium Risk", "High Risk"]
    label_encoder.classes_ = np.array(class_order)
    y = label_encoder.transform(y_raw)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    print(f"  Train: {len(X_train):,} rows | Test: {len(X_test):,} rows")

    print("\nTraining models...")
    models = train_models(X_train, y_train)

    all_metrics = []
    roc_results = {}
    for name, model in models.items():
        print(f"  Evaluating {name}...")
        metrics = evaluate_model(model, name, X_test, y_test, class_order)
        all_metrics.append(metrics)

        plot_confusion_matrix(model, name, X_test, y_test, class_order)
        roc_results[name] = plot_roc_curve(model, name, X_test, y_test, class_order)

    plot_feature_importance(models["RandomForest"], "RandomForest", FEATURE_COLUMNS)
    plot_accuracy_comparison(all_metrics)

    # Select the best model by weighted F1-score (robust to class imbalance)
    best_metrics = max(all_metrics, key=lambda m: m["f1_score"])
    best_model_name = best_metrics["model_name"]
    best_model = models[best_model_name]
    print(f"\nBest model selected: {best_model_name} "
          f"(F1={best_metrics['f1_score']}, Accuracy={best_metrics['accuracy']})")

    # Persist the winning model bundle
    bundle = {
        "model": best_model,
        "model_name": best_model_name,
        "label_encoder": label_encoder,
        "feature_columns": FEATURE_COLUMNS,
        "class_order": class_order,
    }
    joblib.dump(bundle, RISK_MODEL_PATH)
    print(f"Saved best model bundle -> {RISK_MODEL_PATH}")

    # Persist comparison metrics (used by the /analytics API + docs)
    summary = {
        "best_model": best_model_name,
        "feature_columns": FEATURE_COLUMNS,
        "class_order": class_order,
        "roc_auc": roc_results,
        "models": [
            {k: v for k, v in m.items() if k != "classification_report"}
            for m in all_metrics
        ],
        "classification_reports": {m["model_name"]: m["classification_report"] for m in all_metrics},
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved metrics -> {METRICS_PATH}")

    print("\n=== Model Comparison ===")
    for m in all_metrics:
        print(f"  {m['model_name']:15s} | Acc: {m['accuracy']:.4f} | "
              f"Prec: {m['precision']:.4f} | Rec: {m['recall']:.4f} | F1: {m['f1_score']:.4f}")


if __name__ == "__main__":
    main()
