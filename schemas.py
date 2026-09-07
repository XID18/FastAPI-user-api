from pydantic import BaseModel, Field,EmailStr
import requests
from fastapi import HTTPException
from  models import Rates
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: str
    age: int

class UserRegister(UserBase):
     email: EmailStr
     password : str
     

class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    email: EmailStr
    

    class Config:
        
        from_attributes=True

class Token(BaseModel):
     access_token : str
     token_type: str

class UserUpdate(UserBase):
     email: EmailStr


class UserPatch(UserBase):
     name : Optional[str] = None
     age : Optional[int] = None
     email : Optional[str] = None



class PostBase(BaseModel):
    title: str = Field(min_lenght = 3, max_lenght= 100)
    body: str = Field(min_lenght = 3)
    author_id: int
    created_at : datetime


class PostCreate(BaseModel):
    title : str
    body : str


class PostResponse(PostBase):
    id: int
    author: User

    class Config:
            
            from_attributes=True

class PostPatch(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None

class PostUpdate(PostBase):
    
     title : str
     body : str

class ItemBase(BaseModel):
    title: str
    body: str
    author_id: int
    

class ItemPatch(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class ItemResponse(ItemBase):
    id: int
    author: User
    

    class Config:
            
            from_attributes=True


class RateCreate(BaseModel):
     usd : float = 1.0
     rub : float = 90.0
     



class RateResponse(BaseModel):

    id: int
    usd: float
    rub: float

    class Config:
         from_attributes = True





