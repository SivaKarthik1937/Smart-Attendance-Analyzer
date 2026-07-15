"""
eda.py
======
Exploratory Data Analysis for the Smart Attendance Pattern Analyzer.

Generates and saves every distribution/comparison/correlation chart
required by the spec (separate from the model-evaluation charts, which
live in train_model.py / train_forecast_model.py / train_segmentation_model.py):

    - Correlation matrix (heatmap)
    - Attendance distribution (histogram)
    - Department comparison (bar chart)
    - Semester comparison (bar chart)
    - Subject comparison (bar chart)
    - Monthly trend (overall line chart)
    - Risk distribution (pie chart)
    - Attendance vs Internal Marks (scatter)
    - Gender-wise attendance (bar chart)
    - Attendance heatmap (Department x Semester)

All figures are saved as PNGs to backend/analysis/plots/, and a JSON
summary of key statistics is written to backend/analysis/eda_summary.json
for consumption by the /analytics API route.

Usage:
    python eda.py
"""

from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

ANALYSIS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(ANALYSIS_DIR)
DATASET_DIR = os.path.join(BACKEND_DIR, "dataset")
PLOTS_DIR = os.path.join(ANALYSIS_DIR, "plots")
SUMMARY_PATH = os.path.join(ANALYSIS_DIR, "eda_summary.json")

os.makedirs(PLOTS_DIR, exist_ok=True)

MAIN_CSV = os.path.join(DATASET_DIR, "attendance_dataset.csv")
MONTHLY_CSV = os.path.join(DATASET_DIR, "monthly_attendance.csv")

MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
RISK_COLORS = {"Low Risk": "#16a34a", "Medium Risk": "#f59e0b", "High Risk": "#dc2626"}


# --------------------------------------------------------------------------
# Individual chart functions
# --------------------------------------------------------------------------

