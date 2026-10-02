from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.limiter import limiter
from app.schemas.user import Token, UserCreate, UserResponse
from app.services.auth_services import login_user, signup_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    new_user, error = signup_user(db, user)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return new_user


@router.post("/login", response_model=Token)
@limiter.limit("200/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    result, error = login_user(db, form_data.username, form_data.password)
    if error:
        raise HTTPException(status_code=401, detail=error)
    return result