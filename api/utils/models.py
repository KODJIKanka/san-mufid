from sqlalchemy import Boolean, Column, Integer, String, DateTime, BINARY
import datetime

from .sandb import Base





# Définition de la table utilisateur
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime, default = datetime.datetime.utcnow)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default = True)


# Définition de la table document
class FileModel(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    content_type = Column(String)
    data = Column(BINARY)
    