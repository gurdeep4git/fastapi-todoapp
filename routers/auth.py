from datetime import datetime, timedelta, timezone
import re
from typing import Annotated, cast
from fastapi import APIRouter, Depends, HTTPException, Form
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import User
from passlib.context import CryptContext
from jose import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Define the HTTP Bearer scheme for token authentication
http_bearer = HTTPBearer()

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

SECRET_KEY = "063t18vxq8vpazjc0tktwlimcfcszkk3l8n9y5u7g1h2o4r5s6a7d8f9b0"
ALGORITHM = "HS256"

class UserCreate(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: Annotated[str, Field(min_length=5, max_length=100)]
    first_name: Annotated[str, Field(min_length=1, max_length=50)]
    last_name: Annotated[str, Field(min_length=1, max_length=50)]
    password: Annotated[str, Field(min_length=6)]
    role: Annotated[str, Field(min_length=3, max_length=20)]

class LoginRequest(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=50)]
    password: Annotated[str, Field(min_length=6)]    

class UserResponse(BaseModel):
    username: str
    model_config = {
        "from_attributes": True
    }    


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

def create_access_token(
    username: str,
    user_id: int,
    role: str,
    expires_delta: timedelta | None = None
):
    payload = {
        "sub": username,
        "user_id": user_id,
        "role": role
    }

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=30)
    )

    payload["exp"] = expire

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )    

async def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer)]):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")

        if not username or not user_id or not role:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        return {
            "username": username,
            "user_id": user_id,
            "role": role
        }
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    

@router.post('/login', status_code=status.HTTP_200_OK)
async def login(db:db_dependency, login_request: LoginRequest):
    user = db.query(User).filter(User.username == login_request.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    
    if not pwd_context.verify(login_request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    
    token = create_access_token(
        username=cast(str, user.username),
        user_id=cast(int, user.id),
        role=cast(str, user.role)
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(db : db_dependency, user: UserCreate):

    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
    
    if not re.match(r"^[a-zA-Z0-9_]+$", user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username can contain only letters, numbers and underscore"
        )
    
    new_user = User(
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=pwd_context.hash(user.password),
        role=user.role,
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user