def plot_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Correlation heatmap across the numeric behavioural features."""
    numeric_cols = [
        "Attendance_Percentage", "Previous_Attendance_Percentage", "Leaves_Taken",
        "Internal_Marks", "Distance_KM", "Monthly_Attendance",
    ]
    corr = df[numeric_cols].corr().round(3)

    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(numeric_cols)))
    ax.set_yticks(range(len(numeric_cols)))
    labels = [c.replace("_", " ") for c in numeric_cols]
    ax.set_xticklabels(labels, rotation=40, ha="right")
    ax.set_yticklabels(labels)
    for i in range(len(numeric_cols)):
        for j in range(len(numeric_cols)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center",
                     color="white" if abs(corr.iloc[i, j]) > 0.5 else "black", fontsize=8)
    ax.set_title("Correlation Matrix — Attendance Features")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "eda_correlation_matrix.png"), dpi=150)
    plt.close(fig)

    return corr


def plot_attendance_distribution(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(df["Attendance_Percentage"], bins=30, color="#2563eb", edgecolor="white")
    ax.axvline(75, color="red", linestyle="--", lw=1.5, label="75% threshold")
    ax.set_xlabel("Attendance %")
    ax.set_ylabel("Number of Records")
    ax.set_title("Attendance Distribution")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "eda_attendance_distribution.png"), dpi=150)
    plt.close(fig)


def plot_department_comparison(df: pd.DataFrame) -> pd.Series:
    dept_avg = df.groupby("Department")["Attendance_Percentage"].mean().sort_values()

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.barh(dept_avg.index, dept_avg.values, color="#2563eb")
    for bar, v in zip(bars, dept_avg.values):
        ax.text(v + 0.3, bar.get_y() + bar.get_height() / 2, f"{v:.1f}%", va="center", fontsize=8)
    ax.axvline(75, color="red", linestyle="--", lw=1)
    ax.set_xlabel("Average Attendance %")
    ax.set_title("Department-wise Attendance Comparison")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "eda_department_comparison.png"), dpi=150)
    plt.close(fig)

    return dept_avg


def plot_semester_comparison(df: pd.DataFrame) -> pd.Series:
    sem_avg = df.groupby("Semester")["Attendance_Percentage"].mean().sort_index()

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    bars = ax.bar(sem_avg.index.astype(str), sem_avg.values, color="#7c3aed")
    for bar, v in zip(bars, sem_avg.values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.3, f"{v:.1f}%", ha="center", fontsize=8)
    ax.axhline(75, color="red", linestyle="--", lw=1)
    ax.set_xlabel("Semester")
    ax.set_ylabel("Average Attendance %")
    ax.set_title("Semester-wise Attendance Comparison")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "eda_semester_comparison.png"), dpi=150)
    plt.close(fig)

    return sem_avg


def plot_subject_comparison(df: pd.DataFrame) -> pd.Series:
    subj_avg = df.groupby("Subject")["Attendance_Percentage"].mean().sort_values()

    fig, ax = plt.subplots(figsize=(8, 8))
    bars = ax.barh(subj_avg.index, subj_avg.values, color="#0891b2")
    for bar, v in zip(bars, subj_avg.values):
        ax.text(v + 0.3, bar.get_y() + bar.get_height() / 2, f"{v:.1f}%", va="center", fontsize=7)
    ax.axvline(75, color="red", linestyle="--", lw=1)
    ax.set_xlabel("Average Attendance %")
    ax.set_title("Subject-wise Attendance Comparison")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "eda_subject_comparison.png"), dpi=150)
    plt.close(fig)

    return subj_avg


def plot_monthly_trend(monthly_df: pd.DataFrame) -> pd.Series:
    monthly_avg = monthly_df.groupby("Month")["Attendance_Percentage"].mean().reindex(MONTH_ORDER)

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.plot(monthly_avg.index, monthly_avg.values, marker="o", color="#2563eb", lw=2)
    for x, y in zip(monthly_avg.index, monthly_avg.values):
        ax.text(x, y + 0.3, f"{y:.1f}%", ha="center", fontsize=8)
    ax.axhline(75, color="red", linestyle="--", lw=1, label="75% threshold")
    ax.set_xlabel("Month")
    ax.set_ylabel("Average Attendance %")
    ax.set_title("Overall Monthly Attendance Trend")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "eda_monthly_trend.png"), dpi=150)
    plt.close(fig)

    return monthly_avg


def plot_risk_distribution_pie(df: pd.DataFrame) -> pd.Series:
    counts = df["Risk_Label"].value_counts().reindex(["Low Risk", "Medium Risk", "High Risk"]).fillna(0)

    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.pie(counts, labels=counts.index, autopct="%1.1f%%",
           colors=[RISK_COLORS[k] for k in counts.index], startangle=90,
           wedgeprops={"edgecolor": "white", "linewidth": 1})
    ax.set_title("Overall Risk Distribution")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "eda_risk_distribution.png"), dpi=150)
    plt.close(fig)

    return counts


def plot_attendance_vs_marks_scatter(df: pd.DataFrame) -> None:
    sample = df.sample(n=min(3000, len(df)), random_state=42)  # sample for a readable scatter

    fig, ax = plt.subplots(figsize=(7, 5.5))
    colors = sample["Risk_Label"].map(RISK_COLORS)
    ax.scatter(sample["Attendance_Percentage"], sample["Internal_Marks"], c=colors, alpha=0.4, s=12)
    handles = [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=8, label=k)
               for k, c in RISK_COLORS.items()]
    ax.legend(handles=handles, title="Risk Level")
    ax.set_xlabel("Attendance %")
    ax.set_ylabel("Internal Marks")
    ax.set_title("Attendance vs Internal Marks")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "eda_attendance_vs_marks.png"), dpi=150)
    plt.close(fig)


def plot_gender_comparison(df: pd.DataFrame) -> pd.Series:
    gender_avg = df.groupby("Gender")["Attendance_Percentage"].mean()

    fig, ax = plt.subplots(figsize=(5, 4.5))
    bars = ax.bar(gender_avg.index, gender_avg.values, color=["#2563eb", "#db2777"])
    for bar, v in zip(bars, gender_avg.values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.3, f"{v:.1f}%", ha="center", fontsize=9)
    ax.set_ylabel("Average Attendance %")
    ax.set_title("Gender-wise Attendance Comparison")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "eda_gender_comparison.png"), dpi=150)
    plt.close(fig)

    return gender_avg


def plot_department_semester_heatmap(df: pd.DataFrame) -> None:
    """Heatmap of average attendance across Department x Semester."""
    pivot = df.pivot_table(index="Department", columns="Semester", values="Attendance_Percentage", aggfunc="mean")

    fig, ax = plt.subplots(figsize=(9, 5.5))
    im = ax.imshow(pivot.values, cmap="RdYlGn", vmin=50, vmax=95, aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("Semester")
    ax.set_title("Attendance Heatmap — Department × Semester")
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax, fraction=0.035, pad=0.04, label="Avg Attendance %")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, "eda_department_semester_heatmap.png"), dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------
# Main pipeline
# --------------------------------------------------------------------------

def main() -> None:
    print("Loading data for EDA...")
    df = pd.read_csv(MAIN_CSV)
    monthly_df = pd.read_csv(MONTHLY_CSV)
    print(f"  Main dataset: {len(df):,} rows | Monthly dataset: {len(monthly_df):,} rows")

    print("Generating charts...")
    corr = plot_correlation_matrix(df)
    plot_attendance_distribution(df)
    dept_avg = plot_department_comparison(df)
    sem_avg = plot_semester_comparison(df)
    subj_avg = plot_subject_comparison(df)
    monthly_avg = plot_monthly_trend(monthly_df)
    risk_counts = plot_risk_distribution_pie(df)
    plot_attendance_vs_marks_scatter(df)
    gender_avg = plot_gender_comparison(df)
    plot_department_semester_heatmap(df)
    print(f"  Saved all charts to {PLOTS_DIR}")

    summary = {
        "total_records": len(df),
        "total_students": int(df["Student_ID"].nunique()),
        "overall_avg_attendance": round(float(df["Attendance_Percentage"].mean()), 2),
        "students_below_75_pct_records": int((df["Attendance_Percentage"] < 75).sum()),
        "correlation_matrix": corr.to_dict(),
        "department_avg_attendance": dept_avg.round(2).to_dict(),
        "semester_avg_attendance": {str(k): round(v, 2) for k, v in sem_avg.to_dict().items()},
        "subject_avg_attendance": subj_avg.round(2).to_dict(),
        "monthly_avg_attendance": monthly_avg.round(2).to_dict(),
        "risk_distribution": risk_counts.astype(int).to_dict(),
        "gender_avg_attendance": gender_avg.round(2).to_dict(),
    }
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved EDA summary -> {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
