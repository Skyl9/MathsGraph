from pydantic import BaseModel, Field


class Tag(BaseModel):
    id: int = Field(..., description="L'identifiant unique du tag", examples=[1])
    tag: str = Field(..., description="Le nom ou la valeur du tag", examples=["Algèbre"])


class TagsCreate(BaseModel):
    tag_name: str = Field(..., description="Le nom du nouveau tag à créer", examples=["Topologie"])


class TagsUpdate(BaseModel):
    tag_id: int = Field(..., description="L'identifiant du tag à mettre à jour", examples=[1])
    concept_id: int = Field(..., description="L'identifiant du concept à lier ou délier avec ce tag", examples=[42])
