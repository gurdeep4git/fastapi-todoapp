
from typing import Optional

from pydantic import BaseModel, Field
from typing_extensions import Annotated
from fastapi import Depends, HTTPException, HTTPException, Path, status, APIRouter
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Todos
from .auth import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

user_dependency = Annotated[dict, Depends(get_current_user)]   
db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/todo", status_code=status.HTTP_200_OK)
async def get_all_todos(user:user_dependency, db:db_dependency):
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    return db.query(Todos).all()

@router.delete("todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user:user_dependency, db:db_dependency, todo_id:int = Path(gt=0)):
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    todo = db.query(Todos).filter(Todos.id == todo_id).first()

    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    
    db.delete(todo)
    db.commit()
