from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_payload
from app.core.limiter import limiter
from app.db.database import get_db
from app.schemas.auth import Token, UserCreate, User, PasswordResetRequestSchema, PasswordResetConfirmSchema
from app.schemas.response import Response as ApiResponse
from app.services import AuthService
from app.services.auth_service import logger

router = APIRouter(tags=["authentication"])


@router.post(
    "/register",
    summary="Inscrit un nouvel utilisateur",
    description="Crée un nouveau compte utilisateur avec les informations fournies. Soumis à une limitation de requêtes.",
    response_model=ApiResponse[User],
)
@limiter.limit("5/minute")  # Max 5 inscriptions par IP par minute
async def register_user(request: Request, user: UserCreate, db: AsyncSession = Depends(get_db)):
    user_created: User = await AuthService(db).register_user(user)
    await db.commit()
    logger.debug("Route POST /register user registered successfully")
    return {"error": None, "success": True, "data": user_created, "meta": None}


@router.post(
    "/token",
    summary="Authentifie un utilisateur (Login)",
    description="Vérifie les identifiants et génère un jeton d'accès (JWT) retourné dans la réponse et placé dans un cookie de session.",
    response_model=Token,
)
@limiter.limit("10/minute")  # Max 10 tentatives de login par IP par minute
async def login_for_access_token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    token: Token = await AuthService(db).login_for_access_token(form_data, response)
    await db.commit()
    logger.debug("Route POST /token: access token generated and session saved successfully")
    return token


@router.post(
    "/password-reset/request",
    summary="Demande de réinitialisation de mot de passe",
    description="Génère un lien ou code de réinitialisation envoyé par email si l'adresse est associée à un compte.",
    response_model=ApiResponse,
)
@limiter.limit("3/minute")  # Max 3 demandes de reset par IP par minute
async def request_password_reset(
    request: Request, email: PasswordResetRequestSchema, db: AsyncSession = Depends(get_db)
):
    message: dict = await AuthService(db).request_password_reset(email.email)
    await db.commit()
    logger.debug("Route POST /password-request/request Requête envoyé avec succèes")
    return {"error": None, "success": True, "data": message, "meta": None}


@router.post(
    "/password-reset/confirm",
    summary="Confirme la réinitialisation de mot de passe",
    description="Permet de définir un nouveau mot de passe en utilisant le jeton de réinitialisation valide.",
    response_model=ApiResponse,
)
async def reset_password(reset_data: PasswordResetConfirmSchema, db: AsyncSession = Depends(get_db)):
    detail: dict = await AuthService(db).reset_password(reset_data)
    await db.commit()
    logger.debug(f"Route POST /password-reset/confirm s'est exécuté correctement, {detail}")
    return {"error": None, "success": True, "data": detail, "meta": None}


@router.post(
    "/logout",
    summary="Déconnecte l'utilisateur",
    description="Supprime le cookie de session contenant le jeton d'accès pour déconnecter l'utilisateur.",
    response_model=ApiResponse,
)
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/", secure=True, samesite="none")
    return {"success": True, "data": None, "error": None, "meta": None}


@router.get(
    "/me",
    summary="Récupère les informations de l'utilisateur connecté depuis le cookie",
    description="Renvoie les détails du profil de l'utilisateur actuellement authentifié via son token JWT.",
    response_model=ApiResponse,
)
async def get_me(current_user: dict = Depends(get_current_user_payload)):
    return {"error": None, "success": True, "data": current_user, "meta": None}
