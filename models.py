# models.py
from sqlalchemy import Column, Integer, String, Float,ForeignKey, Float, DateTime
from sqlalchemy.orm import declarative_base, relationship
from database import Base
from datetime import datetime



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    email = Column(String, unique = True, index=True)
    hashed_password = Column(String)
    posts = relationship("Post",back_populates="author")
    items = relationship("Item",back_populates="author")
    
    

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    body= Column(String)
    author_id = Column(Integer, ForeignKey('users.id'),nullable= False)
    author = relationship('User', back_populates="posts")
    created_at = Column(DateTime, default = datetime.utcnow)

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    body= Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'),nullable= False)
    author = relationship('User', back_populates="items")
    
class Rates(Base):
    __tablename__ = 'rates'

    id = Column(Integer, primary_key= True, index=True)
    usd = Column(Float, default= 1.0)
    rub = Column(Float, default= 90.0)