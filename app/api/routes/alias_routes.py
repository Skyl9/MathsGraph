from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.core.deps import get_current_user_payload
from app.core.exceptions import InternalServerError
from app.db.database import get_db
from app.schemas import CreateAlias, Response
from app.services.alias_service import AliasService, logger

router = APIRouter(prefix="/alias", tags=["alias"])


@router.post("/create", response_model=Response)
async def create_alias(
    data: CreateAlias, 
    db: AsyncConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload)
):
    """Crée un alias à partir d'un nom d'utilisateur et d'un prénom.

    Cette fonction crée un nouvel alias en utilisant les données
    fournies et les stocke dans la base de données. Elle gère la
    connexion à la base de données de manière asynchrone et
    s'assure que l'opération est atomique.

    Args:
        data: Les informations nécessaires pour créer un alias.
            Inclut `username` et `first_name`.
        db: La connexion asynchrone à la base de données.

    Returns:
        Un dictionnaire représentant une réponse standard de l'API.

    Raises:
        InternalServerError: Si une erreur survient lors de la
            création de l'alias dans la base de données.
    """
    try:
        async with db.transaction():
            await AliasService(db).add_alias(data)
        logger.debug(f"Route POST /{router.prefix}/alias : {str(data)} ")
        return {"success": True, "data": None, "meta": None, "error": None}
    except InternalServerError as exc:
        logger.error(f"Route POST /{router.prefix}/alias : {str(exc)}")
        raise InternalServerError(detail=str(exc))
