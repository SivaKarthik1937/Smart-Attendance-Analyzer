"""
models.py
=========
Pydantic schemas (request/response DTOs) used across the FastAPI routes.

Naming convention:
    - `*Create` / `*Register` -> incoming payloads for creation
    - `*Login`                -> incoming login payloads
    - `*Out` / `*Response`    -> outgoing payloads returned to the client
    - `*Base`                 -> shared fields reused by multiple schemas

These are intentionally kept separate from the SQLAlchemy ORM models in
`database.py` so that the API's public contract can evolve independently
of the internal storage schema.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# --------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------

class RoleEnum(str, Enum):
    student = "student"
    faculty = "faculty"
    admin = "admin"


class RiskLevelEnum(str, Enum):
    low = "Low Risk"
    medium = "Medium Risk"
    high = "High Risk"


class TrendEnum(str, Enum):
    improving = "improving"
    stable = "stable"
    declining = "declining"


class SegmentEnum(str, Enum):
    excellent = "Excellent"
    average = "Average"
    critical = "Critical"


class ExportFormatEnum(str, Enum):
    pdf = "pdf"
    csv = "csv"


# --------------------------------------------------------------------------
# Auth Schemas
# --------------------------------------------------------------------------

class UserRegister(BaseModel):
    """Payload for creating a new user account (student or faculty)."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique login username")
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=6, max_length=128)
    role: RoleEnum

    # Fields required only when role == student
    name: Optional[str] = Field(None, description="Required for student/faculty registration")
    department: Optional[str] = None
    semester: Optional[int] = Field(None, ge=1, le=8, description="Required for students")
    gender: Optional[str] = None
    distance_km: Optional[float] = Field(None, ge=0)

    # Fields required only when role == faculty
    designation: Optional[str] = None


class UserLogin(BaseModel):
    """Payload for authenticating an existing user."""
    username: str
    password: str


class Token(BaseModel):
    """JWT bearer token response."""
    access_token: str
    token_type: str = "bearer"
    role: RoleEnum
    username: str
    expires_in_minutes: int


class TokenPayload(BaseModel):
    """Decoded JWT payload structure."""
    sub: str                # username
    role: RoleEnum
    exp: Optional[int] = None


# --------------------------------------------------------------------------
# Student Schemas
# --------------------------------------------------------------------------

class StudentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_code: str
    name: str
    department: str
    semester: int
    gender: Optional[str] = None
    distance_km: Optional[float] = None


class StudentProfileOut(StudentBase):
    """Full student profile, as returned on the student dashboard."""
    id: int
    overall_attendance_percentage: Optional[float] = None
    trend: Optional[str] = None
    created_at: datetime


class SubjectAttendanceOut(BaseModel):
    """Subject-wise attendance breakdown for a student."""
    model_config = ConfigDict(from_attributes=True)

    subject_name: str
    total_classes: int
    classes_attended: int
    attendance_percentage: float
    leaves_taken: int
    internal_marks: Optional[int] = None
    risk_label: Optional[str] = None


class MonthlyTrendPoint(BaseModel):
    """A single point on a monthly attendance trend line."""
    month: str
    attendance_percentage: float


class StudentDashboardOut(BaseModel):
    """Aggregate payload powering the entire student dashboard page."""
    profile: StudentProfileOut
    overall_attendance_percentage: float
    subject_wise: List[SubjectAttendanceOut]
    monthly_trend: List[MonthlyTrendPoint]
    total_leaves: int
    average_internal_marks: Optional[float] = None
    latest_prediction: Optional["PredictionOut"] = None


# --------------------------------------------------------------------------
# Faculty Schemas
# --------------------------------------------------------------------------

class FacultyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    faculty_code: str
    name: str
    department: str
    designation: Optional[str] = None


class FacultyProfileOut(FacultyBase):
    id: int
    created_at: datetime


class StudentSummaryOut(BaseModel):
    """Compact student row used in faculty tables (defaulter lists, etc.)."""
    model_config = ConfigDict(from_attributes=True)

    student_code: str
    name: str
    department: str
    semester: int
    overall_attendance_percentage: Optional[float] = None
    trend: Optional[str] = None
    risk_level: Optional[str] = None


class DepartmentStatOut(BaseModel):
    department: str
    average_attendance: float
    total_students: int
    below_75_count: int


