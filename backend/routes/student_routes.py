"""
routes/student_routes.py
==========================
Endpoints that power the Student Dashboard. Every route here operates on
the CURRENTLY LOGGED-IN student only (resolved via the JWT -> User ->
Student relationship) -- a student can never fetch another student's data
through these endpoints. Faculty-initiated lookups of a specific student
live in `faculty_routes.py` instead, with their own access rules.
"""

from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import require_student
from database import Attendance, MonthlyAttendance, Prediction, Student, User, get_db
from models import (
    AttendanceHistoryOut,
    AttendanceRecordOut,
    MonthlyTrendPoint,
    PredictionOut,
    StudentDashboardOut,
    StudentProfileOut,
    SubjectAttendanceOut,
)

router = APIRouter(prefix="/api/student", tags=["Student"])

MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _get_own_student(current_user: User) -> Student:
    """Resolve the Student profile linked to the current logged-in user."""
    if not current_user.student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No student profile is linked to this account.",
        )
    return current_user.student


def _get_attendance_records(db: Session, student_id: int) -> List[Attendance]:
    return (
        db.query(Attendance)
        .filter(Attendance.student_id == student_id)
        .join(Attendance.subject)
        .all()
    )


def _get_monthly_trend(db: Session, student_id: int) -> List[MonthlyTrendPoint]:
    rows = db.query(MonthlyAttendance).filter(MonthlyAttendance.student_id == student_id).all()
    if not rows:
        return []

    # Average across all enrolled subjects for each month
    totals: dict[str, list[float]] = {m: [] for m in MONTH_ORDER}
    for row in rows:
        if row.month in totals:
            totals[row.month].append(row.attendance_percentage)

    trend = []
    for month in MONTH_ORDER:
        values = totals.get(month, [])
        if values:
            trend.append(MonthlyTrendPoint(month=month, attendance_percentage=round(sum(values) / len(values), 2)))
    return trend


def _prediction_to_out(pred: Optional[Prediction]) -> Optional[PredictionOut]:
    """Convert a Prediction ORM row into the PredictionOut API schema."""
    if pred is None:
        return None
    try:
        recommendations = json.loads(pred.ai_recommendation) if pred.ai_recommendation else []
    except (json.JSONDecodeError, TypeError):
        recommendations = [pred.ai_recommendation] if pred.ai_recommendation else []

    return PredictionOut(
        student_code=None,  # filled by caller if needed
        predicted_risk_level=pred.predicted_risk_level,
        risk_model_used=pred.risk_model_used,
        risk_confidence=None,
        forecast_attendance_percentage=pred.forecast_attendance_percentage,
        forecast_model_used=pred.forecast_model_used,
        cluster_segment=pred.cluster_segment,
        ai_recommendations=recommendations,
        created_at=pred.created_at,
    )


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@router.get("/profile", response_model=StudentProfileOut)
def get_profile(current_user: User = Depends(require_student), db: Session = Depends(get_db)) -> StudentProfileOut:
    """Return the logged-in student's profile information."""
    student = _get_own_student(current_user)
    return StudentProfileOut.model_validate(student)


@router.get("/dashboard", response_model=StudentDashboardOut)
def get_dashboard(current_user: User = Depends(require_student), db: Session = Depends(get_db)) -> StudentDashboardOut:
    """
    Return everything the Student Dashboard page needs in a single call:
    profile, overall + subject-wise attendance, monthly trend, leave/marks
    summary, and the most recent prediction (if one has been generated).
    """
    student = _get_own_student(current_user)
    records = _get_attendance_records(db, student.id)

    subject_wise = [
        SubjectAttendanceOut(
            subject_name=r.subject.name,
            total_classes=r.total_classes,
            classes_attended=r.classes_attended,
            attendance_percentage=r.attendance_percentage,
            leaves_taken=r.leaves_taken,
            internal_marks=r.internal_marks,
            risk_label=r.risk_label,
        )
        for r in records
    ]

    overall_attendance = (
        round(sum(r.attendance_percentage for r in records) / len(records), 2) if records else 0.0
    )
    total_leaves = sum(r.leaves_taken for r in records)
    avg_marks = (
        round(sum(r.internal_marks for r in records if r.internal_marks is not None) / len(records), 2)
        if records else None
    )

    monthly_trend = _get_monthly_trend(db, student.id)

    latest_prediction_row = (
        db.query(Prediction)
        .filter(Prediction.student_id == student.id)
        .order_by(Prediction.created_at.desc())
        .first()
    )
    latest_prediction = _prediction_to_out(latest_prediction_row)
    if latest_prediction:
        latest_prediction.student_code = student.student_code

    return StudentDashboardOut(
        profile=StudentProfileOut.model_validate(student),
        overall_attendance_percentage=overall_attendance,
        subject_wise=subject_wise,
        monthly_trend=monthly_trend,
        total_leaves=total_leaves,
        average_internal_marks=avg_marks,
        latest_prediction=latest_prediction,
    )


@router.get("/attendance", response_model=AttendanceHistoryOut)
def get_attendance_history(
    current_user: User = Depends(require_student), db: Session = Depends(get_db)
) -> AttendanceHistoryOut:
    """Return full per-subject attendance records plus the monthly trend."""
    student = _get_own_student(current_user)
    records = _get_attendance_records(db, student.id)

    record_out = [
        AttendanceRecordOut(
            subject_name=r.subject.name,
            total_classes=r.total_classes,
            classes_attended=r.classes_attended,
            attendance_percentage=r.attendance_percentage,
            previous_attendance_percentage=r.previous_attendance_percentage,
            leaves_taken=r.leaves_taken,
            internal_marks=r.internal_marks,
            monthly_attendance=r.monthly_attendance,
            risk_label=r.risk_label,
        )
        for r in records
    ]

    monthly_trend = _get_monthly_trend(db, student.id)

    return AttendanceHistoryOut(
        student_code=student.student_code,
        records=record_out,
        monthly_trend=monthly_trend,
    )
