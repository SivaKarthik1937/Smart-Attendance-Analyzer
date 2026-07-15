"""
routes/faculty_routes.py
==========================
Endpoints that power the Faculty Dashboard: institution-wide aggregates,
department/subject comparisons, defaulter lists, improving/declining
students, risk distribution, and the ability to drill into any individual
student's full record (faculty are not restricted to "their own" data the
way students are).
"""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import require_faculty
from database import Attendance, Student, Subject, User, get_db
from models import (
    DepartmentStatOut,
    FacultyDashboardOut,
    RiskDistributionOut,
    StudentDashboardOut,
    StudentProfileOut,
    StudentSummaryOut,
    SubjectAttendanceOut,
    SubjectStatOut,
)
from routes.student_routes import _get_attendance_records, _get_monthly_trend, _prediction_to_out
from database import Prediction

router = APIRouter(prefix="/api/faculty", tags=["Faculty"])

RISK_SEVERITY = {"Low Risk": 0, "Medium Risk": 1, "High Risk": 2}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _compute_worst_case_risk(db: Session, student_ids: Optional[List[int]] = None) -> Dict[int, str]:
    """
    Compute each student's "headline" risk level as the most severe risk
    label across any of their enrolled subjects (a student at High Risk
    in even one subject is flagged High Risk overall -- the conservative,
    actionable choice for a faculty-facing warning system).
    """
    query = db.query(Attendance.student_id, Attendance.risk_label)
    if student_ids is not None:
        query = query.filter(Attendance.student_id.in_(student_ids))

    worst: Dict[int, str] = {}
    for student_id, risk_label in query.all():
        if not risk_label:
            continue
        current = worst.get(student_id)
        if current is None or RISK_SEVERITY.get(risk_label, 0) > RISK_SEVERITY.get(current, 0):
            worst[student_id] = risk_label
    return worst


def _to_summary(student: Student, risk_map: Dict[int, str]) -> StudentSummaryOut:
    return StudentSummaryOut(
        student_code=student.student_code,
        name=student.name,
        department=student.department,
        semester=student.semester,
        overall_attendance_percentage=student.overall_attendance_percentage,
        trend=student.trend,
        risk_level=risk_map.get(student.id),
    )


def _department_stats(db: Session) -> List[DepartmentStatOut]:
    rows = (
        db.query(Student.department, func.avg(Student.overall_attendance_percentage), func.count(Student.id))
        .group_by(Student.department)
        .all()
    )
    stats = []
    for dept, avg_attendance, count in rows:
        below_75 = (
            db.query(func.count(Student.id))
            .filter(Student.department == dept, Student.overall_attendance_percentage < 75)
            .scalar()
        )
        stats.append(
            DepartmentStatOut(
                department=dept,
                average_attendance=round(float(avg_attendance or 0), 2),
                total_students=count,
                below_75_count=below_75 or 0,
            )
        )
    return sorted(stats, key=lambda s: s.average_attendance)


def _subject_stats(db: Session, department: Optional[str] = None) -> List[SubjectStatOut]:
    query = (
        db.query(Subject.name, func.avg(Attendance.attendance_percentage), func.count(Attendance.id))
        .join(Attendance, Attendance.subject_id == Subject.id)
    )
    if department:
        query = query.join(Student, Attendance.student_id == Student.id).filter(Student.department == department)
    rows = query.group_by(Subject.name).all()

    return sorted(
        [
            SubjectStatOut(subject_name=name, average_attendance=round(float(avg or 0), 2), total_enrolled=count)
            for name, avg, count in rows
        ],
        key=lambda s: s.average_attendance,
    )


