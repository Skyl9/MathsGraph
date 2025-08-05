from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from psycopg import AsyncConnection

from app.db.database import get_db
from app.schemas.auth import Token, UserCreate, User, PasswordResetRequestSchema, PasswordResetConfirmSchema
from app.services import AuthService

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=User)
async def register_user(user: UserCreate,db:AsyncConnection = Depends(get_db)):
    return await AuthService(db).register_user(user)


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),db:AsyncConnection = Depends(get_db)):
    return await AuthService(db).login_for_access_token(form_data)

@router.post("/password-reset/request")
async def request_password_reset(email: PasswordResetRequestSchema,db:AsyncConnection = Depends(get_db)):
    """
    Route pour obtenir un token de réinitialisation de mot de passe.
    """
    return await AuthService(db).request_password_reset(email.email)


@router.post("/password-reset/confirm")
async def reset_password(reset_data: PasswordResetConfirmSchema,db:AsyncConnection = Depends(get_db)):
    """
    Route pour réinitialiser le mot de passe via un token valide.
    """
    return await AuthService(db).reset_password(reset_data)
