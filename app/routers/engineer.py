from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.models import User, Task, PartRequest
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/engineer", tags=["engineer"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def tasks_page(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    tasks = db.query(Task).filter(
        Task.engineer_id == current_user.id,
        Task.status != "completed"
    ).order_by(Task.created_at.desc()).all()

    return templates.TemplateResponse(
        "engineer/dashboard.html",
        {
            "request": request,
            "tasks": tasks,
            "user": current_user
        }
    )


@router.get("/my-completed", response_class=HTMLResponse)
async def my_completed_page(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    tasks = db.query(Task).filter(
        Task.status == "completed",
        Task.engineer_id == current_user.id
    ).order_by(Task.closed_at.desc()).all()

    return templates.TemplateResponse(
        "engineer/my_completed.html",
        {
            "request": request,
            "tasks": tasks,
            "user": current_user
        }
    )


@router.get("/tasks/{task_id}", response_class=HTMLResponse)
async def task_detail_page(
        request: Request,
        task_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.engineer_id == current_user.id
    ).first()

    if not task:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404
        )

    part_requests = db.query(PartRequest).filter(PartRequest.task_id == task_id).all()

    return templates.TemplateResponse(
        "engineer/task_detail.html",
        {
            "request": request,
            "task": task,
            "part_requests": part_requests,
            "user": current_user
        }
    )