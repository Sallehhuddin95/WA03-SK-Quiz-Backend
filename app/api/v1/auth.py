from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import SESSION_COOKIE_NAME
from app.models.user import User
from app.repositories.session import SessionRepository
from app.repositories.user import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    MeResponse,
)
from app.schemas.common import Envelope
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

DbSession = Annotated[Session, Depends(get_db)]


def get_auth_service() -> AuthService:
    return AuthService(SessionRepository(), UserRepository())


@router.post("/login", response_model=Envelope[LoginResponse])
def login(
    payload: LoginRequest,
    response: Response,
    db: DbSession,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    user, token = service.login(db, payload.username, payload.kata_laluan)
    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.session_max_days * 24 * 3600,
        path="/",
        domain=settings.cookie_domain,
    )
    return Envelope(data=service.to_session_user(db, user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        service.logout(db, token)
    settings = get_settings()
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(
        SESSION_COOKIE_NAME, path="/", domain=settings.cookie_domain
    )
    return response


@router.get("/me", response_model=Envelope[MeResponse])
def me(
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return Envelope(data=service.to_session_user(db, user))


@router.post("/change-password", response_model=Envelope[dict])
def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    token = request.cookies.get(SESSION_COOKIE_NAME) or ""
    service.change_password(
        db, user, token, payload.kata_laluan_semasa, payload.kata_laluan_baru
    )
    return Envelope(data={"mesej": "Kata laluan berjaya ditukar."})