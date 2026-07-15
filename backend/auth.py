"""
auth.py
=======
Authentication & authorization layer for the Smart Attendance Pattern
Analyzer API.

Responsibilities:
    - Password hashing / verification (bcrypt via passlib).
    - JWT access token creation and decoding (python-jose).
    - `authenticate_user()` to validate login credentials against the DB.
    - FastAPI dependencies for extracting and validating the current user,
      and for enforcing role-based access control (student / faculty / admin).

Environment variables (see .env.example):
    JWT_SECRET_KEY          - secret used to sign tokens (required in prod)
    JWT_ALGORITHM            - signing algorithm (default: HS256)
    ACCESS_TOKEN_EXPIRE_MINUTES - token lifetime in minutes (default: 60)
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import User, get_db
from models import RoleEnum, TokenPayload

load_dotenv()

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-insecure-secret-change-me-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

if SECRET_KEY.startswith("dev-only"):
    # Not a hard failure (keeps local dev friction-free), but surfaced loudly
    # so it is never accidentally shipped to production.
    print("[auth.py] WARNING: Using default insecure JWT_SECRET_KEY. "
          "Set JWT_SECRET_KEY in your .env file before deploying.")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# tokenUrl must match the actual login route mounted in app.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=True)


# --------------------------------------------------------------------------
# Password hashing
# --------------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# --------------------------------------------------------------------------
# JWT token creation / decoding
# --------------------------------------------------------------------------

def create_access_token(username: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT containing the username (`sub`) and role claims.

    Args:
        username: the user's login username, stored as the `sub` claim.
        role: the user's role ('student' | 'faculty' | 'admin').
        expires_delta: optional custom expiry; defaults to
            ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT, returning its typed payload.

    Raises:
        HTTPException(401): if the token is missing, malformed, expired,
            or signed with the wrong key.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        role: Optional[str] = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
        return TokenPayload(sub=username, role=RoleEnum(role), exp=payload.get("exp"))
    except JWTError:
        raise credentials_exception
    except ValueError:
        # role string didn't match RoleEnum
        raise credentials_exception


# --------------------------------------------------------------------------
# User authentication
# --------------------------------------------------------------------------

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Validate login credentials.

    Returns:
        The matching `User` ORM object if credentials are valid and the
        account is active, otherwise None.
    """
    user = db.query(User).filter(User.username == username.lower()).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


# --------------------------------------------------------------------------
# FastAPI dependencies
# --------------------------------------------------------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Resolve the currently authenticated user from the bearer token.
    Use this as a dependency on any route that requires authentication,
    regardless of role.
    """
    payload = decode_access_token(token)
    user = db.query(User).filter(User.username == payload.sub).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for this token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been disabled",
        )
    return user


def require_roles(*allowed_roles: Sequence[str]):
    """
    Dependency factory enforcing role-based access control.

    Usage:
        @router.get("/faculty/dashboard")
        def faculty_dashboard(user: User = Depends(require_roles("faculty", "admin"))):
            ...

    Raises:
        HTTPException(403): if the current user's role is not in
            `allowed_roles`.
    """
    normalized_roles = {r.value if isinstance(r, RoleEnum) else str(r) for r in allowed_roles}

    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of the following roles: {sorted(normalized_roles)}",
            )
        return current_user

    return _dependency


# Convenience, pre-built role dependencies for common cases
require_student = require_roles(RoleEnum.student)
require_faculty = require_roles(RoleEnum.faculty, RoleEnum.admin)
require_admin = require_roles(RoleEnum.admin)
require_any_authenticated = get_current_user
