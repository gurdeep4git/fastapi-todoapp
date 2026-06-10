from database import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    role = Column(String(20))

class Todos(Base):
    __tablename__ = "todos"

    id =  Column(Integer, primary_key=True, index=True)
    title =  Column(String(100), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    priority = Column(Integer, nullable=False)
    complete = Column(Boolean, nullable=False, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))