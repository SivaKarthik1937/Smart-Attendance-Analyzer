"""
database.py
============
Database layer for the Smart Attendance Pattern Analyzer.

Responsibilities:
    - Configure the SQLAlchemy engine/session for a SQLite database.
    - Define the ORM models (tables): User, Student, Faculty, Subject,
      Attendance, Prediction.
    - Provide a FastAPI dependency (`get_db`) for request-scoped sessions.
    - Provide `init_db()` to create all tables.
    - Provide `seed_database()` to bulk-load the synthetic dataset produced
      by `dataset/generate_dataset.py` into the database, and to create
      default login accounts for every student/faculty member.

Run directly to (re)build the database from scratch:
    python database.py
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Generator, Optional

import pandas as pd
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

# --------------------------------------------------------------------------
# Engine / Session configuration
# --------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'attendance.db')}"
DATASET_DIR = os.path.join(BASE_DIR, "dataset")

# `check_same_thread=False` is required because FastAPI/Starlette may
# handle a single SQLite connection across different threads under
# Uvicorn's worker model.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()

DEFAULT_STUDENT_PASSWORD = "student123"
DEFAULT_FACULTY_PASSWORD = "faculty123"
DEFAULT_ADMIN_PASSWORD = "admin123"


# --------------------------------------------------------------------------
# ORM Models
# --------------------------------------------------------------------------

class User(Base):
    """
    Authentication table. Every login (student, faculty, or admin) has a
    row here. `role` drives role-based access control in `auth.py`.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # 'student' | 'faculty' | 'admin'

    # Optional foreign keys linking a login to a profile record
    student_ref_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    faculty_ref_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)

    is_active = Column(Integer, default=1)  # 1 = active, 0 = disabled
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="user", uselist=False)
    faculty = relationship("Faculty", back_populates="user", uselist=False)

    __table_args__ = (Index("ix_users_role", "role"),)


class Student(Base):
    """One row per student profile (student-level, not per-subject)."""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_code = Column(String(20), unique=True, nullable=False, index=True)  # e.g. STU00001
    name = Column(String(120), nullable=False)
    department = Column(String(80), nullable=False, index=True)
    semester = Column(Integer, nullable=False, index=True)
    gender = Column(String(10), nullable=True)
    distance_km = Column(Float, nullable=True)
    overall_attendance_percentage = Column(Float, nullable=True)
    trend = Column(String(20), nullable=True)  # improving | stable | declining
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="student", uselist=False)
    attendance_records = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="student", cascade="all, delete-orphan")


class Faculty(Base):
    """One row per faculty member."""
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True)
    faculty_code = Column(String(20), unique=True, nullable=False, index=True)  # e.g. FAC0001
    name = Column(String(120), nullable=False)
    department = Column(String(80), nullable=False, index=True)
    designation = Column(String(80), nullable=True)  # e.g. Assistant Professor
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="faculty", uselist=False)


class Subject(Base):
    """Subjects offered per department/semester."""
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    department = Column(String(80), nullable=False, index=True)

    attendance_records = relationship("Attendance", back_populates="subject")

    __table_args__ = (UniqueConstraint("name", "department", name="uq_subject_department"),)


class Attendance(Base):
    """
    One row per (student, subject) - mirrors `attendance_dataset.csv`.
    This is the primary table driving dashboards, analytics and ML
    feature extraction.
    """
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)

    total_classes = Column(Integer, nullable=False)
    classes_attended = Column(Integer, nullable=False)
    attendance_percentage = Column(Float, nullable=False, index=True)
    previous_attendance_percentage = Column(Float, nullable=True)
    leaves_taken = Column(Integer, default=0)
    internal_marks = Column(Integer, nullable=True)
    monthly_attendance = Column(Float, nullable=True)  # most recent month %
    risk_label = Column(String(20), nullable=True, index=True)  # ground-truth label from dataset

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="attendance_records")
    subject = relationship("Subject", back_populates="attendance_records")

    __table_args__ = (UniqueConstraint("student_id", "subject_id", name="uq_student_subject"),)


class MonthlyAttendance(Base):
    """Long-format monthly attendance trend, mirrors `monthly_attendance.csv`."""
    __tablename__ = "monthly_attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)
    month = Column(String(10), nullable=False)
    attendance_percentage = Column(Float, nullable=False)

    __table_args__ = (Index("ix_monthly_student_month", "student_id", "month"),)


