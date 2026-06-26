from .auth import User
from .history import History
from .concept import ConceptResponse, ConceptCreate, ConceptBase
from .categorie import CategorieBase
from .source import SourceResponse, SourceCreate, SourceBase
from .relation import RelationResponse, RelationCreate, RelationType
from .mathematicien import MathematicienXConcept, MathematicienCreate, MathematicienBase
from .nom_etranger import NomEtrangerResponse, NomEtrangerCreate, NomEtrangerBase
from .user import UserResponse, UserCreate, UserInDB, UserBase
from .GraphData import GraphData, Nodes, Position
from .Views import Views
from .EditableClass import EditableField
from .response import Response
from .patchClass import UpdateConceptDict, CreateData, CreateAlias, Relation, CreateRelation, Source, CreateSource
from .tags import Tag

# Reconstruire les modèles après avoir tout importé
ConceptResponse.model_rebuild()
SourceResponse.model_rebuild()
RelationResponse.model_rebuild()
MathematicienXConcept.model_rebuild()
NomEtrangerResponse.model_rebuild()
UserResponse.model_rebuild()
Nodes.model_rebuild()
History.model_rebuild()
User.model_rebuild()
Tag.model_rebuild()


__all__ = [
    "ConceptResponse",
    "ConceptCreate",
    "ConceptBase",
    "CategorieBase",
    "SourceResponse",
    "SourceCreate",
    "SourceBase",
    "RelationResponse",
    "RelationCreate",
    "RelationType",
    "MathematicienXConcept",
    "MathematicienCreate",
    "MathematicienBase",
    "NomEtrangerResponse",
    "NomEtrangerCreate",
    "NomEtrangerBase",
    "UserResponse",
    "UserCreate",
    "UserInDB",
    "UserBase",
    "GraphData",
    "Nodes",
    "Position",
    "Views",
    "EditableField",
    "Response",
    "History",
    "Tag",
    "CreateData",
    "CreateAlias",
    "Relation",
    "CreateRelation",
    "Source",
    "CreateSource",
    "UpdateConceptDict",
]