class SubjectStatOut(BaseModel):
    subject_name: str
    average_attendance: float
    total_enrolled: int


class RiskDistributionOut(BaseModel):
    low_risk: int
    medium_risk: int
    high_risk: int


class FacultyDashboardOut(BaseModel):
    """Aggregate payload powering the entire faculty dashboard page."""
    total_students: int
    students_below_75: int
    highest_attendance: float
    lowest_attendance: float
    average_attendance: float
    department_stats: List[DepartmentStatOut]
    subject_stats: List[SubjectStatOut]
    top_defaulters: List[StudentSummaryOut]
    students_improving: List[StudentSummaryOut]
    students_declining: List[StudentSummaryOut]
    risk_distribution: RiskDistributionOut


# --------------------------------------------------------------------------
# Attendance Schemas
# --------------------------------------------------------------------------

class AttendanceRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    subject_name: str
    total_classes: int
    classes_attended: int
    attendance_percentage: float
    previous_attendance_percentage: Optional[float] = None
    leaves_taken: int
    internal_marks: Optional[int] = None
    monthly_attendance: Optional[float] = None
    risk_label: Optional[str] = None


class AttendanceHistoryOut(BaseModel):
    student_code: str
    records: List[AttendanceRecordOut]
    monthly_trend: List[MonthlyTrendPoint]


# --------------------------------------------------------------------------
# Prediction Schemas
# --------------------------------------------------------------------------

class PredictionRequest(BaseModel):
    """
    Manual feature input for on-demand prediction (e.g. faculty testing
    a hypothetical scenario, or the frontend prediction page). If
    `student_code` is provided instead, the backend will pull live
    features from the database rather than requiring manual entry.
    """
    student_code: Optional[str] = None

    current_attendance: Optional[float] = Field(None, ge=0, le=100)
    previous_attendance: Optional[float] = Field(None, ge=0, le=100)
    leaves_taken: Optional[int] = Field(None, ge=0)
    internal_marks: Optional[int] = Field(None, ge=0, le=100)
    distance_km: Optional[float] = Field(None, ge=0)
    monthly_attendance: Optional[float] = Field(None, ge=0, le=100)


class ModelComparisonEntry(BaseModel):
    model_name: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None
    r2_score: Optional[float] = None


class PredictionOut(BaseModel):
    """Full prediction response: risk, forecast, segment, and AI advice."""
    student_code: Optional[str] = None

    predicted_risk_level: RiskLevelEnum
    risk_model_used: str
    risk_confidence: Optional[float] = Field(None, description="Probability of the predicted class")

    forecast_attendance_percentage: float
    forecast_model_used: str

    cluster_segment: SegmentEnum

    ai_recommendations: List[str]

    created_at: Optional[datetime] = None


class PredictionHistoryOut(BaseModel):
    student_code: str
    history: List[PredictionOut]


# --------------------------------------------------------------------------
# Analytics Schemas
# --------------------------------------------------------------------------

class CorrelationPair(BaseModel):
    feature_a: str
    feature_b: str
    correlation: float


class FeatureImportanceEntry(BaseModel):
    feature: str
    importance: float


class AnalyticsOverviewOut(BaseModel):
    """Powers the Analytics page: distributions, comparisons, model insight."""
    attendance_distribution: List[float]
    department_comparison: List[DepartmentStatOut]
    semester_comparison: dict[str, float]
    subject_comparison: List[SubjectStatOut]
    monthly_trend_overall: List[MonthlyTrendPoint]
    correlation_matrix: List[CorrelationPair]
    feature_importance: List[FeatureImportanceEntry]
    risk_model_comparison: List[ModelComparisonEntry]
    forecast_model_comparison: List[ModelComparisonEntry]


# --------------------------------------------------------------------------
# Generic / Utility Schemas
# --------------------------------------------------------------------------

class MessageResponse(BaseModel):
    """Generic success/informational message wrapper."""
    message: str


class ErrorResponse(BaseModel):
    detail: str


class ExportRequest(BaseModel):
    student_code: Optional[str] = Field(None, description="Omit for a faculty-wide export")
    format: ExportFormatEnum = ExportFormatEnum.pdf


# Resolve forward reference (StudentDashboardOut.latest_prediction -> PredictionOut)
StudentDashboardOut.model_rebuild()
