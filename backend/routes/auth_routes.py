"""
routes/auth_routes.py
======================
Authentication endpoints: registration, login (JWT issuance), and a
"who am I" endpoint used by the frontend to restore session state.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth import authenticate_user, create_access_token, get_current_user, hash_password
from database import Faculty, Student, User, get_db
from models import MessageResponse, RoleEnum, Token, UserRegister

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _generate_next_code(db: Session, model, code_attr: str, prefix: str, width: int = 5) -> str:
    """
    Generate the next sequential code (e.g. STU00042 / FAC0012) for a new
    Student/Faculty row, based on the highest existing numeric suffix.
    """
    last_row = db.query(model).order_by(model.id.desc()).first()
    next_num = 1
    if last_row is not None:
        existing_code = getattr(last_row, code_attr, None)
        if existing_code and existing_code.startswith(prefix):
            try:
                next_num = int(existing_code[len(prefix):]) + 1
            except ValueError:
                next_num = db.query(model).count() + 1
        else:
            next_num = db.query(model).count() + 1
    return f"{prefix}{next_num:0{width}d}"


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)) -> Token:
    """
    Register a new student or faculty account. Automatically logs the
    user in by returning a JWT, so the frontend can go straight from the
    registration form into the dashboard.
    """
    username = payload.username.strip().lower()

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is already taken")

    if payload.email:
        existing_email = db.query(User).filter(User.email == payload.email).first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")

    student_ref_id: Optional[int] = None
    faculty_ref_id: Optional[int] = None

    if payload.role == RoleEnum.student:
        if not (payload.name and payload.department and payload.semester):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="name, department, and semester are required to register as a student",
            )
        student_code = _generate_next_code(db, Student, "student_code", "STU")
        student = Student(
            student_code=student_code,
            name=payload.name,
            department=payload.department,
            semester=payload.semester,
            gender=payload.gender,
            distance_km=payload.distance_km or 0.0,
            overall_attendance_percentage=0.0,
            trend="stable",
        )
        db.add(student)
        db.flush()
        student_ref_id = student.id

    elif payload.role == RoleEnum.faculty:
        if not (payload.name and payload.department):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="name and department are required to register as faculty",
            )
        faculty_code = _generate_next_code(db, Faculty, "faculty_code", "FAC", width=4)
        faculty = Faculty(
            faculty_code=faculty_code,
            name=payload.name,
            department=payload.department,
            designation=payload.designation or "Assistant Professor",
        )
        db.add(faculty)
        db.flush()
        faculty_ref_id = faculty.id

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin accounts cannot self-register")

    user = User(
        username=username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role.value,
        student_ref_id=student_ref_id,
        faculty_ref_id=faculty_ref_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(username=user.username, role=user.role)
    return Token(access_token=token, role=RoleEnum(user.role), username=user.username, expires_in_minutes=60)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    """
    Authenticate with username + password (OAuth2 password flow, so this
    endpoint also powers the "Authorize" button in Swagger UI) and return
    a signed JWT access token.
    """
    user = authenticate_user(db, form_data.username.strip().lower(), form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(username=user.username, role=user.role)
    return Token(access_token=token, role=RoleEnum(user.role), username=user.username, expires_in_minutes=60)


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)) -> dict:
    """Return basic identity info for the currently authenticated user."""
    profile_code = None
    profile_name = None
    if current_user.role == RoleEnum.student.value and current_user.student:
        profile_code = current_user.student.student_code
        profile_name = current_user.student.name
    elif current_user.role == RoleEnum.faculty.value and current_user.faculty:
        profile_code = current_user.faculty.faculty_code
        profile_name = current_user.faculty.name

    return {
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "profile_code": profile_code,
        "profile_name": profile_name,
    }


@router.post("/logout", response_model=MessageResponse)
def logout() -> MessageResponse:
    """
    Stateless JWT logout: there is no server-side session to invalidate,
    so this simply signals the frontend to discard its stored token.
    """
    return MessageResponse(message="Logged out successfully. Please discard the access token on the client.")
