from pydantic import BaseModel


class TokenPayload(BaseModel):
    sub : str
    id : int|str
    role : str = "user"
