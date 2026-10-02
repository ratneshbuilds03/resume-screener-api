from sqlalchemy import Column, Integer ,String ,Boolean,DateTime
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    
    __tablename__="users"

    id =Column(Integer,primary_key=True,index=True)
    name =Column(String(200),nullable=False)
    email =Column(String(200),unique=True,nullable=False,index=True)
    password_hash =Column(String(300),nullable=False)
    is_active =Column(Boolean,default=True)
    created_at =Column(DateTime(timezone=True),server_default=func.now())