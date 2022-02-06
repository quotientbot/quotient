from pydantic import BaseModel, HttpUrl


class SS(BaseModel):
    url: HttpUrl
