from fastapi import FastAPI, HTTPException, UploadFile, Depends, status
from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError
from sqlalchemy.ext.declarative import declarative_base
import chardet
import jwt
import os

SECRET_KEY = "d960c8b12cb5a8c4b8adebc7775e568f4f51f0ac7efec671f2c136d0220f1b69"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configuration de la base de données MySQL
SQLALCHEMY_DATABASE_URL = "sqlite:///./sanDB.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modèle de données pour un utilisateur
class User(BaseModel):
    username: str
    password: str

class UserInDB(User):
    hashed_password : str

class Token(BaseModel):
    access_token : str
    token_type : str

class TokenData(BaseModel):
    username : str or None = None

# Modèle de données pour un document
class Document(BaseModel):
    id: int
    title: str
    content: str

# Définition de la table utilisateur
class UserTable(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String)

# Définition de la table document
class DocumentTable(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50))
    content = Column(String)


Base.metadata.create_all(bind=engine)

# Initialisation de l'application FastAPI
app = FastAPI()


# Créer le contexte de cryptage pour les mots de passe

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Créer l'objet OAuth2PasswordBearer pour gérer l'authentification

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#Créer la fonction pour vérifier les mots de passe

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Créer la fonction pour générer les mots de passe hashés
def get_password_hash(password):
    return pwd_context.hash(password)

# Créer la fonction pour récupérer un utilisateur par nom d'utilisateur

def get_user(db, username):
    if username in db:
        user_data = db[username]
        return UserInDB(**user_data)

def authenticate_user(db, username: str, password:str):
    user = get_user(db,username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False

    return user

def create_access_token(data:dict, expires_delta:timedelta or None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token:str = Depends(oauth2_scheme)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

    try:
        payload = jwt.decode(token, SECRET_KEY,algorithms=[ALGORITHM] )
        username : str = payload.get("sub")
        if username is None:
            raise credential_exception

        token_data = TokenData(username=username)

    except JWTError:
        raise credential_exception

    user = get_user(SQLALCHEMY_DATABASE_URL, username = token_data.username)
    if user is None:
        raise credential_exception
    return user


async def get_current_active_user(current_user : UserInDB = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")

    return current_user

# Créer la route pour se connecter et obtenir un jeton d'accès

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data:OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(SQLALCHEMY_DATABASE_URL, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data= {"sub":user.username},expires_delta=access_token_expires)
    return {"access_token":access_token, "token_type":"bearer"}

@app.get("/users/me/", response_model=User)
async def reade_users_me(current_user : User = Depends(get_current_active_user)):
    return current_user

@app.get("/users/me/items", response_model=User)
async def reade_users_me(current_user : User = Depends(get_current_active_user)):
    return [{"item_id":1, "owner":current_user}]








# Opérations CRUD pour les utilisateurs
@app.post("/users/")
def create_user(user: User):
    db = SessionLocal()
    db_user = UserTable(username=user.username, password=get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}")
def read_user(user_id: int):
    db = SessionLocal()
    db_user = db.query(UserTable).filter(UserTable.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/users/")
def read_users(skip: int = 0, limit: int = 100):
    db = SessionLocal()
    users = db.query(UserTable).offset(skip).limit(limit).all()
    return users

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    db = SessionLocal()
    db_user = db.query(UserTable).filter(UserTable.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}

# Opérations CRUD pour les documents
@app.post("/documents/")
async def create_document(document: UploadFile):
    doc_content = await document.read()
    db = SessionLocal()
    result=chardet.detect(doc_content)
    db_document = DocumentTable(title=doc_content.title, content=result['encoding'])
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

@app.get("/documents/{document_id}")
def read_document(document_id: int):
    db = SessionLocal()
    db_document = db.query(DocumentTable).filter(DocumentTable.id == document_id).first()
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_document

@app.get("/documents/")
def read_documents(skip: int = 0, limit: int = 100):
    db = SessionLocal()
    documents = db.query(DocumentTable).offset(skip).limit(limit).all()
    return documents

@app.delete("/documents/{document_id}")
def delete_document(document_id: int):
    db = SessionLocal()
    db_document = db.query(DocumentTable).filter(DocumentTable.id == document_id).first()
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(db_document)
    db.commit()
    return {"message": "Document deleted successfully"}

