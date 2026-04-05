from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models import models
import os

# Импортируем роуты
from app.routers import auth, engineer, dispatcher, storekeeper, api

# Создаем таблицы при запуске (для разработки)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Service Center MVP")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Подключаем шаблоны
templates = Jinja2Templates(directory="app/templates")

# Подключаем роуты
app.include_router(auth.router)
app.include_router(engineer.router)
app.include_router(dispatcher.router)
app.include_router(storekeeper.router)
app.include_router(api.router)

# Корневой маршрут
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Сервисный центр"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)