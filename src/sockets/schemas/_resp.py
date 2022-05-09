from pydantic import BaseModel

__all__ = ("SockResponse",)


class SockResponse(BaseModel):
    ok: bool = True
    error: str = None
    data: dict = None
