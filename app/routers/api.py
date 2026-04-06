from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from app.models.models import User, Task, Client, PartRequest, TaskStatusUpdate, Document

from app.database import get_db
from app.models.models import User, Task, Client, PartRequest, TaskStatusUpdate
from app.schemas.tasks import (
    TaskCreate, TaskResponse, TaskUpdate,
    PartRequestCreate, PartRequestResponse,
    TaskStatusUpdate as TaskStatusUpdateSchema
)
from app.utils.dependencies import get_current_user, require_role

from fastapi.responses import FileResponse
from app.services.pdf_generator import generate_act_pdf

router = APIRouter(prefix="/api", tags=["api"])


# ===== ЗАДАЧИ =====

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список задач (в зависимости от роли)"""
    if current_user.role == "engineer":
        # Инженер видит только свои задачи
        tasks = db.query(Task).filter(Task.engineer_id == current_user.id).all()
    elif current_user.role == "dispatcher":
        # Диспетчер видит все задачи
        tasks = db.query(Task).all()
    else:
        # Остальные пока ничего не видят
        tasks = []

    return tasks


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
        task_data: TaskCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_role("dispatcher"))
):
    """Создать новую задачу (только диспетчер)"""

    # Проверяем: либо выбран существующий клиент, либо введены данные нового
    if not task_data.client_id and not task_data.client_name:
        raise HTTPException(
            status_code=400,
            detail="Укажите существующего клиента или введите имя нового"
        )

    # Создаём задачу
    task = Task(
        dispatcher_id=current_user.id,
        description=task_data.description,
        equipment_type=task_data.equipment_type,
        equipment_model=task_data.equipment_model,
        serial_number=task_data.serial_number,
        scheduled_date=task_data.scheduled_date,
        client_address=task_data.client_address,
        client_phone=task_data.client_phone
    )

    # Если выбран существующий клиент
    if task_data.client_id:
        client = db.query(Client).filter(Client.id == task_data.client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Клиент не найден")
        task.client_id = task_data.client_id
        task.client_name = client.name  # Дублируем для удобства
        task.client_phone = client.phone
        task.client_address = client.address or task_data.client_address
    else:
        # Новый клиент — сохраняем введённые данные
        task.client_name = task_data.client_name
        task.client_phone = task_data.client_phone
        task.client_address = task_data.client_address

    db.add(task)
    db.commit()
    db.refresh(task)

    # Создаём запись в истории
    status_update = TaskStatusUpdate(
        task_id=task.id,
        user_id=current_user.id,
        new_status="new",
        comment=f"Задача создана. Клиент: {task.client_name}"
    )
    db.add(status_update)
    db.commit()

    return task


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
        task_id: int,
        task_update: TaskUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Обновить задачу (статус, назначение)"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    # Проверяем права
    if current_user.role.value == "engineer" and task.engineer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Это не ваша задача")

    # Обновляем поля
    if task_update.status and task_update.status != task.status:
        # Сохраняем в историю
        status_update = TaskStatusUpdate(
            task_id=task.id,
            user_id=current_user.id,
            old_status=task.status,
            new_status=task_update.status
        )
        db.add(status_update)
        task.status = task_update.status

        if task_update.status == "completed":
            task.closed_at = datetime.utcnow()

    # Если назначается инженер (и это делает диспетчер)
    if task_update.engineer_id and current_user.role.value == "dispatcher":
        old_engineer_id = task.engineer_id
        task.engineer_id = task_update.engineer_id

        # ВАЖНО: если задача была в статусе 'new', меняем на 'assigned'
        if task.status == "new":
            status_update = TaskStatusUpdate(
                task_id=task.id,
                user_id=current_user.id,
                old_status=task.status,
                new_status="assigned",
                comment=f"Назначен инженер ID:{task_update.engineer_id}"
            )
            db.add(status_update)
            task.status = "assigned"

    db.commit()
    db.refresh(task)

    return task


# ===== ЗАПЧАСТИ =====

@router.post("/tasks/{task_id}/parts", response_model=PartRequestResponse)
async def request_part(
        task_id: int,
        part_data: PartRequestCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Инженер запрашивает запчасть"""
    # Проверяем, что задача принадлежит инженеру
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.engineer_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    part_request = PartRequest(
        task_id=task_id,
        engineer_id=current_user.id,
        part_name=part_data.part_name,
        part_quantity=part_data.part_quantity
    )

    db.add(part_request)
    db.commit()
    db.refresh(part_request)

    return part_request


