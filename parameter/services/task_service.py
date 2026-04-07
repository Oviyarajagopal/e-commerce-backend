from sqlalchemy.orm import Session
import models

def create_task(db: Session, task_data):
    new_task = models.Task(**task_data.dict())
    db.add(new_task)
    db.commit()
    return {"message": "Task created"}


def get_tasks(db: Session, priority: str = None):
    query = db.query(models.Task).filter(models.Task.is_deleted == False)

    if priority:
        query = query.filter(models.Task.priority == priority)

    return query.all()


def get_task(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def update_task(db: Session, task_id: int, data):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not task:
        return None

    for key, value in data.dict(exclude_unset=True).items():
        setattr(task, key, value)

    db.commit()
    return task


def delete_task(db: Session, task_id: int):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not task:
        return None

    task.is_deleted = True
    db.commit()
    return task