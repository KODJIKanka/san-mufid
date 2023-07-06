from fastapi import FastAPI, HTTPException, status, Depends
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


def get_user_by_id(db, id:int):
    return db.query(models.User).filter(models.User.id==id).first()



def authenticate_user(db, username: str, password:str):
    user = get_user(db,username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False

    return user


def create_access_token(user):
    try:
        claims = {
            "sub": user.username,
            "role": user.role.value,
            "active": user.is_active,
            "exp": datetime.utcnow() + timedelta(minutes=120),
        }
        return jwt.encode(claims=claims, key=SECRET_KEY, algorithm=ALGORITHM)
    except Exception as ex:
        raise ex


def verify_token(token):
    try:
        payload = jwt.decode(token, key=SECRET_KEY)
        return payload
    except:
        raise Exception("Wrong token")


def check_active(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    active = payload.get("active")
    if not active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please activate your Account first",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        return payload


def check_admin(payload: dict = Depends(check_active)):
    role = payload.get("role")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this route",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        return payload
    
def get_users(db: Session):
    return db.query(models.User).all()




def create_user(db:Session, user:schema.UserCreate):
    db_user = models.User(username=user.username, hashed_password = get_password_hash(user.password), role=user.role)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"db_user" : db_user}

def delete_user(db: Session, id: int):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        return None
    db.delete(user)
    db.commit()
    return user

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
        formatted_size = models.FileModel(size=file[3]).formatted_size
        result.append({"id": file[0], "name": file[1], "content_type": file[2] , "size": formatted_size , "path": file[4], "hash": file[5]})
    return result

def get_file_hash(filepath: str):
    """Calculates the SHA-256 hash of a file"""
    hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hash.update(chunk)
    return hash.hexdigest()