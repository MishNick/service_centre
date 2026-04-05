from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime

# Перечисления для статусов
class TaskStatus(str, enum.Enum):
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_PART = "waiting_for_part"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PartRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DISPATCHER = "dispatcher"
    ENGINEER = "engineer"
    STOREKEEPER = "storekeeper"

# Модель пользователя
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.ENGINEER)
    password_hash = Column(String(200), nullable=True)  # Может быть null, если только по СМС
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    tasks_as_engineer = relationship("Task", foreign_keys="Task.engineer_id", back_populates="engineer")
    tasks_as_dispatcher = relationship("Task", foreign_keys="Task.dispatcher_id", back_populates="dispatcher")
    part_requests = relationship("PartRequest", back_populates="engineer")

# Модель клиента
class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), index=True)
    email = Column(String(100))
    company_name = Column(String(200))
    inn = Column(String(20))
    address = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    tasks = relationship("Task", back_populates="client")

# Модель задачи
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    engineer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    dispatcher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.NEW)
    description = Column(Text)
    equipment_type = Column(String(100))
    equipment_model = Column(String(100))
    serial_number = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    # Связи
    client = relationship("Client", back_populates="tasks")
    engineer = relationship("User", foreign_keys=[engineer_id], back_populates="tasks_as_engineer")
    dispatcher = relationship("User", foreign_keys=[dispatcher_id], back_populates="tasks_as_dispatcher")
    status_updates = relationship("TaskStatusUpdate", back_populates="task")
    part_requests = relationship("PartRequest", back_populates="task")
    documents = relationship("Document", back_populates="task")

# История статусов задачи
class TaskStatusUpdate(Base):
    __tablename__ = "task_status_updates"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    old_status = Column(Enum(TaskStatus))
    new_status = Column(Enum(TaskStatus), nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    task = relationship("Task", back_populates="status_updates")
    user = relationship("User")

# Заявка на запчасть
class PartRequest(Base):
    __tablename__ = "part_requests"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    engineer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    part_name = Column(String(200), nullable=False)
    part_quantity = Column(Integer, default=1)
    status = Column(Enum(PartRequestStatus), default=PartRequestStatus.PENDING)
    storekeeper_comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    # Связи
    task = relationship("Task", back_populates="part_requests")
    engineer = relationship("User", back_populates="part_requests")

# Сгенерированные документы
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    document_type = Column(String(50), default="act")
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    task = relationship("Task", back_populates="documents")