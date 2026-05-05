import os
import redis
from config.config import settings
from dotenv import load_dotenv

load_dotenv()

redis_client = None

try:
    redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=int(settings.REDIS_PORT),
    db=int(settings.REDIS_DB),
    decode_responses=True
)
    redis_client.ping()
    print("✅ Redis Connected")
except Exception as e:
    print("❌ Redis Error:", e)

