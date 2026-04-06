from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
from app.schemas.users import PhoneLoginRequest, PhoneVerifyRequest
from app.utils.sms import generate_sms_code, verify_sms_code
from app.utils.auth import create_access_token, set_token_cookie, clear_token_cookie
import logging

router = APIRouter(prefix="/auth", tags=["authentication"])
templates = Jinja2Templates(directory="app/templates")


# Страница входа
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # Всегда показываем страницу входа
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "title": "Вход в систему"}
    )


# Страница ввода кода
@router.get("/verify", response_class=HTMLResponse)
async def verify_page(request: Request, phone: str = None):
    if not phone:
        return RedirectResponse(url="/auth/login", status_code=302)
    return templates.TemplateResponse(
        "auth/verify.html",
        {"request": request, "phone": phone, "title": "Подтверждение"}
    )


# API: Запрос кода
@router.post("/request-code")
async def request_code(
    request: PhoneLoginRequest,
    db: Session = Depends(get_db)
):
    # Проверяем, есть ли пользователь с таким телефоном
    user = db.query(User).filter(User.phone == request.phone).first()

    if not user:
        logging.warning(f"Пользователь {request.phone} не найден, создаем тестового")

        from app.models.models import UserRole
        user = User(
            phone=request.phone,
            name="Тестовый пользователь",
            role=UserRole.ENGINEER,
            is_active=1
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Генерируем и отправляем код
    generate_sms_code(request.phone)

    return {"message": "Код отправлен", "phone": request.phone}


# API: Проверка кода
@router.post("/verify-code")
async def verify_code(
    request: PhoneVerifyRequest,
    db: Session = Depends(get_db)
):
    # Проверяем код
    if not verify_sms_code(request.phone, request.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или истекший код"
        )

    # Ищем пользователя
    user = db.query(User).filter(User.phone == request.phone).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    # Создаем токен
    access_token = create_access_token(data={"sub": str(user.id)})

    # Определяем URL редиректа в зависимости от роли
    role = user.role.value
    if role == "dispatcher":
        redirect_url = "/dispatcher/dashboard"
    elif role == "engineer":
        redirect_url = "/engineer/dashboard"
    elif role == "storekeeper":
        redirect_url = "/storekeeper/requests"
    else:
        redirect_url = "/"

    # Создаем ответ и устанавливаем cookie
    response = RedirectResponse(url=redirect_url, status_code=302)
    set_token_cookie(response, access_token)

    return response


# Выход
@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/auth/login", status_code=302)
    clear_token_cookie(response)
    return response