from app.database import engine
from app.models import models

# Создаем все таблицы
def init_db():
    models.Base.metadata.create_all(bind=engine)
    print("✅ База данных создана!")

if __name__ == "__main__":
    init_db()