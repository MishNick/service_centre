from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.models import User, Task, Client
from app.utils.dependencies import get_current_user, require_role

router = APIRouter(prefix="/dispatcher", tags=["dispatcher"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_role("dispatcher"))
):
    # Получаем все активные задачи
    tasks = db.query(Task).filter(
        Task.status != "completed"
    ).order_by(Task.created_at.desc()).all()

    # Получаем список инженеров для назначения
    engineers = db.query(User).filter(User.role == "engineer").all()

    return templates.TemplateResponse(
        "dispatcher/dashboard.html",
        {
            "request": request,
            "tasks": tasks,
            "engineers": engineers,
            "user": current_user
        }
    )


@router.get("/tasks/create", response_class=HTMLResponse)
async def create_task_page(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_role("dispatcher"))
):
    clients = db.query(Client).all()

    return templates.TemplateResponse(
        "dispatcher/create_task.html",
        {
            "request": request,
            "clients": clients,
            "user": current_user
        }
    )

