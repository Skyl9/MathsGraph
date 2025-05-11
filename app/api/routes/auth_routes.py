from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.auth import Token, UserCreate, User
from app.services import AuthService

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=User)
async def register_user(user: UserCreate):
    return AuthService.register_user(user)


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    return AuthService.login_for_access_token(form_data)
