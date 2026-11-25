"""Authentication and authorization for the NeuroBloom API.

Authentication
    Login endpoints issue a signed JWT access token. Browsers receive it only as an
    httpOnly cookie, so page scripts cannot read it. Non-browser clients and tests
    may send the same token as ``Authorization: Bearer <token>``. Every request is
    resolved to a ``Principal`` loaded from the database, so deactivated accounts,
    unverified clinicians and changed passwords take effect immediately.

Cross-site request forgery
    Unsafe requests (POST, PUT, PATCH, DELETE) authenticated by the cookie must carry
    the ``X-Requested-With: NeuroBloom`` header. Other sites cannot add that header
    without passing the CORS preflight, which only allows the configured origins.

Authorization
    Route policies below bind the identifiers in a request (``user_id``,
    ``patient_id``, ``doctor_id``, ``admin_id``) to the authenticated principal.
    Endpoints that take further resource identifiers (messages, prescriptions,
    reports, sessions, requests, contexts, plans) also check that the resource
    belongs to that principal. Clinician access to a patient's data requires an
    active assignment and the patient's current consent to share data.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from sqlmodel import Session, select

from app.core.config import engine, settings
from app.models.admin import Admin
from app.models.doctor import Doctor
from app.models.patient_assignment import PatientAssignment
from app.models.user import User

ROLE_PATIENT = "patient"
ROLE_DOCTOR = "doctor"
ROLE_ADMIN = "admin"
ROLES = (ROLE_PATIENT, ROLE_DOCTOR, ROLE_ADMIN)

TOKEN_ISSUER = "neurobloom"
CSRF_HEADER = "X-Requested-With"
CSRF_HEADER_VALUE = "NeuroBloom"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

_ROLE_MODELS = {ROLE_PATIENT: User, ROLE_DOCTOR: Doctor, ROLE_ADMIN: Admin}


# ── database session ──────────────────────────────────────────────────────────

def get_db_session():
    with Session(engine) as session:
        yield session


# ── tokens ────────────────────────────────────────────────────────────────────

def password_fingerprint(password_hash: str) -> str:
    """Short digest of the stored hash; a password change invalidates older tokens."""
    return hashlib.sha256(password_hash.encode("utf-8")).hexdigest()[:16]


def create_access_token(role: str, subject_id: int, password_hash: str) -> tuple[str, datetime]:
    if role not in ROLES:
        raise ValueError(f"Unknown role: {role}")
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    claims = {
        "sub": str(subject_id),
        "role": role,
        "pwf": password_fingerprint(password_hash),
        "iss": TOKEN_ISSUER,
        "iat": issued_at,
        "exp": expires_at,
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        issuer=TOKEN_ISSUER,
        options={"require": ["sub", "role", "pwf", "iat", "exp", "iss"]},
    )


def set_auth_cookie(response: Response, token: str, expires_at: datetime) -> None:
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=expires_at,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path="/",
    )


def issue_login(response: Response, role: str, account: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """Set the session cookie and add the token fields to a login response body."""
    token, expires_at = create_access_token(role, account.id, account.password_hash)
    set_auth_cookie(response, token, expires_at)
    return {
        **payload,
        "access_token": token,
        "token_type": "bearer",
        "expires_at": expires_at.isoformat(),
    }


# ── authenticated principal ───────────────────────────────────────────────────

@dataclass(frozen=True)
class Principal:
    role: str
    id: int
    account: Any

    @property
    def is_patient(self) -> bool:
        return self.role == ROLE_PATIENT

    @property
    def is_doctor(self) -> bool:
        return self.role == ROLE_DOCTOR

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden(detail: str = "Not authorized for this resource") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _extract_token(request: Request) -> tuple[str | None, str | None]:
    authorization = request.headers.get("Authorization", "")
    scheme, _, credentials = authorization.partition(" ")
    if scheme.lower() == "bearer" and credentials.strip():
        return credentials.strip(), "header"
    cookie_token = request.cookies.get(settings.AUTH_COOKIE_NAME)
    if cookie_token:
        return cookie_token, "cookie"
    return None, None


def _account_is_usable(role: str, account: Any) -> bool:
    if not getattr(account, "is_active", True):
        return False
    if role == ROLE_DOCTOR and not account.is_verified:
        return False
    return True


def get_current_principal(request: Request, session: Session = Depends(get_db_session)) -> Principal:
    token, source = _extract_token(request)
    if not token:
        raise _unauthorized("Not authenticated")

    try:
        claims = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Session expired")
    except jwt.InvalidTokenError:
        raise _unauthorized("Invalid authentication token")

    role = claims.get("role")
    model = _ROLE_MODELS.get(role)
    try:
        subject_id = int(claims["sub"])
    except (TypeError, ValueError):
        subject_id = None
    if model is None or subject_id is None:
        raise _unauthorized("Invalid authentication token")

    account = session.get(model, subject_id)
    if account is None or not _account_is_usable(role, account):
        raise _unauthorized("Account is not available")
    if claims.get("pwf") != password_fingerprint(account.password_hash):
        raise _unauthorized("Credentials have changed; please sign in again")

    if source == "cookie" and request.method.upper() not in SAFE_METHODS:
        if request.headers.get(CSRF_HEADER) != CSRF_HEADER_VALUE:
            raise forbidden("Missing request verification header")

    principal = Principal(role=role, id=subject_id, account=account)
    request.state.principal = principal
    return principal


# ── relationship checks (also used inside endpoints) ──────────────────────────

def active_assignment(session: Session, doctor_id: int, patient_id: int) -> PatientAssignment | None:
    return session.exec(
        select(PatientAssignment)
        .where(PatientAssignment.doctor_id == doctor_id)
        .where(PatientAssignment.patient_id == patient_id)
        .where(PatientAssignment.is_active == True)  # noqa: E712
    ).first()


def doctor_may_access_patient_data(session: Session, doctor_id: int, patient_id: int) -> bool:
    """Assigned clinician and the patient currently consents to data sharing."""
    patient = session.get(User, patient_id)
    if patient is None or not patient.consent_to_share:
        return False
    return active_assignment(session, doctor_id, patient_id) is not None


def ensure_doctor_patient_data_access(session: Session, doctor_id: int, patient_id: int) -> None:
    if active_assignment(session, doctor_id, patient_id) is None:
        raise forbidden("No access to this patient")
    patient = session.get(User, patient_id)
    if patient is None or not patient.consent_to_share:
        raise forbidden("Patient has not consented to data sharing")


def consented_patient_ids(session: Session, doctor_id: int, patient_ids: Iterable[int]) -> list[int]:
    """Keep only the patients whose data this clinician may currently see."""
    allowed = []
    for patient_id in patient_ids:
        patient = session.get(User, patient_id)
        if patient is not None and patient.consent_to_share:
            allowed.append(patient_id)
    return allowed


def _ensure_patient_self(principal: Principal, patient_id: int) -> None:
    if not (principal.is_patient and principal.id == patient_id):
        raise forbidden()


def _ensure_patient_data_reader(principal: Principal, patient_id: int, session: Session) -> None:
    if principal.is_patient and principal.id == patient_id:
        return
    if principal.is_doctor:
        ensure_doctor_patient_data_access(session, principal.id, patient_id)
        return
    raise forbidden()


def _ensure_doctor_self(principal: Principal, doctor_id: int) -> None:
    if not (principal.is_doctor and principal.id == doctor_id):
        raise forbidden()


# ── route policies (used as FastAPI dependencies) ─────────────────────────────

def require_authenticated(principal: Principal = Depends(get_current_principal)) -> Principal:
    """Any signed-in account; for endpoints that hold no personal data."""
    return principal


def require_patient(principal: Principal = Depends(get_current_principal)) -> Principal:
    if not principal.is_patient:
        raise forbidden("Patient account required")
    return principal


def patient_self_by_user_id(user_id: int, principal: Principal = Depends(get_current_principal)) -> Principal:
    """Patient acting on their own record (writes, task sessions, settings)."""
    _ensure_patient_self(principal, user_id)
    return principal


def patient_self_by_patient_id(patient_id: int, principal: Principal = Depends(get_current_principal)) -> Principal:
    _ensure_patient_self(principal, patient_id)
    return principal


def patient_data_reader_by_user_id(
    user_id: int,
    principal: Principal = Depends(get_current_principal),
    session: Session = Depends(get_db_session),
) -> Principal:
    """The patient, or an assigned clinician while the patient consents (read-only use)."""
    _ensure_patient_data_reader(principal, user_id, session)
    return principal


def doctor_self(doctor_id: int, principal: Principal = Depends(get_current_principal)) -> Principal:
    _ensure_doctor_self(principal, doctor_id)
    return principal


def doctor_patient_data_access(
    doctor_id: int,
    patient_id: int,
    principal: Principal = Depends(get_current_principal),
    session: Session = Depends(get_db_session),
) -> Principal:
    """Clinician reading or acting on a patient's record: assignment and consent required."""
    _ensure_doctor_self(principal, doctor_id)
    ensure_doctor_patient_data_access(session, doctor_id, patient_id)
    return principal


def doctor_patient_contact(
    doctor_id: int,
    patient_id: int,
    principal: Principal = Depends(get_current_principal),
    session: Session = Depends(get_db_session),
) -> Principal:
    """Clinician communicating with, or unassigning, an assigned patient (no data access)."""
    _ensure_doctor_self(principal, doctor_id)
    if active_assignment(session, doctor_id, patient_id) is None:
        raise forbidden("No access to this patient")
    return principal


def admin_self(admin_id: int, principal: Principal = Depends(get_current_principal)) -> Principal:
    if not (principal.is_admin and principal.id == admin_id):
        raise forbidden("Admin access required")
    return principal


# Policies that bind a request identifier to the signed-in account.
IDENTITY_POLICIES = (
    patient_self_by_user_id,
    patient_self_by_patient_id,
    patient_data_reader_by_user_id,
    doctor_self,
    doctor_patient_data_access,
    doctor_patient_contact,
    admin_self,
)
ALL_POLICIES = IDENTITY_POLICIES + (require_authenticated, require_patient)
