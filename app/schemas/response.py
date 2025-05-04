from pydantic import BaseModel


class Response(BaseModel):
    message: str
    status: int
    data: dict