import uuid
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Path, status
from pydantic import BaseModel, Field

# Инициализация приложения FastAPI с описанием для Swagger UI
app = FastAPI(
    title="Task Manager API",
    description="REST API для управления личными задачами и отслеживания их приоритетов в режиме реального времени.",
    version="1.0.0",
)

# Временное хранилище задач в оперативной памяти (In-Memory DB)
tasks_db: Dict[uuid.UUID, dict] = {}


# --- МОДЕЛИ ДАННЫХ (PYDANTIC) ---

class TaskCreate(BaseModel):
    """Модель данных для создания новой задачи."""
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Краткое название задачи. Должно быть информативным.",
        examples=["Купить продукты"],
    )
    description: Optional[str] = Field(
        None,
        description="Подробное описание задачи, шаги к выполнению или дополнительные заметки.",
        examples=["Молоко 3.2%, хлеб бородинский, куриное филе"],
    )
    priority: int = Field(
        ...,
        ge=1,
        le=5,
        description="Уровень важности задачи от 1 (самый низкий) до 5 (самый высокий).",
        examples=[3],
    )


class TaskResponse(BaseModel):
    """Модель ответа, содержащая полные данные о задаче, включая её ID."""
    id: uuid.UUID = Field(
        ...,
        description="Уникальный идентификатор задачи в формате UUID (v4).",
        examples=["4f1b7a2d-8c3b-491a-b62d-112233445566"],
    )
    title: str = Field(..., description="Название задачи.")
    description: Optional[str] = Field(None, description="Детальное описание задачи.")
    priority: int = Field(..., description="Установленный приоритет задачи (1-5).")


class ErrorResponse(BaseModel):
    """Модель стандартного ответа об ошибке 404."""
    detail: str = Field(..., description="Текстовое сообщение с подробным описанием ошибки.")


# --- ЭНДПОИНТЫ API ---

@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую задачу",
    description="Принимает параметры задачи (название, описание, приоритет), выполняет валидацию полей, генерирует уникальный UUID и сохраняет задачу в оперативную память.",
)
async def create_task(task: TaskCreate):
    task_id = uuid.uuid4()
    new_task = {"id": task_id, **task.model_dump()}
    tasks_db[task_id] = new_task
    return new_task


@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Задача с указанным идентификатором не найдена в системе.",
        }
    },
    summary="Получить задачу по ID",
    description="Ищет задачу во временном хранилище по её уникальному UUID. Возвращает полные данные задачи, если она найдена, или ошибку 404, если объект отсутствует.",
)
async def get_task(
    task_id: uuid.UUID = Path(
        ..., description="Уникальный UUID задачи, которую необходимо найти."
    )
):
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача с ID {task_id} не найдена",
        )
    return tasks_db[task_id]