class Prediction(Base):
    """
    Stores ML model outputs generated at request time via the
    `/prediction` API endpoints (risk classification, forecast, cluster
    segment, AI-generated recommendation text).
    """
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)

    predicted_risk_level = Column(String(20), nullable=True)         # Low / Medium / High Risk
    risk_model_used = Column(String(30), nullable=True)              # DecisionTree | RandomForest
    forecast_attendance_percentage = Column(Float, nullable=True)    # predicted semester-end %
    forecast_model_used = Column(String(30), nullable=True)          # LinearRegression | RandomForestRegressor
    cluster_segment = Column(String(20), nullable=True)              # Excellent | Average | Critical
    ai_recommendation = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    student = relationship("Student", back_populates="predictions")


# --------------------------------------------------------------------------
# FastAPI dependency
# --------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped SQLAlchemy session, always closed afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------------------------------
# Initialization / Seeding
# --------------------------------------------------------------------------

def init_db() -> None:
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)


def _hash_password(plain_password: str) -> str:
    """
    Hash a password using bcrypt via passlib. Imported lazily here (rather
    than at module scope) to keep `database.py` free of a hard dependency
    on `auth.py`, avoiding any risk of circular imports.
    """
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(plain_password)


def _database_is_empty(db: Session) -> bool:
    return db.query(Student).first() is None


