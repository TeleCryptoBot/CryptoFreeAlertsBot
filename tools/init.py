import os
from redis import Redis

# Initialize environment variables
TELEGRAM_API_KEY = os.environ.get("TELEGRAM_API_KEY")

PERCENTAGE_CHANGE = int(os.environ.get("PERCENTAGE_CHANGE", 3))
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

# Initialize Redis client
redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT)
