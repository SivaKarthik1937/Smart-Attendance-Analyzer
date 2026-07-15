"""
train_segmentation_model.py
============================
Model 3: Student Segmentation.

Clusters students into three behavioural segments using K-Means:
    - Excellent : consistently high attendance, low leaves, strong marks
    - Average   : moderate, middle-of-the-pack behaviour
    - Critical  : low attendance, high leaves, weak marks

Unlike Models 1 & 2 (which operate per subject enrollment), segmentation
is computed at the STUDENT level (one row per student), using aggregated
behaviour across all of a student's subjects, since a "segment" is a
property of the student as a whole rather than any single subject.

Features (student-level aggregates):
    - avg_attendance   : mean attendance % across all enrolled subjects
    - avg_leaves       : mean leaves taken across subjects
    - avg_internal_marks : mean internal marks across subjects
    - distance_km      : distance from college

Pipeline:
    1. Aggregate attendance_dataset.csv to student level.
    2. Standardize features (KMeans is distance-based -> scale-sensitive).
    3. Fit KMeans(n_clusters=3).
    4. Map the 3 raw cluster indices to human labels by ranking clusters
       on mean attendance (highest -> Excellent, lowest -> Critical).
    5. Evaluate with silhouette score.
    6. Visualize via PCA(2D) scatter, cluster-size pie chart, and a
       per-segment feature comparison bar chart.

Artifacts written:
    backend/ml/saved_models/segmentation_model.pkl
    backend/ml/metrics/segmentation_model_metrics.json
    backend/analysis/plots/segmentation_pca_scatter.png
    backend/analysis/plots/segmentation_distribution_pie.png
    backend/analysis/plots/segmentation_feature_comparison.png

Usage:
    python train_segmentation_model.py
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
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_DATASET_PATH = os.path.join(BACKEND_DIR, "dataset", "attendance_dataset.csv")

SAVED_MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_models")
METRICS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metrics")
PLOTS_DIR = os.path.join(BACKEND_DIR, "analysis", "plots")

os.makedirs(SAVED_MODELS_DIR, exist_ok=True)
os.makedirs(METRICS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

SEGMENTATION_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "segmentation_model.pkl")
METRICS_PATH = os.path.join(METRICS_DIR, "segmentation_model_metrics.json")

FEATURE_COLUMNS = ["avg_attendance", "avg_leaves", "avg_internal_marks", "distance_km"]
SEGMENT_LABELS_BY_RANK = ["Critical", "Average", "Excellent"]  # lowest attendance -> highest
RANDOM_STATE = 42


# --------------------------------------------------------------------------
# Data preparation
# --------------------------------------------------------------------------

def build_student_level_features(csv_path: str = MAIN_DATASET_PATH) -> pd.DataFrame:
    """Aggregate the per-subject dataset up to one row per student."""
    df = pd.read_csv(csv_path)

    agg = df.groupby("Student_ID").agg(
        name=("Name", "first"),
        department=("Department", "first"),
        semester=("Semester", "first"),
        avg_attendance=("Attendance_Percentage", "mean"),
        avg_leaves=("Leaves_Taken", "mean"),
        avg_internal_marks=("Internal_Marks", "mean"),
        distance_km=("Distance_KM", "first"),
    ).reset_index()

    return agg


# --------------------------------------------------------------------------
# Clustering
# --------------------------------------------------------------------------

def fit_kmeans(X_scaled: np.ndarray, n_clusters: int = 3) -> KMeans:
    model = KMeans(n_clusters=n_clusters, random_state=RANDOM_STATE, n_init=10)
    model.fit(X_scaled)
    return model


def map_clusters_to_labels(df: pd.DataFrame, cluster_col: str = "cluster_raw") -> dict[int, str]:
    """
    Rank raw cluster IDs by mean attendance and map them to human-readable
    segment names (highest attendance = Excellent, lowest = Critical).
    """
    ranking = df.groupby(cluster_col)["avg_attendance"].mean().sort_values()
    mapping = {cluster_id: SEGMENT_LABELS_BY_RANK[i] for i, cluster_id in enumerate(ranking.index)}
    return mapping


# --------------------------------------------------------------------------
# Visualization
# --------------------------------------------------------------------------

def plot_pca_scatter(X_scaled: np.ndarray, labels: pd.Series) -> None:
    """Reduce to 2D via PCA and scatter-plot the clusters."""
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    coords = pca.fit_transform(X_scaled)

    color_map = {"Excellent": "#16a34a", "Average": "#f59e0b", "Critical": "#dc2626"}

    fig, ax = plt.subplots(figsize=(7, 6))
    for segment, color in color_map.items():
        mask = labels == segment
        ax.scatter(coords[mask, 0], coords[mask, 1], s=8, alpha=0.4, color=color, label=segment)
    ax.set_xlabel(f"PCA Component 1 ({pca.explained_variance_ratio_[0]*100:.1f}% variance)")
    ax.set_ylabel(f"PCA Component 2 ({pca.explained_variance_ratio_[1]*100:.1f}% variance)")
    ax.set_title("Student Segmentation — K-Means Clusters (PCA Projection)")
    ax.legend()
    fig.tight_layout()

    out_path = os.path.join(PLOTS_DIR, "segmentation_pca_scatter.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_distribution_pie(labels: pd.Series) -> None:
    counts = labels.value_counts().reindex(["Excellent", "Average", "Critical"]).fillna(0)
    colors = ["#16a34a", "#f59e0b", "#dc2626"]

    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.pie(counts, labels=counts.index, autopct="%1.1f%%", colors=colors, startangle=90,
           wedgeprops={"edgecolor": "white", "linewidth": 1})
    ax.set_title("Student Segment Distribution")
    fig.tight_layout()

    out_path = os.path.join(PLOTS_DIR, "segmentation_distribution_pie.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_feature_comparison(df: pd.DataFrame) -> None:
    """Bar chart comparing mean feature values across the 3 segments."""
    summary = df.groupby("segment")[FEATURE_COLUMNS].mean().reindex(["Excellent", "Average", "Critical"])

    fig, axes = plt.subplots(1, len(FEATURE_COLUMNS), figsize=(16, 4))
    colors = {"Excellent": "#16a34a", "Average": "#f59e0b", "Critical": "#dc2626"}
    for ax, feature in zip(axes, FEATURE_COLUMNS):
        bars = ax.bar(summary.index, summary[feature], color=[colors[s] for s in summary.index])
        ax.set_title(feature.replace("_", " ").title())
        for bar, v in zip(bars, summary[feature]):
            ax.text(bar.get_x() + bar.get_width() / 2, v, f"{v:.1f}", ha="center", va="bottom", fontsize=8)

    fig.suptitle("Mean Feature Values by Segment")
    fig.tight_layout()

    out_path = os.path.join(PLOTS_DIR, "segmentation_feature_comparison.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------
# Main pipeline
# --------------------------------------------------------------------------

def main() -> None:
    print("Building student-level features...")
    df = build_student_level_features()
    print(f"  Built {len(df):,} student-level rows with features: {FEATURE_COLUMNS}")

    X = df[FEATURE_COLUMNS]  # keep as DataFrame so the scaler remembers feature names
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("\nFitting K-Means (k=3)...")
    kmeans = fit_kmeans(X_scaled, n_clusters=3)
    df["cluster_raw"] = kmeans.labels_

    sil_score = silhouette_score(X_scaled, kmeans.labels_)
    print(f"  Silhouette score: {sil_score:.4f}")

    label_mapping = map_clusters_to_labels(df)
    df["segment"] = df["cluster_raw"].map(label_mapping)
    print(f"  Cluster -> label mapping: {label_mapping}")

    plot_pca_scatter(X_scaled, df["segment"])
    plot_distribution_pie(df["segment"])
    plot_feature_comparison(df)

    bundle = {
        "model": kmeans,
        "scaler": scaler,
        "feature_columns": FEATURE_COLUMNS,
        "cluster_label_mapping": label_mapping,
    }
    joblib.dump(bundle, SEGMENTATION_MODEL_PATH)
    print(f"\nSaved model bundle -> {SEGMENTATION_MODEL_PATH}")

    segment_counts = df["segment"].value_counts().to_dict()
    summary = {
        "silhouette_score": round(float(sil_score), 4),
        "feature_columns": FEATURE_COLUMNS,
        "cluster_label_mapping": {str(k): v for k, v in label_mapping.items()},
        "segment_counts": segment_counts,
        "segment_feature_means": df.groupby("segment")[FEATURE_COLUMNS].mean().round(2).to_dict(orient="index"),
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved metrics -> {METRICS_PATH}")

    print("\n=== Segment Distribution ===")
    for segment, count in segment_counts.items():
        print(f"  {segment:12s}: {count:,} students ({count/len(df)*100:.1f}%)")


if __name__ == "__main__":
    main()