def seed_database(dataset_dir: str = DATASET_DIR, force: bool = False) -> None:
    """
    Populate the database from the CSVs generated by
    `dataset/generate_dataset.py`. Safe to call multiple times: it is a
    no-op if data already exists, unless `force=True`.

    Steps:
        1. Load students_master.csv -> Student rows + student User logins.
        2. Derive unique subjects from attendance_dataset.csv -> Subject rows.
        3. Load attendance_dataset.csv -> Attendance rows.
        4. Load monthly_attendance.csv -> MonthlyAttendance rows.
        5. Create a handful of Faculty rows (one per department) + logins.
        6. Create a default admin/faculty login.
    """
    students_csv = os.path.join(dataset_dir, "students_master.csv")
    attendance_csv = os.path.join(dataset_dir, "attendance_dataset.csv")
    monthly_csv = os.path.join(dataset_dir, "monthly_attendance.csv")

    if not (os.path.exists(students_csv) and os.path.exists(attendance_csv)):
        raise FileNotFoundError(
            "Dataset CSVs not found. Run `python dataset/generate_dataset.py` first."
        )

    db = SessionLocal()
    try:
        if not force and not _database_is_empty(db):
            print("Database already seeded. Pass force=True to re-seed.")
            return

        if force:
            print("Force re-seed requested: clearing existing data...")
            db.query(Prediction).delete()
            db.query(MonthlyAttendance).delete()
            db.query(Attendance).delete()
            db.query(Subject).delete()
            db.query(User).delete()
            db.query(Student).delete()
            db.query(Faculty).delete()
            db.commit()

        print("Loading CSVs...")
        students_df = pd.read_csv(students_csv)
        attendance_df = pd.read_csv(attendance_csv)
        monthly_df = pd.read_csv(monthly_csv) if os.path.exists(monthly_csv) else pd.DataFrame()

        # --- 1. Students + student logins ---
        print(f"Inserting {len(students_df)} students...")
        student_password_hash = _hash_password(DEFAULT_STUDENT_PASSWORD)
        faculty_password_hash = _hash_password(DEFAULT_FACULTY_PASSWORD)
        admin_password_hash = _hash_password(DEFAULT_ADMIN_PASSWORD)
        student_code_to_id: dict[str, int] = {}
        for _, row in students_df.iterrows():
            student = Student(
                student_code=row["Student_ID"],
                name=row["Name"],
                department=row["Department"],
                semester=int(row["Semester"]),
                gender=row.get("Gender"),
                distance_km=float(row.get("Distance_KM", 0.0)),
                overall_attendance_percentage=float(row.get("Overall_Attendance_Percentage", 0.0)),
                trend=row.get("Trend"),
            )
            db.add(student)
            db.flush()  # populate student.id without committing
            student_code_to_id[student.student_code] = student.id

            user = User(
                username=student.student_code.lower(),
                email=f"{student.student_code.lower()}@college.edu",
                hashed_password=student_password_hash,
                role="student",
                student_ref_id=student.id,
            )
            db.add(user)

        db.commit()

        # --- 2. Subjects (deduplicated) ---
        print("Inserting subjects...")
        unique_subjects = attendance_df[["Subject", "Department"]].drop_duplicates()
        subject_key_to_id: dict[tuple[str, str], int] = {}
        for _, row in unique_subjects.iterrows():
            subject = Subject(name=row["Subject"], department=row["Department"])
            db.add(subject)
            db.flush()
            subject_key_to_id[(row["Subject"], row["Department"])] = subject.id
        db.commit()

        # --- 3. Attendance rows (bulk insert for performance) ---
        print(f"Inserting {len(attendance_df)} attendance records...")
        attendance_mappings = []
        for _, row in attendance_df.iterrows():
            s_id = student_code_to_id.get(row["Student_ID"])
            subj_id = subject_key_to_id.get((row["Subject"], row["Department"]))
            if s_id is None or subj_id is None:
                continue
            attendance_mappings.append(
                {
                    "student_id": s_id,
                    "subject_id": subj_id,
                    "total_classes": int(row["Total_Classes"]),
                    "classes_attended": int(row["Classes_Attended"]),
                    "attendance_percentage": float(row["Attendance_Percentage"]),
                    "previous_attendance_percentage": float(row.get("Previous_Attendance_Percentage", 0.0)),
                    "leaves_taken": int(row.get("Leaves_Taken", 0)),
                    "internal_marks": int(row.get("Internal_Marks", 0)),
                    "monthly_attendance": float(row.get("Monthly_Attendance", 0.0)),
                    "risk_label": row.get("Risk_Label"),
                }
            )
        db.bulk_insert_mappings(Attendance, attendance_mappings)
        db.commit()

        # --- 4. Monthly attendance trend rows ---
        if not monthly_df.empty:
            print(f"Inserting {len(monthly_df)} monthly attendance records...")
            # Need subject department to resolve subject_id; join via attendance_df
            subj_dept_lookup = attendance_df[["Subject", "Department"]].drop_duplicates().set_index("Subject")["Department"].to_dict()

            monthly_mappings = []
            for _, row in monthly_df.iterrows():
                s_id = student_code_to_id.get(row["Student_ID"])
                dept = subj_dept_lookup.get(row["Subject"])
                subj_id = subject_key_to_id.get((row["Subject"], dept))
                if s_id is None or subj_id is None:
                    continue
                monthly_mappings.append(
                    {
                        "student_id": s_id,
                        "subject_id": subj_id,
                        "month": row["Month"],
                        "attendance_percentage": float(row["Attendance_Percentage"]),
                    }
                )
            db.bulk_insert_mappings(MonthlyAttendance, monthly_mappings)
            db.commit()

        # --- 5. Faculty (one per department) + logins ---
        print("Inserting faculty...")
        departments = sorted(students_df["Department"].unique())
        designations = ["Assistant Professor", "Associate Professor", "Professor"]
        for idx, dept in enumerate(departments, start=1):
            faculty_code = f"FAC{idx:04d}"
            faculty = Faculty(
                faculty_code=faculty_code,
                name=f"Dr. {dept.split()[0]} Faculty",
                department=dept,
                designation=designations[idx % len(designations)],
            )
            db.add(faculty)
            db.flush()

            user = User(
                username=faculty_code.lower(),
                email=f"{faculty_code.lower()}@college.edu",
                hashed_password=faculty_password_hash,
                role="faculty",
                faculty_ref_id=faculty.id,
            )
            db.add(user)
        db.commit()

        # --- 6. Default admin account ---
        print("Creating default admin account...")
        admin_user = User(
            username="admin",
            email="admin@college.edu",
           hashed_password=admin_password_hash,
            role="admin",
        )
        db.add(admin_user)
        db.commit()

        print("Seeding complete.")
        print(f"  Students : {db.query(Student).count()}")
        print(f"  Faculty  : {db.query(Faculty).count()}")
        print(f"  Subjects : {db.query(Subject).count()}")
        print(f"  Attendance rows : {db.query(Attendance).count()}")
        print(f"  Monthly rows    : {db.query(MonthlyAttendance).count()}")
        print(f"  Users    : {db.query(User).count()}")
        print("\nDefault credentials:")
        print(f"  Student -> username: <student_id lowercase e.g. stu00001>, password: {DEFAULT_STUDENT_PASSWORD}")
        print(f"  Faculty -> username: <faculty_code lowercase e.g. fac0001>, password: {DEFAULT_FACULTY_PASSWORD}")
        print(f"  Admin   -> username: admin, password: {DEFAULT_ADMIN_PASSWORD}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(f"Initializing database at: {DATABASE_URL}")
    init_db()
    seed_database(force=True)
