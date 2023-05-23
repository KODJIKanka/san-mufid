from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token : str
    token_type : str

class TokenData(BaseModel):
    username : Optional[str]  = None

class User(BaseModel):
    username: str
    #is_active : Optional[bool]  = None

class UserInDB(User):
    hashed_password : str

class UserCreate(User):
    password : str


# Modèle de données pour un document
class Document(BaseModel):
    id: int
    title: str