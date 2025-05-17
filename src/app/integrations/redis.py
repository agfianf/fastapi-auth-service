import json
from redis import Redis

from app.config import settings


class RedisHelper:
    def __init__(self) -> None:
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
        )

    def ping(self) -> bool:
        return self.redis.ping()

    def set_data(
        self,
        key: str,
        value: str | float | bool,
        expire_sec: int | None = None,
    ) -> None:
        if isinstance(value, bool):
            value = int(value)

        if expire_sec is None:
            self.redis.set(
                name=key,
                value=value,
            )
        else:
            self.redis.setex(
                name=key,
                time=expire_sec,
                value=value,
            )

    def delete_data(self, key: str) -> None:
        self.redis.delete(key)

    def get_boolean(self, key: str) -> bool | None:
        value = self.redis.get(key)
        if value is not None:
            decoded_value = int(value.decode("utf-8"))
            decoded_value = bool(decoded_value)
        return decoded_value

    def get_data(self, key: str) -> str | None:
        value = self.redis.get(key)
        if value is not None:
            value = value.decode("utf-8")
        return value

    def add_token_to_blacklist(
        self,
        token: str,
        expire_sec: int | None = None,
    ) -> None:
        if expire_sec is None:
            expire_sec = settings.AUTH_TOKEN_REFRESH_EXPIRE_MINUTES * 60

        self.set_data(
            key=token,
            expire_sec=expire_sec,
            value="blacklist",
        )

    def is_token_revoked(self, token: str) -> bool:
        result = self.get_data(token)
        return result == "blacklist"
        
    # User caching methods
    def cache_user_details(self, user_uuid: str, user_data: dict, expire_sec: int = 300) -> None:
        """Cache user details with a TTL.
        
        Parameters
        ----------
        user_uuid : str
            The UUID of the user
        user_data : dict
            The user data to cache
        expire_sec : int, optional
            Cache expiration time in seconds, by default 300 (5 minutes)
        """
        key = f"user:{user_uuid}"
        self.redis.setex(
            name=key,
            time=expire_sec,
            value=json.dumps(user_data),
        )
    
    def get_cached_user_details(self, user_uuid: str) -> dict | None:
        """Get cached user details.
        
        Parameters
        ----------
        user_uuid : str
            The UUID of the user
            
        Returns
        -------
        dict | None
            The cached user data or None if not found
        """
        key = f"user:{user_uuid}"
        data = self.redis.get(key)
        if data is not None:
            return json.loads(data.decode("utf-8"))
        return None
    
    def invalidate_user_cache(self, user_uuid: str) -> None:
        """Invalidate cached user details.
        
        Parameters
        ----------
        user_uuid : str
            The UUID of the user
        """
        key = f"user:{user_uuid}"
        self.redis.delete(key)
