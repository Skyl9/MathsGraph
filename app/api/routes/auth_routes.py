from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.limiter import limiter
from app.schemas.response import Response as ApiResponse
from app.schemas.auth import Token, UserCreate, User, PasswordResetRequestSchema, PasswordResetConfirmSchema
from app.services import AuthService
from app.services.auth_service import logger

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=ApiResponse[User])
@limiter.limit("5/minute")  # Max 5 inscriptions par IP par minute
async def register_user(request: Request, user: UserCreate, db: AsyncSession = Depends(get_db)):
    user_created: User = await AuthService(db).register_user(user)
    await db.commit()
    logger.debug(f"Route POST /register user {str(user_created)} registered successfully")
    return {"error": None, "success": True, "data": user_created, "meta": None}


@router.post("/token", response_model=Token)
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


@router.post("/password-reset/request", response_model=ApiResponse)
@limiter.limit("3/minute")  # Max 3 demandes de reset par IP par minute
async def request_password_reset(
    request: Request, email: PasswordResetRequestSchema, db: AsyncSession = Depends(get_db)
):
    message: dict = await AuthService(db).request_password_reset(email.email)
    await db.commit()
    logger.debug("Route POST /password-request/request Requête envoyé avec succèes")
    return {"error": None, "success": True, "data": message, "meta": None}


@router.post("/password-reset/confirm", response_model=ApiResponse)
async def reset_password(reset_data: PasswordResetConfirmSchema, db: AsyncSession = Depends(get_db)):
    detail: dict = await AuthService(db).reset_password(reset_data)
    await db.commit()
    logger.debug(f"Route POST /password-reset/confirm s'est exécuté correctement, {detail}")
    return {"error": None, "success": True, "data": detail, "meta": None}


@router.post("/logout", summary="Déconnecte l'utilisateur")
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/", secure=True, samesite="none")
    return {"success": True, "data": None, "error": None, "meta": None}
