from sqlalchemy import Boolean, Column, Integer, String, DateTime, BINARY, ForeignKey, Enum
import datetime
from typing import Optional
from sqlalchemy.orm import relationship
from .sandb import Base
from .schema import Roles






# Définition de la table utilisateur
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime, default = datetime.datetime.utcnow)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default = True)
    role = Column(Enum(Roles), default="user")
    
    
# Définition de la table document
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