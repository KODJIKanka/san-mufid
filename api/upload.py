from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, BINARY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import sessionmaker, Session
import io
from typing import List

app = FastAPI()

# Création de la base de données SQLite
engine = create_engine("sqlite:///./files.db")
Base = declarative_base()

class FileModel(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    content_type = Column(String)
    data = Column(BINARY)
    #size = Column(Integer)

Base.metadata.create_all(bind=engine)

# Fonctions CRUD pour la base de données
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_file(db, name: str, content_type: str, data: bytes):
    file = FileModel(name=name, content_type=content_type, data=data)
    db.add(file)
    db.commit()
    db.refresh(file)
    return file

#def get_file(db, file_id: int):
#   return db.query(FileModel).filter(FileModel.id == file_id).first()

#def delete_file(db, file_id: int):
#    db.query(FileModel).filter(FileModel.id == file_id).delete()
#    db.commit()

# Endpoints de l'API
@app.post("/files/")
async def upload_file(file: UploadFile = File(...), db = Depends(get_db)):
    file_data = await file.read()
    new_file = create_file(db, name=file.filename, content_type=file.content_type, data=file_data)
    return {"id": new_file.id, "name": new_file.name}

@app.get("/files/{file_id}")
async def read_file(file_id: int):
    db= SessionLocal()
    file = db.query(FileModel).filter(FileModel.id==file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return {"name": file.name, "content":file.content_type}


@app.get("/allfiles/")
def read_files(skip: int = 0, limit: int = 100, db :Session = Depends(get_db)):
    files = db.query(FileModel.id,FileModel.name, FileModel.content_type).offset(skip).limit(limit).all()
    return files




@app.delete("/files/{file_id}")
def delete_file(file_id: int):
    db = SessionLocal()
    db_file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    db.delete(db_file)
    db.commit()
    return {"message": "File deleted successfully"}
