import redis

try:
    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True
    )

    redis_client.ping()
    print("✅ Redis Connected")

except Exception as e:
    print("❌ Redis not connected:", e)
    redis_client = None