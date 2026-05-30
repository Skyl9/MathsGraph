from typing import Optional, Literal

from pydantic import BaseModel


class RelationType(BaseModel):
    id: int
    description: Optional[str] = None
    date_relation: Optional[str] = None


class RelationCreate(RelationType):
    pass

class ConceptRelation(BaseModel):
    id: int
    nom: str
class RelationResponse(RelationType):
    concept_source: ConceptRelation
    concept_cible: ConceptRelation
    type_relation: Literal["reciproque", "equivalence", "implication", "utilise"]

