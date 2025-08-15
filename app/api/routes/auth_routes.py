from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from psycopg import AsyncConnection

from app.core.exceptions import InternalServerError
from app.db.database import get_db
from app.schemas.response import Response as ApiResponse
from app.schemas.auth import Token, UserCreate, User, PasswordResetRequestSchema, PasswordResetConfirmSchema
from app.services import AuthService
from app.services.auth_service import logger

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=ApiResponse[User])
async def register_user(user: UserCreate, db: AsyncConnection = Depends(get_db)):
    try:
        async with db.transaction():
            userCreated: User = await AuthService(db).register_user(user)
        logger.debug(f"Route POST /register user {str(userCreated)} registered successfully")
        return {"error": None, "success": True, "data": userCreated, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route POST /{router.prefix}/register Erreur : {str(exc)}")
        raise InternalServerError(detail=str(exc))


@router.post("/token", response_model=ApiResponse[Token])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: AsyncConnection = Depends(get_db)):
    try:
        async with db.transaction():
            token: Token = await AuthService(db).login_for_access_token(form_data)

        logger.debug(f"Route POST /login a token successfully")
        return {"error": None, "success": True, "data": token, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route POST /{router.prefix}/login Erreur : {str(exc)}")
        raise InternalServerError(detail=str(exc))


@router.post("/password-reset/request", response_model=ApiResponse)
async def request_password_reset(email: PasswordResetRequestSchema, db: AsyncConnection = Depends(get_db)):
    """
    Route pour obtenir un token de réinitialisation de mot de passe.
    """
    try:
        async with db.transaction():
            message: PasswordResetRequestSchema = await AuthService(db).request_password_reset(email.email)

        logger.debug(f"Route POST /password-request/request Requête envoyé avec succèes")
        return {"error": None, "success": True, "data": message, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route POST /password-reset/request Erreur : {str(exc)}")
        raise InternalServerError(detail=str(exc))


@router.post("/password-reset/confirm", response_model=ApiResponse)
async def reset_password(reset_data: PasswordResetConfirmSchema, db: AsyncConnection = Depends(get_db)):
    """
    Route pour réinitialiser le mot de passe via un token valide.
    """
    try:
        async with db.transaction():
            detail: PasswordResetRequestSchema = await AuthService(db).reset_password(reset_data)
        logger.debug(f"Route POST /password-reset/confirm s'est exécuté correctement, {detail}")
        return {"error": None, "success": True, "data": detail, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route POST /password-reset/confirm Erreur : {str(exc)}")
        raise InternalServerError(detail=str(exc))

