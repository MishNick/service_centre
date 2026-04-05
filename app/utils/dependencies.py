from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
from app.utils.auth import verify_token, get_token_from_cookie
import logging


async def get_current_user(
        request: Request,
        db: Session = Depends(get_db)
) -> User:
    """Проверяет токен из cookie и возвращает пользователя"""

    # Получаем токен из cookie
    token = get_token_from_cookie(request)

    if not token:
        # Если это запрос HTML страницы, редирект на логин
        if request.url.path.startswith(('/dispatcher/', '/engineer/', '/storekeeper/')):
            from fastapi.responses import RedirectResponse
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": "/auth/login"}
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


def require_role(required_role: str):
    """Декоратор для проверки роли"""

    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role.value != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden"
            )
        return current_user

    return role_checker