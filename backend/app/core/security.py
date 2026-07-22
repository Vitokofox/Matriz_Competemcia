from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import Permiso, Usuario

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: int) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Usuario:
    settings = get_settings()
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        user_id = int(payload.get("sub", ""))
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise credentials_error from exc
    user = db.get(Usuario, user_id)
    if user is None or not user.activo:
        raise credentials_error
    return user


def permissions_for(user: Usuario) -> set[str]:
    return {
        permission.codigo
        for role in user.roles
        if role.activo
        for permission in role.permisos
        if permission.activo
    }


def require_permission(permission_code: str):
    def dependency(user: Usuario = Depends(get_current_user)) -> Usuario:
        if permission_code not in permissions_for(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso requerido: {permission_code}",
            )
        return user

    return dependency


def require_any_permission(*permission_codes: str):
    def dependency(user: Usuario = Depends(get_current_user)) -> Usuario:
        if not permissions_for(user).intersection(permission_codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos suficientes",
            )
        return user

    return dependency


def get_permission(db: Session, code: str) -> Permiso | None:
    return db.query(Permiso).filter_by(codigo=code, activo=True).first()