def _base_student_query(db: Session, department: Optional[str] = None, semester: Optional[int] = None):
    query = db.query(Student)
    if department:
        query = query.filter(Student.department == department)
    if semester:
        query = query.filter(Student.semester == semester)
    return query


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@router.get("/dashboard", response_model=FacultyDashboardOut)
def get_faculty_dashboard(
    department: Optional[str] = Query(None, description="Filter to a single department; omit for institution-wide view"),
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> FacultyDashboardOut:
    """
    Aggregate payload powering the entire Faculty Dashboard page: totals,
    below-75% count, department/subject comparisons, top defaulters,
    improving/declining students, and overall risk distribution.
    """
    base_query = _base_student_query(db, department=department)

    total_students = base_query.count()
    if total_students == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No students found for this filter")

    students_below_75 = base_query.filter(Student.overall_attendance_percentage < 75).count()

    attendance_stats = base_query.with_entities(
        func.max(Student.overall_attendance_percentage),
        func.min(Student.overall_attendance_percentage),
        func.avg(Student.overall_attendance_percentage),
    ).first()
    highest, lowest, average = attendance_stats

    department_stats = _department_stats(db) if not department else [
        s for s in _department_stats(db) if s.department == department
    ]
    subject_stats = _subject_stats(db, department=department)

    # Top 10 defaulters (lowest attendance, excluding students with no attendance data yet)
    defaulter_rows = (
        base_query.filter(Student.overall_attendance_percentage > 0)
        .order_by(Student.overall_attendance_percentage.asc())
        .limit(10)
        .all()
    )

    improving_rows = (
        base_query.filter(Student.trend == "improving")
        .order_by(Student.overall_attendance_percentage.desc())
        .limit(10)
        .all()
    )
    declining_rows = (
        base_query.filter(Student.trend == "declining")
        .order_by(Student.overall_attendance_percentage.asc())
        .limit(10)
        .all()
    )

    relevant_ids = [s.id for s in defaulter_rows + improving_rows + declining_rows]
    risk_map = _compute_worst_case_risk(db, student_ids=relevant_ids)

    # Risk distribution across ALL students matching the filter
    all_ids = [s.id for s in base_query.all()]
    full_risk_map = _compute_worst_case_risk(db, student_ids=all_ids)
    risk_counts = {"Low Risk": 0, "Medium Risk": 0, "High Risk": 0}
    for risk in full_risk_map.values():
        if risk in risk_counts:
            risk_counts[risk] += 1

    return FacultyDashboardOut(
        total_students=total_students,
        students_below_75=students_below_75,
        highest_attendance=round(float(highest or 0), 2),
        lowest_attendance=round(float(lowest or 0), 2),
        average_attendance=round(float(average or 0), 2),
        department_stats=department_stats,
        subject_stats=subject_stats,
        top_defaulters=[_to_summary(s, risk_map) for s in defaulter_rows],
        students_improving=[_to_summary(s, risk_map) for s in improving_rows],
        students_declining=[_to_summary(s, risk_map) for s in declining_rows],
        risk_distribution=RiskDistributionOut(
            low_risk=risk_counts["Low Risk"],
            medium_risk=risk_counts["Medium Risk"],
            high_risk=risk_counts["High Risk"],
        ),
    )


@router.get("/students", response_model=List[StudentSummaryOut])
def list_students(
    department: Optional[str] = None,
    semester: Optional[int] = None,
    search: Optional[str] = Query(None, description="Search by name or student code"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> List[StudentSummaryOut]:
    """Paginated, filterable, searchable list of all students."""
    query = _base_student_query(db, department=department, semester=semester)
    if search:
        like_pattern = f"%{search.strip()}%"
        query = query.filter((Student.name.ilike(like_pattern)) | (Student.student_code.ilike(like_pattern)))

    rows = query.order_by(Student.student_code).offset(skip).limit(limit).all()
    risk_map = _compute_worst_case_risk(db, student_ids=[s.id for s in rows])

    return [_to_summary(s, risk_map) for s in rows]


@router.get("/students/{student_code}", response_model=StudentDashboardOut)
def get_student_detail(
    student_code: str,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> StudentDashboardOut:
    """Full drill-down view of a single student, for faculty inspection."""
    student = db.query(Student).filter(Student.student_code == student_code.upper()).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student '{student_code}' not found")

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


@router.get("/below-75", response_model=List[StudentSummaryOut])
def get_students_below_75(
    department: Optional[str] = None,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> List[StudentSummaryOut]:
    """All students currently below the 75% attendance requirement."""
    rows = (
        _base_student_query(db, department=department)
        .filter(Student.overall_attendance_percentage < 75)
        .order_by(Student.overall_attendance_percentage.asc())
        .all()
    )
    risk_map = _compute_worst_case_risk(db, student_ids=[s.id for s in rows])
    return [_to_summary(s, risk_map) for s in rows]


@router.get("/top-defaulters", response_model=List[StudentSummaryOut])
def get_top_defaulters(
    limit: int = Query(10, ge=1, le=50),
    department: Optional[str] = None,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> List[StudentSummaryOut]:
    """The N students with the lowest attendance percentage."""
    rows = (
        _base_student_query(db, department=department)
        .filter(Student.overall_attendance_percentage > 0)
        .order_by(Student.overall_attendance_percentage.asc())
        .limit(limit)
        .all()
    )
    risk_map = _compute_worst_case_risk(db, student_ids=[s.id for s in rows])
    return [_to_summary(s, risk_map) for s in rows]
