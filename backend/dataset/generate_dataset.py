"""
generate_dataset.py
====================
Synthetic Dataset Generator for the Smart Attendance Pattern Analyzer.

This script produces a realistic, internally-consistent attendance dataset
for 5000+ students, spanning multiple departments, semesters and subjects.

Design goals for realism:
    - Each student has a hidden "diligence factor" that drives correlated
      behaviour across attendance, leaves, internal marks and monthly trend.
    - Attendance percentages follow a right-skewed distribution (most
      students attend reasonably well, a smaller tail attends poorly),
      achieved with a Beta distribution rather than a uniform/normal one.
    - Previous-semester attendance correlates with current attendance but
      includes independent drift (students improve or decline over time).
    - Distance from college has a mild negative correlation with attendance.
    - Internal marks correlate positively with attendance.
    - Monthly attendance is generated as a 6-month time series per student
      with a randomly assigned trend (improving / stable / declining) so
      that trend-based features and charts are meaningful.
    - Risk labels are derived from a weighted rule-based formula (not pure
      randomness) so that the ML models trained later actually have
      learnable signal.

Outputs (written to backend/dataset/):
    1. attendance_dataset.csv   -> main flat dataset (one row per student
                                    per subject) matching the required
                                    column specification.
    2. monthly_attendance.csv   -> long-format monthly trend data per
                                    student (used for trend charts / EDA).
    3. students_master.csv      -> one row per student, student-level
                                    profile data (used for dashboards).
    4. DATA_DICTIONARY.md       -> human-readable description of columns.

Usage:
    python generate_dataset.py --num-students 5000 --seed 42
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field
from datetime import date
from typing import List

import numpy as np
import pandas as pd

try:
    from faker import Faker
    _FAKER_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback for environments without faker installed
    _FAKER_AVAILABLE = False

    _FIRST_NAMES_M = ["Aarav", "Vihaan", "Rohan", "Arjun", "Kabir", "Ishaan", "Aditya", "Sai",
                       "Karthik", "Nikhil", "Rahul", "Varun", "Aryan", "Dev", "Yash", "Manav"]
    _FIRST_NAMES_F = ["Ananya", "Diya", "Priya", "Kavya", "Isha", "Meera", "Riya", "Sneha",
                       "Tanya", "Anika", "Neha", "Pooja", "Shreya", "Divya", "Radhika", "Nisha"]
    _LAST_NAMES = ["Sharma", "Verma", "Iyer", "Nair", "Gupta", "Reddy", "Menon", "Rao",
                   "Kumar", "Singh", "Patel", "Joshi", "Kapoor", "Chatterjee", "Pillai", "Desai"]

    class Faker:
        """Minimal drop-in fallback for the `faker` package, used only if
        the real library is not installed. Produces plausible Indian names
        deterministically, seeded via Faker.seed()."""

        _rng_state = np.random.default_rng(0)

        @staticmethod
        def seed(seed_value: int) -> None:
            Faker._rng_state = np.random.default_rng(seed_value)

        def name_male(self) -> str:
            first = Faker._rng_state.choice(_FIRST_NAMES_M)
            last = Faker._rng_state.choice(_LAST_NAMES)
            return f"{first} {last}"

        def name_female(self) -> str:
            first = Faker._rng_state.choice(_FIRST_NAMES_F)
            last = Faker._rng_state.choice(_LAST_NAMES)
            return f"{first} {last}"

# --------------------------------------------------------------------------
# Static reference data
# --------------------------------------------------------------------------

DEPARTMENTS: dict[str, List[str]] = {
    "Computer Science": ["Data Structures", "Operating Systems", "DBMS", "Computer Networks", "AI & ML"],
    "Electronics": ["Digital Electronics", "Signals & Systems", "Microprocessors", "VLSI Design", "Communication Systems"],
    "Mechanical": ["Thermodynamics", "Fluid Mechanics", "Machine Design", "Manufacturing Tech", "Heat Transfer"],
    "Civil": ["Structural Analysis", "Geotechnical Engg", "Surveying", "Concrete Technology", "Transportation Engg"],
    "Electrical": ["Electrical Machines", "Power Systems", "Control Systems", "Power Electronics", "Circuit Theory"],
    "Information Technology": ["Web Technologies", "Cloud Computing", "Cyber Security", "Software Engineering", "Data Mining"],
}

SEMESTERS = list(range(1, 9))            # Semester 1 to 8
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]   # 6-month rolling window
GENDERS = ["Male", "Female"]

RISK_LABELS = ["Low Risk", "Medium Risk", "High Risk"]


# --------------------------------------------------------------------------
# Data classes
# --------------------------------------------------------------------------

@dataclass
class StudentProfile:
    """Holds the hidden/generative parameters for a single student."""
    student_id: str
    name: str
    gender: str
    department: str
    semester: int
    diligence: float           # 0-1 hidden factor driving attendance behaviour
    trend: str                 # 'improving' | 'stable' | 'declining'
    distance_km: float
    subjects: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# Generation helpers
# --------------------------------------------------------------------------

def _make_student_id(index: int) -> str:
    """Generate a formatted student ID, e.g. STU00001."""
    return f"STU{index:05d}"


def _sample_diligence(rng: np.random.Generator) -> float:
    """
    Sample a 'diligence' factor in [0, 1] using a Beta distribution skewed
    toward higher values (most students are reasonably diligent, a smaller
    fraction is consistently poor), which is what drives realistic
    right-skewed attendance distributions.
    """
    return float(rng.beta(a=6, b=1.8))


def _sample_trend(rng: np.random.Generator) -> str:
    """Randomly assign a behavioural trend with realistic proportions."""
    return rng.choice(
        ["improving", "stable", "declining"],
        p=[0.25, 0.50, 0.25],
    )


def _generate_students(num_students: int, rng: np.random.Generator, faker: Faker) -> List[StudentProfile]:
    """Create the base population of student profiles."""
    students: List[StudentProfile] = []
    departments = list(DEPARTMENTS.keys())

    for i in range(1, num_students + 1):
        department = rng.choice(departments)
        semester = int(rng.choice(SEMESTERS))
        gender = rng.choice(GENDERS, p=[0.55, 0.45])
        name = faker.name_male() if gender == "Male" else faker.name_female()
        diligence = _sample_diligence(rng)
        trend = _sample_trend(rng)
        # Distance mildly anti-correlated with diligence (farther students
        # tend, on average, to skip slightly more -- but with a lot of noise)
        base_distance = rng.gamma(shape=2.0, scale=6.0)   # right-skewed, km
        distance_km = float(np.clip(base_distance, 0.5, 45.0))

        # Pick 4-6 subjects offered for that department/semester
        subject_pool = DEPARTMENTS[department]
        n_subjects = int(rng.integers(4, len(subject_pool) + 1))
        subjects = list(rng.choice(subject_pool, size=n_subjects, replace=False))

        students.append(
            StudentProfile(
                student_id=_make_student_id(i),
                name=name,
                gender=gender,
                department=department,
                semester=semester,
                diligence=diligence,
                trend=trend,
                distance_km=round(distance_km, 1),
                subjects=subjects,
            )
        )
    return students


def _attendance_for_subject(student: StudentProfile, rng: np.random.Generator) -> tuple[int, int, float]:
    """
    Simulate total classes held, classes attended, and attendance % for a
    single subject, driven by the student's diligence with added noise and
    a mild distance penalty.
    """
    total_classes = int(rng.integers(45, 65))

    distance_penalty = min(student.distance_km / 350.0, 0.06)  # up to -6%
    noise = rng.normal(0, 0.05)
    attendance_rate = student.diligence - distance_penalty + noise
    attendance_rate = float(np.clip(attendance_rate, 0.40, 1.0))

    classes_attended = int(round(total_classes * attendance_rate))
    classes_attended = min(classes_attended, total_classes)
    attendance_pct = round((classes_attended / total_classes) * 100, 2)

    return total_classes, classes_attended, attendance_pct


def _previous_attendance(current_pct: float, student: StudentProfile, rng: np.random.Generator) -> float:
    """
    Derive previous-semester attendance % from current, adjusted by the
    inverse of the student's trend (if they are 'improving' now, their
    previous attendance was likely lower, and vice versa) plus noise.
    """
    trend_shift = {
        "improving": rng.uniform(4, 12),     # previous was lower
        "declining": -rng.uniform(4, 12),    # previous was higher
        "stable": rng.uniform(-3, 3),
    }[student.trend]

    previous = current_pct - trend_shift + rng.normal(0, 3)
    return float(np.clip(round(previous, 2), 30, 100))


def _leaves_taken(attendance_pct: float, rng: np.random.Generator) -> int:
    """Leaves are inversely related to attendance %, with noise."""
    base = int(round((100 - attendance_pct) / 4))
    leaves = max(0, base + int(rng.integers(-2, 3)))
    return min(leaves, 30)


def _internal_marks(attendance_pct: float, rng: np.random.Generator) -> int:
    """Internal marks (out of 100) correlate positively with attendance."""
    base = 40 + (attendance_pct - 50) * 0.7
    marks = base + rng.normal(0, 7)
    return int(np.clip(round(marks), 0, 100))


def _monthly_attendance_series(student: StudentProfile, final_pct: float, rng: np.random.Generator) -> List[float]:
    """
    Build a 6-month attendance percentage series ending near `final_pct`,
    shaped by the student's trend, for use in trend charts and as the
    'Monthly Attendance' feature (last month's value).
    """
    trend_slope = {
        "improving": rng.uniform(1.5, 4.0),
        "declining": -rng.uniform(1.5, 4.0),
        "stable": rng.uniform(-0.5, 0.5),
    }[student.trend]

    series = []
    # Work backwards from the final month so the series ends at final_pct
    value = final_pct
    for _ in reversed(range(len(MONTHS))):
        series.append(round(np.clip(value, 30, 100), 2))
        value -= trend_slope + rng.normal(0, 1.5)
    series.reverse()
    return series


def _derive_risk_label(
    attendance_pct: float,
    previous_pct: float,
    leaves: int,
    internal_marks: int,
    trend: str,
) -> str:
    """
    Rule-based (weighted score) risk classification. This is intentionally
    a deterministic-ish formula (with the noise already baked into the
    inputs) so downstream ML models trained on this data have real,
    learnable signal rather than pure noise.

    Score components (higher score => higher risk):
        - Low current attendance is the dominant factor.
        - A declining trend adds risk; an improving trend reduces it.
        - High leave count adds risk.
        - Low internal marks adds a small amount of risk.
    """
    score = 0.0

    # Attendance is the dominant signal
    if attendance_pct < 65:
        score += 3
    elif attendance_pct < 75:
        score += 1.5
    else:
        score += 0

    # Trend adjustment
    if trend == "declining":
        score += 1.0
    elif trend == "improving":
        score -= 0.5

    # Drop vs previous semester
    if previous_pct - attendance_pct > 8:
        score += 0.75

    # Leaves
    if leaves >= 12:
        score += 0.75
    elif leaves >= 7:
        score += 0.35

    # Internal marks (poor academic performance compounds risk)
    if internal_marks < 40:
        score += 0.5

    if score >= 3.0:
        return "High Risk"
    elif score >= 1.25:
        return "Medium Risk"
    else:
        return "Low Risk"


# --------------------------------------------------------------------------
# Main generation pipeline
# --------------------------------------------------------------------------

def generate_dataset(num_students: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Generate the full synthetic dataset.

    Returns:
        main_df:    one row per (student, subject) -- matches required schema
        monthly_df: long-format monthly attendance trend per student
        master_df:  one row per student -- student-level profile
    """
    rng = np.random.default_rng(seed)
    faker = Faker()
    Faker.seed(seed)

    students = _generate_students(num_students, rng, faker)

    main_rows = []
    monthly_rows = []
    master_rows = []

    for student in students:
        # Aggregate values computed once per student, then varied slightly per subject
        subject_records = []
        for subject in student.subjects:
            total_classes, classes_attended, attendance_pct = _attendance_for_subject(student, rng)
            previous_pct = _previous_attendance(attendance_pct, student, rng)
            leaves = _leaves_taken(attendance_pct, rng)
            marks = _internal_marks(attendance_pct, rng)
            monthly_series = _monthly_attendance_series(student, attendance_pct, rng)
            risk_label = _derive_risk_label(attendance_pct, previous_pct, leaves, marks, student.trend)

            main_rows.append(
                {
                    "Student_ID": student.student_id,
                    "Name": student.name,
                    "Department": student.department,
                    "Semester": student.semester,
                    "Gender": student.gender,
                    "Subject": subject,
                    "Total_Classes": total_classes,
                    "Classes_Attended": classes_attended,
                    "Attendance_Percentage": attendance_pct,
                    "Previous_Attendance_Percentage": previous_pct,
                    "Leaves_Taken": leaves,
                    "Internal_Marks": marks,
                    "Distance_KM": student.distance_km,
                    "Monthly_Attendance": monthly_series[-1],
                    "Trend": student.trend,
                    "Risk_Label": risk_label,
                }
            )

            for month_name, month_pct in zip(MONTHS, monthly_series):
                monthly_rows.append(
                    {
                        "Student_ID": student.student_id,
                        "Subject": subject,
                        "Month": month_name,
                        "Attendance_Percentage": month_pct,
                    }
                )

            subject_records.append(attendance_pct)

        # Student-level master record: average across their subjects
        master_rows.append(
            {
                "Student_ID": student.student_id,
                "Name": student.name,
                "Department": student.department,
                "Semester": student.semester,
                "Gender": student.gender,
                "Distance_KM": student.distance_km,
                "Overall_Attendance_Percentage": round(float(np.mean(subject_records)), 2),
                "Trend": student.trend,
                "Num_Subjects": len(student.subjects),
            }
        )

    main_df = pd.DataFrame(main_rows)
    monthly_df = pd.DataFrame(monthly_rows)
    master_df = pd.DataFrame(master_rows)

    return main_df, monthly_df, master_df


def _write_data_dictionary(path: str) -> None:
    """Write a Markdown data dictionary describing every column produced."""
    content = """# Data Dictionary — Smart Attendance Pattern Analyzer

## attendance_dataset.csv (main dataset, one row per student per subject)

| Column | Type | Description |
|---|---|---|
| Student_ID | string | Unique student identifier, e.g. STU00001 |
| Name | string | Student full name (synthetic) |
| Department | string | Department / branch of study |
| Semester | int | Current semester (1-8) |
| Gender | string | Male / Female |
| Subject | string | Subject name this row's attendance relates to |
| Total_Classes | int | Total classes held for the subject this term |
| Classes_Attended | int | Classes the student attended |
| Attendance_Percentage | float | Classes_Attended / Total_Classes * 100 |
| Previous_Attendance_Percentage | float | Attendance % in the previous semester |
| Leaves_Taken | int | Number of leaves taken during the term |
| Internal_Marks | int | Internal assessment marks (0-100) |
| Distance_KM | float | Student's distance from college in kilometers |
| Monthly_Attendance | float | Most recent month's attendance % (see monthly_attendance.csv for full series) |
| Trend | string | Hidden behavioural trend used to generate the data: improving / stable / declining |
| Risk_Label | string | Target label: Low Risk / Medium Risk / High Risk |

## monthly_attendance.csv (long format)

| Column | Type | Description |
|---|---|---|
| Student_ID | string | Unique student identifier |
| Subject | string | Subject name |
| Month | string | Month abbreviation (Jan-Jun, 6-month rolling window) |
| Attendance_Percentage | float | Attendance % for that student/subject/month |

## students_master.csv (one row per student)

| Column | Type | Description |
|---|---|---|
| Student_ID | string | Unique student identifier |
| Name | string | Student full name |
| Department | string | Department / branch |
| Semester | int | Current semester |
| Gender | string | Male / Female |
| Distance_KM | float | Distance from college |
| Overall_Attendance_Percentage | float | Average attendance % across all enrolled subjects |
| Trend | string | improving / stable / declining |
| Num_Subjects | int | Number of subjects the student is enrolled in |

## Generation Notes

- Data is fully synthetic, generated with NumPy + Faker using seeded RNG for reproducibility.
- Attendance is modeled with a per-student "diligence" factor (Beta distribution) so the
  overall distribution is realistically right-skewed rather than uniform.
- Risk_Label is derived via a weighted rule-based scoring formula (not random), so the
  dataset contains genuine, learnable signal for the ML models trained in `ml/train_model.py`.
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic attendance dataset.")
    parser.add_argument("--num-students", type=int, default=5000, help="Number of students to generate.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--out-dir", type=str, default=os.path.dirname(os.path.abspath(__file__)),
                         help="Output directory for generated CSV files.")
    args = parser.parse_args()

    print(f"Generating synthetic dataset for {args.num_students} students (seed={args.seed})...")
    main_df, monthly_df, master_df = generate_dataset(args.num_students, args.seed)

    os.makedirs(args.out_dir, exist_ok=True)

    main_path = os.path.join(args.out_dir, "attendance_dataset.csv")
    monthly_path = os.path.join(args.out_dir, "monthly_attendance.csv")
    master_path = os.path.join(args.out_dir, "students_master.csv")
    dict_path = os.path.join(args.out_dir, "DATA_DICTIONARY.md")

    main_df.to_csv(main_path, index=False)
    monthly_df.to_csv(monthly_path, index=False)
    master_df.to_csv(master_path, index=False)
    _write_data_dictionary(dict_path)

    print(f"  -> {main_path}  ({len(main_df):,} rows)")
    print(f"  -> {monthly_path}  ({len(monthly_df):,} rows)")
    print(f"  -> {master_path}  ({len(master_df):,} rows)")
    print(f"  -> {dict_path}")
    print("\nRisk label distribution:")
    print(main_df["Risk_Label"].value_counts(normalize=True).round(3) * 100)
    print("\nDone.")


if __name__ == "__main__":
    main()
