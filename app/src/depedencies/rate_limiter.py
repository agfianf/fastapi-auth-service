from slowapi import Limiter
from slowapi.util import get_remote_address
from src.config import settings


redis_uri = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=redis_uri,
    default_limits=["60/minute"],
)

critical_limit = "10/minute"
default_limit = "60/minute"
free_limit = "120/minute"
