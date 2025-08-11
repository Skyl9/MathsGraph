from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from psycopg import AsyncConnection

from app.core.exceptions import InternalServerError
from app.db.database import get_db
from app.schemas import Response
from app.schemas.auth import Token, UserCreate, User, PasswordResetRequestSchema, PasswordResetConfirmSchema
from app.services import AuthService
from app.services.auth_service import logger

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=Response[User])
async def register_user(user: UserCreate, db: AsyncConnection = Depends(get_db)):
    try:
        user: User = await AuthService(db).register_user(user)
        logger.debug(f"Route POST /register user {user} registered successfully")
        return {"error": None, "success": True, "data": user, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route POST /{router.prefix}/register Erreur : {exc}")
        raise InternalServerError(detail=str(exc))


@router.post("/token", response_model=Response[Token])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: AsyncConnection = Depends(get_db)):
    try:
        token: Token = await AuthService(db).login_for_access_token(form_data)
        logger.debug(f"Route POST /login a token successfully")
        return {"error": None, "success": True, "data": token, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route POST /{router.prefix}/login Erreur : {exc}")
        raise InternalServerError(detail=str(exc))


@router.post("/password-reset/request", response_model=Response[PasswordResetRequestSchema])
async def request_password_reset(email: PasswordResetRequestSchema, db: AsyncConnection = Depends(get_db)):
    """
    Route pour obtenir un token de réinitialisation de mot de passe.
    """
    try:
        message: PasswordResetRequestSchema = await AuthService(db).request_password_reset(email.email)
        logger.debug(f"Route POST /password-request/request Requête envoyé avec succèes")
        return {"error": None, "success": True, "data": message, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route POST /password-reset/request Erreur : {exc}")
        raise InternalServerError(detail=str(exc))


@router.post("/password-reset/confirm", response_model=Response[PasswordResetConfirmSchema])
async def reset_password(reset_data: PasswordResetConfirmSchema, db: AsyncConnection = Depends(get_db)):
    """
    Route pour réinitialiser le mot de passe via un token valide.
    """
    try:
        detail: PasswordResetRequestSchema = await AuthService(db).reset_password(reset_data)
        logger.debug(f"Route POST /password-reset/confirm s'est exécuté correctement, {detail.details}")
    except InternalServerError as exc:
        logger.error(f"Route POST /password-reset/confirm Erreur : {exc}")
        raise InternalServerError(detail=str(exc))
