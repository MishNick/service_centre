from app.database import SessionLocal
from app.models.models import User, Client, Task, UserRole
from datetime import datetime, timedelta
import random


def seed_database():
    db = SessionLocal()

    # Создаем тестовых пользователей
    users = [
        User(phone="+79991111111", name="Иван Петров (Диспетчер)", role=UserRole.DISPATCHER),
        User(phone="+79992222222", name="Петр Иванов (Инженер)", role=UserRole.ENGINEER),
        User(phone="+79993333333", name="Сергей Сидоров (Инженер)", role=UserRole.ENGINEER),
        User(phone="+79994444444", name="Анна Смирнова (Кладовщик)", role=UserRole.STOREKEEPER),
    ]

    for user in users:
        existing = db.query(User).filter(User.phone == user.phone).first()
        if not existing:
            db.add(user)

    db.commit()

    # Создаем тестовых клиентов
    clients = [
        Client(name="ООО Ромашка", phone="+74951234567", address="ул. Ленина, 1"),
        Client(name="ИП Иванов", phone="+74957654321", address="ул. Пушкина, 10"),
        Client(name="ЗАО Технологии", phone="+74951112233", address="пр. Мира, 15"),
    ]

    for client in clients:
        existing = db.query(Client).filter(Client.name == client.name).first()
        if not existing:
            db.add(client)

    db.commit()

    # Получаем созданные записи
    dispatcher = db.query(User).filter(User.role == UserRole.DISPATCHER).first()
    engineer = db.query(User).filter(User.role == UserRole.ENGINEER).first()

    if dispatcher and engineer and clients:
        # Создаем тестовые задачи
        statuses = ["new", "assigned", "in_progress", "waiting_for_part"]

        for i in range(5):
            task = Task(
                client_id=clients[i % len(clients)].id,
                dispatcher_id=dispatcher.id,
                engineer_id=engineer.id if random.choice([True, False]) else None,
                status=random.choice(statuses),
                description=f"Не работает {random.choice(['принтер', 'сканер', 'МФУ', 'ноутбук'])}",
                equipment_type=random.choice(["Принтер", "МФУ", "Ноутбук", "ПК"]),
                equipment_model=f"Model-{random.randint(100, 999)}",
                serial_number=f"SN{random.randint(10000, 99999)}",
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 5))
            )
            db.add(task)

        db.commit()

    print("✅ Тестовые данные добавлены")
    db.close()


if __name__ == "__main__":
    seed_database()