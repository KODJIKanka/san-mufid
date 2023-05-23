from fastapi import FastAPI
from typing import Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from . import models, schema
from jose  import jwt, JWTError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import databases




SECRET_KEY = "9974f24d4d45f7c4df06e68b181812ed291f3f39ba57814adbd6547e9c5c187f"
ALGORITHM = "HS256"



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Créer la fonction pour générer les mots de passe hashés
def get_password_hash(password):
    return pwd_context.hash(password)

# Créer la fonction pour récupérer un utilisateur par nom d'utilisateur

def get_user(db, username:str):
    return db.query(models.User).filter(models.User.username==username).first()


def authenticate_user(db, username: str, password:str):
    user = get_user(db,username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False

    return user


def create_access_token(data:dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_user(db:Session, user:schema.UserCreate):
    db_user = models.User(username=user.username, hashed_password=get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_file(db, name: str, content_type: str, data: bytes):
    file = models.FileModel(name=name, content_type=content_type, data=data)
    db.add(file)
    db.commit()
    db.refresh(file)
    return file

