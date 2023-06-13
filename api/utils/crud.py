from fastapi import FastAPI, HTTPException
from typing import Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from . import models, schema
from jose  import jwt, JWTError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import databases
import hashlib




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

@property
def formatted_size(self):
        if self.size < 1024:
            return f"{self.size} octets"
        elif self.size < 1024**2:
            return f"{self.size/1024:.2f} Ko"
        else:
            return f"{self.size/1024**2:.2f} Mo"


def create_file(db, name: str, content_type: str, data: bytes, size: int, path : str, hash: str):
    file = models.FileModel(name=name, content_type=content_type, data=data, size=size, path=path, hash=hash)
    db.add(file)
    db.commit()
    db.refresh(file)
    return file


def get_file_data(db, file_id: int):
    file = db.query(models.FileModel).filter(models.FileModel.id==file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return {"name": file.name, "content_type": file.content_type, "size": file.formatted_size, "path":file.path, "hash":file.hash}

def get_all_files(db, skip: int, limit: int):
    files = db.query(models.FileModel.id,models.FileModel.name, models.FileModel.content_type, models.FileModel.size , models.FileModel.path, models.FileModel.hash).offset(skip).limit(limit).all()
    result = []
    for file in files:
        result.append({"id": file[0], "name": file[1], "content_type": file[2] , "size": file[3] , "path": file[4], "hash": file[5]})
    return result


def get_file_hash(filepath: str):
    """Calculates the SHA-256 hash of a file"""
    hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hash.update(chunk)
    return hash.hexdigest()