@router.patch("/parts/{request_id}")
async def process_part_request(
        request_id: int,
        action: str,  # approve или reject
        comment: str = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_role("storekeeper"))
):
    """Кладовщик обрабатывает заявку на запчасть"""
    part_request = db.query(PartRequest).filter(PartRequest.id == request_id).first()
    if not part_request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    if action == "approve":
        part_request.status = "approved"
    elif action == "reject":
        part_request.status = "rejected"
    else:
        raise HTTPException(status_code=400, detail="Неверное действие")

    part_request.storekeeper_comment = comment
    part_request.closed_at = datetime.utcnow()

    db.commit()

    return {"message": f"Заявка {action}d"}


@router.get("/tasks/{task_id}/generate-act")
async def generate_act(
        task_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Сгенерировать акт выполненных работ по задаче
    """
    # Находим задачу
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    # Проверяем права: инженер (свои задачи) или диспетчер
    if current_user.role.value == "engineer" and task.engineer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    if current_user.role.value not in ["dispatcher", "engineer"]:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    # Проверяем, что задача выполнена
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Акт можно сформировать только для выполненных задач")

    # Получаем клиента (либо из связанной таблицы, либо из полей задачи)
    client = task.client  # Может быть None для новых клиентов
    engineer = task.engineer

    # Создаём объект клиента для PDF, даже если client = None
    client_for_pdf = {
        'name': task.client_name or (client.name if client else 'Не указан'),
        'phone': task.client_phone or (client.phone if client else 'Не указан'),
        'address': task.client_address or (client.address if client else 'Не указан'),
        'company_name': client.company_name if client else None
    }

    # Генерируем PDF
    pdf_path, pdf_filename = generate_act_pdf(task, client_for_pdf, engineer)

    # Возвращаем файл
    return FileResponse(
        path=pdf_path,
        filename=pdf_filename,
        media_type="application/pdf"
    )


# ===== АРХИВ ЗАДАЧ =====

@router.get("/tasks/completed/all")
async def get_completed_tasks(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Получить все завершённые задачи (для диспетчера)
    """
    if current_user.role.value != "dispatcher":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    tasks = db.query(Task).filter(
        Task.status == "completed"
    ).order_by(Task.closed_at.desc()).all()

    return tasks


@router.get("/tasks/completed/my")
async def get_my_completed_tasks(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Получить свои завершённые задачи (для инженера)
    """
    if current_user.role.value != "engineer":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    tasks = db.query(Task).filter(
        Task.status == "completed",
        Task.engineer_id == current_user.id
    ).order_by(Task.closed_at.desc()).all()

    return tasks


@router.delete("/tasks/{task_id}")
async def delete_task(
        task_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Удалить задачу из архива (только завершённые)
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    # Проверяем права
    if current_user.role.value == "engineer" and task.engineer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Это не ваша задача")

    if current_user.role.value not in ["dispatcher", "engineer"]:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    # Удаляем связанные записи (PartRequest, TaskStatusUpdate, Document)
    db.query(PartRequest).filter(PartRequest.task_id == task_id).delete()
    db.query(TaskStatusUpdate).filter(TaskStatusUpdate.task_id == task_id).delete()
    db.query(Document).filter(Document.task_id == task_id).delete()

    db.delete(task)
    db.commit()

    return {"message": "Задача удалена"}


@router.patch("/tasks/{task_id}/notes")
async def update_completion_notes(
        task_id: int,
        notes: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Добавить/обновить заметки к завершённой задаче (для инженера)
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    # Только инженер, который выполнил задачу
    if current_user.role.value != "engineer" or task.engineer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Заметки можно добавлять только к завершённым задачам")

    task.completion_notes = notes
    db.commit()

    return {"message": "Заметки сохранены", "notes": notes}