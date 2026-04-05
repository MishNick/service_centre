from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.config import settings
from fastapi import Request, Response
from typing import Optional


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def set_token_cookie(response: Response, token: str):
    """Устанавливает токен в cookie"""
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,  # Недоступно из JavaScript (безопаснее)
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        samesite="lax"
    )


def get_token_from_cookie(request: Request) -> Optional[str]:
    """Получает токен из cookie"""
    cookie = request.cookies.get("access_token")
    if cookie and cookie.startswith("Bearer "):
        return cookie.replace("Bearer ", "")
    return None


def clear_token_cookie(response: Response):
    """Удаляет токен из cookie"""
    response.delete_cookie("access_token", path="/")