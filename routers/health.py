from fastapi import APIRouter
from sqlalchemy import text
from database import engine
import redis
from config.config import settings

router = APIRouter()

@router.get("/health")
def health_check():
    db_status = "ok"
    redis_status = "ok"

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except:
        db_status = "failed"

    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=int(settings.REDIS_PORT),
            db=int(settings.REDIS_DB)
        )
        r.ping()
    except:
        redis_status = "failed"

    return {
        "app": "ok",
        "db": db_status,
        "redis": redis_status
    }