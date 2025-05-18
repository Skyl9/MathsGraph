from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.auth import Token, UserCreate, User, PasswordResetRequestSchema, PasswordResetConfirmSchema
from app.services import AuthService

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=User)
async def register_user(user: UserCreate):
    return AuthService.register_user(user)


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    return AuthService.login_for_access_token(form_data)

@router.post("/password-reset/request")
async def request_password_reset(email: PasswordResetRequestSchema
):
    """
    Route pour obtenir un token de réinitialisation de mot de passe.
    """
    email = email.email
    return AuthService.request_password_reset(email)


@router.post("/password-reset/confirm")
async def reset_password(reset_data: PasswordResetConfirmSchema):
    """
    Route pour réinitialiser le mot de passe via un token valide.
    """
    reset_data = reset_data.model_dump() if isinstance(reset_data, PasswordResetConfirmSchema) else reset_data
    if len(reset_data["new_password"]) < 8:
        raise HTTPException(
            status_code=400,
            detail="Le mot de passe doit faire au moins 8 caractères"
        )
    return AuthService.reset_password(reset_data["token"], reset_data["new_password"])
