from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, PartRequest
from app.utils.dependencies import get_current_user, require_role

router = APIRouter(prefix="/storekeeper", tags=["storekeeper"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def requests_page(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_role("storekeeper"))
):
    # Получаем все ожидающие заявки
    pending_requests = db.query(PartRequest).filter(
        PartRequest.status == "pending"
    ).all()

    # Получаем историю
    history = db.query(PartRequest).filter(
        PartRequest.status != "pending"
    ).order_by(PartRequest.closed_at.desc()).limit(20).all()

    return templates.TemplateResponse(
        "storekeeper/requests.html",
        {
            "request": request,
            "pending_requests": pending_requests,
            "history": history,
            "user": current_user
        }
    )