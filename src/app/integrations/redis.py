import json

from redis import Redis

from app.config import settings


class RedisHelper:
    def __init__(self) -> None:
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
        )

    def ping(self) -> bool:
        """Check if Redis is alive."""
        return bool(self.redis.ping())

    def set_data(
        self,
        key: str,
        value: str | bool,
        expire_sec: int | None = None,
    ) -> None:
        """Set data to Redis."""
        is_bool = isinstance(value, bool)
        if expire_sec:
            self.redis.setex(
                name=key,
                time=expire_sec,
                value="1" if is_bool and value else "0" if is_bool else value,
            )
        else:
            self.redis.set(
                name=key,
                value="1" if is_bool and value else "0" if is_bool else value,
            )

    def delete_data(self, key: str) -> None:
        """Delete data from Redis."""
        self.redis.delete(key)

    def get_boolean(self, key: str) -> bool | None:
        """Get boolean data from Redis."""
        value = self.redis.get(key)
        if value is None:
            return None
        return value == b"1"

    def get_data(self, key: str) -> str | None:
        """Get data from Redis."""
        value = self.redis.get(key)
        return value.decode("utf-8") if value else None

    def add_token_to_blacklist(
        self,
        token: str,
        expire_sec: int | None = None,
    ) -> None:
        """Add token to blacklist."""
        self.set_data(
            key=token,
            value="blacklist",
            expire_sec=expire_sec,
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