from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, BINARY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import sessionmaker, Session
import io
import os
import hashlib

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
    size = Column(Integer)
    path = Column(String)
    hash = Column(String)

    @property
    def formatted_size(self):
        if self.size < 1024:
            return f"{self.size} octets"
        elif self.size < 1024**2:
            return f"{self.size/1024:.2f} Ko"
        else:
            return f"{self.size/1024**2:.2f} Mo"

Base.metadata.create_all(bind=engine)

# Fonctions CRUD pour la base de données
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_file(db, name: str, content_type: str, data: bytes, size: int, path: str, hash: str):
    file = FileModel(name=name, content_type=content_type, data=data, size=size, path=path, hash=hash)
    db.add(file)
    db.commit()
    db.refresh(file)
    return file

def get_file_data(db, file_id: int):
    file = db.query(FileModel).filter(FileModel.id==file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return {"name": file.name, "content_type": file.content_type, "formatted_size": file.formatted_size, "path": file.path, "hash": file.hash}

def get_all_files(db, skip: int, limit: int):
    files = db.query(FileModel.id,FileModel.name, FileModel.content_type, FileModel.size, FileModel.path, FileModel.hash).offset(skip).limit(limit).all()
    result = []
    for file in files:
        result.append({"id": file[0], "name": file[1], "content_type": file[2], "formatted_size": file.formatted_size, "path": file[4], "hash": file[5]})
    return result

def get_file_hash(filepath: str):
    """Calculates the SHA-256 hash of a file"""
    hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hash.update(chunk)
    return hash.hexdigest()

# Endpoints de l'API
@app.post("/files/")
async def upload_file(file: UploadFile = File(...), db = Depends(get_db)):
    file_data = await file.read()
    filename = file.filename
    filepath = os.path.join('uploads', filename)
    with open(filepath, 'wb') as f:
        f.write(file_data)

    file_hash = get_file_hash(filepath)

    new_file = create_file(db, name=file.filename, content_type=file.content_type, data=file_data, size=len(file_data), path=filepath, hash=file_hash)

    return {"id": new_file.id, "name": new_file.name,"content": new_file.content_type, "formatted_size": new_file.formatted_size, "path": new_file.path, "hash": new_file.hash}

@app.get("/files/{file_id}")
async def read_file(file_id: int, db = Depends(get_db)):
    return get_file_data(db, file_id)

@app.get("/allfiles/")
def read_files(skip: int = 0, limit: int = 100, db = Depends(get_db)):
    return get_all_files(db, skip, limit)

@app.delete("/files/{file_id}")
def delete_file(file_id: int, db = Depends(get_db)):
    db_file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    os.remove(db_file.path)
    db.delete(db_file)
    db.commit()
    return {"message": "File deleted successfully"}