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
    tasks = db.query(Task).filter(
        Task.status != "completed"
    ).order_by(Task.created_at.desc()).all()

    engineers = db.query(User).filter(User.role == "engineer").all()

    tasks_json = [
        {
            "id": task.id,
            "client_name": task.client_name,
            "client_phone": task.client_phone,
            "client_address": task.client_address,
            "equipment_type": task.equipment_type,
            "equipment_model": task.equipment_model,
            "engineer_id": task.engineer_id,
            "status": task.status.value if task.status else None,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "engineer": {
                "id": task.engineer.id,
                "name": task.engineer.name
            } if task.engineer else None,
            "client": {
                "id": task.client.id,
                "name": task.client.name,
                "phone": task.client.phone,
                "address": task.client.address
            } if task.client else None
        }
        for task in tasks
    ]

    engineers_json = [
        {
            "id": engineer.id,
            "name": engineer.name
        }
        for engineer in engineers
    ]

    return templates.TemplateResponse(
        "dispatcher/dashboard.html",
        {
            "request": request,
            "tasks": tasks,
            "engineers": engineers,
            "tasks_json": tasks_json,
            "engineers_json": engineers_json,
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


@router.get("/archive", response_class=HTMLResponse)
async def archive_page(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_role("dispatcher"))
):
    tasks = db.query(Task).filter(
        Task.status == "completed"
    ).order_by(Task.closed_at.desc()).all()

    return templates.TemplateResponse(
        "dispatcher/archive.html",
        {
            "request": request,
            "tasks": tasks,
            "user": current_user
        }
    )


@router.get("/tasks/{task_id}/view", response_class=HTMLResponse)
async def view_completed_task_page(
        request: Request,
        task_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_role("dispatcher"))
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    return templates.TemplateResponse(
        "dispatcher/task_view.html",
        {
            "request": request,
            "task": task,
            "user": current_user
        }
    )