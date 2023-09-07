from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from utils import  models, schema, crud
from utils.sandb import SessionLocal, engine
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import datetime
import os, sys
import uvicorn

models.Base.metadata.create_all(bind=engine)



app = FastAPI()


app.add_middleware(CORSMiddleware,
                   allow_methods = ["*"],
                   allow_headers = ["*"],
                   allow_credentials = True,
                   allow_origins = ["*"])


def get_db():
    db = SessionLocal()
    try:
        yield db

    finally:
        db.close()

ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")




async def get_current_user(db:Session = Depends(get_db) ,token:str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

    try:
        payload = jwt.decode(token, crud.SECRET_KEY,algorithms=[crud.ALGORITHM] )
        username : str = payload.get("sub")
        if username is None:
            raise credentials_exception

        token_data = username

    except JWTError:
        raise credentials_exception

    user = crud.get_user(db, username = token_data)
    if user is None:
        raise credentials_exception
    return user

@app.post("/token")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    db_user = crud.get_user(db=db, username=form_data.username)
    role = db_user.role
    if not db_user:
        raise HTTPException(
            status_code=401, detail="Anmeldeinformationen nicht korrekt"
        )

    if crud.verify_password(form_data.password, db_user.hashed_password):
        token = crud.create_access_token(db_user)
        return {"access_token": token, "token_Type": "bearer", "role" : role}
    raise HTTPException(status_code=401, detail="Anmeldeinformationen nicht korrekt")


@app.post("/users/")
def create_user(
    user:schema.UserCreate, db: Session=Depends(get_db)
):

     db_user = crud.get_user(db, username=user.username)
     if db_user:
        raise HTTPException(status_code=400, detail="This user already registered")
     return crud.create_user(db=db, user=user)


@app.get("/verify/{token}")
def login_user(token: str, db: Session = Depends(get_db)):
    payload = crud.verify_token(token)
    username = payload.get("sub")
    db_user = crud.get_user(db, username)
    db_user.is_active = True
    db.commit()
    return username
    


@app.get("/adminsonly", dependencies=[Depends(crud.check_admin)])
def get_all_users(db: Session = Depends(get_db)):
    users = crud.get_users(db=db)
    return users

@app.delete("/users/{id}", dependencies=[Depends(crud.check_admin)])
def delete_user(id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_id(db, id= id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    crud.delete_user(db, id = id)
    return {"message": "User deleted successfully"}



#Opérations sur les fichiers

@app.post("/files/", dependencies=[Depends(crud.check_admin)])
async def upload_file(
    file: UploadFile = File(...), db=Depends(get_db)
):
    
    file_data = await file.read()
    filename = file.filename
    filepath = os.path.join("uploads", filename)
    with open(filepath, "wb") as f:
        f.write(file_data)
    file_hash = crud.get_file_hash(filepath)

    existing_file = db.query(models.FileModel).filter(models.FileModel.hash == file_hash).first()
    if existing_file:
        raise HTTPException(status_code=409, detail="File already exists in the database")

    new_file = crud.create_file(
        db, name=file.filename, content_type=file.content_type, data=file_data, size=len(file_data), path=filepath, hash=file_hash
    )

    return {
        "id": new_file.id,
        "name": new_file.name,
        "content": new_file.content_type,
        "formatted_size": new_file.formatted_size,
        "path": new_file.path,
        "hash": new_file.hash,
    }

@app.get("/files/{file_id}", dependencies=[Depends(crud.check_active)])
async def read_file(file_id: int, db = Depends(get_db)):
    return crud.get_file_data(db, file_id)


@app.get("/allfiles/", dependencies=[Depends(crud.check_active)])
def read_files(skip: int = 0, limit: int = 100, db = Depends(get_db)):
    return crud.get_all_files(db, skip, limit)


@app.delete("/files/{file_id}", dependencies=[Depends(crud.check_admin)])
def delete_file(file_id: int, db=Depends(get_db)):
    db_file = db.query(models.FileModel).filter(models.FileModel.id == file_id).first()
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    os.remove(db_file.path)
    db.delete(db_file)
    db.commit()
    return {"message": "File deleted successfully"}




if __name__ == "__main__":
    uvicorn.run(app, host = "127.0.0.1", port = 8000)
