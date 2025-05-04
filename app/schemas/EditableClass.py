from typing import Optional

from pydantic import BaseModel

from app.schemas import CategorieBase
from app.schemas.mathematicien import MathematicienResponse


class EditableField(BaseModel):
    mathematicien : MathematicienResponse
    categorie : CategorieBase
    type : Optional[str] = None