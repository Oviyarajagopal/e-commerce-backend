from fastapi import FastAPI
from database import engine
import models
from routers import task_routers

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Include routes
app.include_router(task_routers.router)