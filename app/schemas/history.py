from __future__ import annotations  # Activer les annotations différées (Python 3.7+)

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


class History(BaseModel):
    id: int = Field(description="L'identifiant unique de l'entrée d'historique.", examples=[1])
    concept_id: int = Field(description="L'identifiant du concept modifié.", examples=[42])
    modified_by: int = Field(description="L'identifiant de l'utilisateur ayant fait la modification.", examples=[3])
    modified_at: datetime = Field(
        description="La date et l'heure de la modification.", examples=["2026-06-25T14:30:00Z"]
    )
    field_modified: str = Field(description="Le nom du champ modifié.", examples=["enonce"])
    old_value: Any = Field(description="L'ancienne valeur du champ avant modification.", examples=["Ancien énoncé"])
    new_value: Any = Field(description="La nouvelle valeur du champ après modification.", examples=["Nouvel énoncé"])
    version_number: int = Field(description="Le numéro de version du concept.", examples=[5])
    global_version: int = Field(description="Le numéro de version globale de la base.", examples=[120])
    is_rollback: bool = Field(description="Indique si cette entrée représente un rollback.", examples=[False])
    note: Optional[str] = Field(
        default=None,
        description="Une note optionnelle justifiant la modification.",
        examples=["Correction d'une faute de frappe"],
    )
