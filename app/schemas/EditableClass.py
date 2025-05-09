from typing import Optional, List

from pydantic import BaseModel


class EditableField(BaseModel):
    mathematicien : List[str]
    categorie : List[str]
    type : Optional[List[str]] = None