from fastapi import FastAPI, Depends, Header
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime
from pydantic import BaseModel

# ------------------ DATABASE ------------------

DATABASE_URL = "mysql+pymysql://root:Viya2105#@localhost/task_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ------------------ MODEL ------------------

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String(255))
    status = Column(String(50), default="pending")
    priority = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

# Create table
Base.metadata.create_all(bind=engine)

# ------------------ SCHEMA ------------------

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    priority: str


class TaskUpdate(BaseModel):
    description: str | None = None
    priority: str | None = None
    status: str | None = None

# ------------------ APP ------------------

app = FastAPI()

# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------ CREATE TASK ------------------

@app.post("/tasks")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_task = Task(**task.dict())
    db.add(new_task)
    db.commit()
    return {"message": "Task created"}

# ------------------ GET TASKS (QUERY + HEADER) ------------------

@app.get("/tasks")
def get_tasks(
    priority: str = None,
    x_user_name: str = Header(None),
    db: Session = Depends(get_db)
):
    query = db.query(Task).filter(Task.is_deleted == False)

    if priority:
        query = query.filter(Task.priority == priority)

    tasks = query.all()

    return {
        "header_user": x_user_name,
        "tasks": tasks
    }

# ------------------ GET SINGLE TASK ------------------

@app.get("/tasks/{id}")
def get_task(id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == id).first()
    return task

# ------------------ UPDATE TASK ------------------

@app.put("/tasks/{id}")
def update_task(id: int, data: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == id).first()

    if not task:
        return {"error": "Task not found"}

    for key, value in data.dict(exclude_unset=True).items():
        setattr(task, key, value)

    task.updated_at = datetime.utcnow()

    db.commit()
    return {"message": "Task updated"}

# ------------------ DELETE TASK (SOFT DELETE) ------------------

@app.delete("/tasks/{id}")
def delete_task(id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == id).first()

    if not task:
        return {"error": "Task not found"}

    task.is_deleted = True
    db.commit()

    return {"message": "Task deleted (soft delete)"}