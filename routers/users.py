
from typing import Optional

from pydantic import BaseModel, Field
from typing_extensions import Annotated
from fastapi import Depends, HTTPException, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from .auth import get_current_user
from passlib.context import CryptContext

router = APIRouter(prefix="/user", tags=["User"])

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChangePasswordRequest(BaseModel):
    password: Annotated[str, Field(min_length=6)]
    new_password: Annotated[str, Field(min_length=6)]        

user_dependency = Annotated[dict, Depends(get_current_user)]   
db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/me", status_code=status.HTTP_200_OK)
async def get_logged_in_user(user:user_dependency, db:db_dependency):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    return db.query(User).filter(User.id == user.get("user_id")).first()

@router.put("/change-password", status_code = status.HTTP_204_NO_CONTENT)
async def change_password(user:user_dependency,db:db_dependency, change_password_request:ChangePasswordRequest):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    user_model = db.query(User).filter(User.id == user.get("user_id")).first()

    if not user_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not pwd_context.verify(change_password_request.password, user_model.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")
    
    user_model.hashed_password = pwd_context.hash(change_password_request.new_password)
    
    db.add(user_model)
    db.commit()