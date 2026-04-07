from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from database import SessionLocal
import schemas
from services import task_service

router = APIRouter()

# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CREATE
@router.post("/tasks")
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return task_service.create_task(db, task)

# GET ALL
@router.get("/tasks")
def get_tasks(
    priority: str = None,
    x_user_name: str = Header(None),
    db: Session = Depends(get_db)
):
    tasks = task_service.get_tasks(db, priority)

    return {
        "header_user": x_user_name,
        "tasks": tasks
    }

# GET ONE
@router.get("/tasks/{id}")
def get_task(id: int, db: Session = Depends(get_db)):
    return task_service.get_task(db, id)

# UPDATE
@router.put("/tasks/{id}")
def update_task(id: int, data: schemas.TaskUpdate, db: Session = Depends(get_db)):
    result = task_service.update_task(db, id, data)

    if not result:
        return {"error": "Task not found"}

    return {"message": "Updated"}

# DELETE
@router.delete("/tasks/{id}")
def delete_task(id: int, db: Session = Depends(get_db)):
    result = task_service.delete_task(db, id)

    if not result:
        return {"error": "Task not found"}

    return {"message": "Deleted (soft)"}