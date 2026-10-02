from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime ,timedelta
from passlib.context import CryptContext
from app.models.user import User
from app.schemas.user import UserCreate
from app.config import settings


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password:str)->str:
    return pwd_context.hash(password)

def verify_password(plain:str,hashed:str) -> bool:
    return pwd_context.verify(plain,hashed)

def create_access_token(user_id:int) -> str:
    expire= datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    payload = {"sub":str(user_id),"exp":expire}
    return jwt.encode(payload,settings.SECRET_KEY,algorithm=settings.ALGORITHM)

def signup_user(db:Session,user_data:UserCreate):
    existing= db.query(User).filter(User.email == user_data.email).first()
    if existing :
        return None,"email already registered"
    
    new_user=User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user ,None

def login_user(db:Session,email:str,password:str):
    user=db.query(User).filter(User.email==email).first()
    if not user or not verify_password(password,user.password_hash):
        return None ,"Invalid email or password"
    
    if not user.is_active:
        return None,"Account is deactivated"
    token= create_access_token(user.id)
    return {"access_token":token,"token_type":"bearer"},None