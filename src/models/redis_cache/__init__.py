import aioredis
from aioredis.commands import Redis
from .key_maker import make_key
import pickle
from .utils import MISSING
from typing import Optional
import functools
from tortoise.models import Model


class NotInitialized(RuntimeError):
    def __init__(self) -> None:
        super().__init__("You must initalize redis cache before using it.")


class RedisCache:
    _initialized = False
    _pool: Redis = None

    @classmethod
    async def init(cls, *args, **kwargs):
        """Initalize redis cache."""

        if cls._initialized:
            cls._pool.close()

        cls._pool = await aioredis.create_redis_pool(*args, **kwargs)
        cls._initialized = True

    @classmethod
    def get_pool(cls):
        if not cls._initialized:
            raise NotInitialized

        return cls._pool

    @classmethod
    def close(cls, verbose=False):
        if verbose and not cls._initialized:
            raise NotInitialized

        if cls._pool is not None:
            cls._pool.close()


def cache(prefix: Optional[str] = MISSING):
    """A decorator for caching asyncio coroutines. (This is just made for quotient-bot only, you might have to customize it before using.)"""

    def decorator(func):
        func.__prefix = prefix

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = make_key(func, *args, **kwargs)
            value = await RedisCache.get_pool().get(key)
            if value is None:
                value = await func(*args, **kwargs)
                await RedisCache.get_pool().set(key, pickle.dumps(value))
            else:
                value = pickle.loads(value)
            return value

        wrapper.make_key = lambda *args, **kwargs: make_key(func, *args, **kwargs)

        async def invalidate(*args, **kwargs):
            key = make_key(func, *args, **kwargs)
            return RedisCache.get_pool().delete(key)

        wrapper.invalidate = invalidate
        return wrapper

    return decorator


def model_cache(prefix: Optional[str] = MISSING):
    def decorator(func):
        func.__prefix = prefix

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = make_key(func, args, kwargs.copy(), ignore=("cls",))
            value = await RedisCache.get_pool().get(key)
            if value is None:
                value = await func(*args, **kwargs)
                await RedisCache.get_pool().set(key, pickle.dumps(dict(value)))
            else:
                value = args[0](**pickle.loads(value))
            return value

        async def invalidate(*args, **kwargs):
            key = make_key(func, (None,) + args, kwargs.copy(), ignore=("cls",))
            return await RedisCache.get_pool().delete(key)

        wrapper.invalidate = invalidate
        return wrapper

    return decorator
