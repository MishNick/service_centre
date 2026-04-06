from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.models import TaskStatus, PartRequestStatus


# Схемы для клиента
class ClientBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientResponse(ClientBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Схемы для задачи
class TaskBase(BaseModel):
    client_id: int
    description: str
    equipment_type: str
    equipment_model: Optional[str] = None
    serial_number: Optional[str] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    engineer_id: Optional[int] = None


class TaskResponse(TaskBase):
    id: int
    engineer_id: Optional[int] = None
    dispatcher_id: int
    status: TaskStatus
    created_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Схемы для запчастей
class PartRequestCreate(BaseModel):
    part_name: str
    part_quantity: int = 1


class PartRequestResponse(PartRequestCreate):
    id: int
    task_id: int
    engineer_id: int
    status: PartRequestStatus
    storekeeper_comment: Optional[str] = None
    created_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Схема для истории статусов
class TaskStatusUpdate(BaseModel):
    id: int
    task_id: int
    user_id: int
    old_status: Optional[str] = None
    new_status: str
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    # Старые поля (client_id стал optional)
    client_id: Optional[int] = None

    # Новые поля для ручного ввода клиента
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_address: Optional[str] = None

    # Основные поля задачи
    equipment_type: str
    equipment_model: Optional[str] = None
    serial_number: Optional[str] = None
    description: str

    # Новая дата
    scheduled_date: Optional[datetime] = None


class TaskResponse(BaseModel):
    id: int
    client_id: Optional[int] = None
    engineer_id: Optional[int] = None
    dispatcher_id: int
    status: TaskStatus
    description: str
    equipment_type: str
    equipment_model: Optional[str] = None
    serial_number: Optional[str] = None
    created_at: datetime
    closed_at: Optional[datetime] = None

    # Новые поля
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_address: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    completion_notes: Optional[str] = None

    class Config:
        from_attributes = True