from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, Token
from app.security import create_access_token, pwd_context

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username, User.is_active.is_(True)))
    if not user or not pwd_context.verify(payload.password, user.password_hash):
        raise HTTPException(401, "Incorrect username or password")
    return Token(access_token=create_access_token(user), role=user.role)
