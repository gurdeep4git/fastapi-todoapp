
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from fastapi import Depends, HTTPException, HTTPException, Path, status, APIRouter
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Todos
from .auth import get_current_user

router = APIRouter(prefix="/todos", tags=["Todos"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

user_dependency = Annotated[dict, Depends(get_current_user)]        

class TodoCreate(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=255)
    priority: int = Field(gt=0, lt=6)
    complete: bool = Field(default=False)    

@router.get('', status_code=status.HTTP_200_OK)
async def read_todos(user: user_dependency, db:Annotated[Session, Depends(get_db)]):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    todos = db.query(Todos).filter(Todos.owner_id == user["user_id"]).all()
    return todos

@router.get("/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(user:user_dependency, db:Annotated[Session, Depends(get_db)], todo_id: int = Path(gt=0)):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    todo = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user["user_id"]).first()
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo

@router.post('', status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db:Annotated[Session, Depends(get_db)], todo: TodoCreate):
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    # Bussiness logic: Check if a todo with the same title already exists
    existing_todo = db.query(Todos).filter(Todos.title == todo.title).first()
    if existing_todo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Todo with this title already exists")
    
    new_todo = Todos(**todo.model_dump(), owner_id=user["user_id"])
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return new_todo

@router.put("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user:user_dependency, db:Annotated[Session, Depends(get_db)], todo: TodoCreate, todo_id: int = Path(gt=0)):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    existing_todo = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user["user_id"]).first()
    if not existing_todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    
    # Update the fields of the existing todo
    for key, value in todo.model_dump().items():
        setattr(existing_todo, key, value)
    
    db.commit()
    db.refresh(existing_todo)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db:Annotated[Session, Depends(get_db)], todo_id: int = Path(gt=0)):
    todo_to_delete = db.query(Todos).filter(Todos.id == todo_id).first()
    if not todo_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    
    db.delete(todo_to_delete)
    db.commit()