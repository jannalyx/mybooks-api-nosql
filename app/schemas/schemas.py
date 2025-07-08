from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel
from datetime import date

# ----------- AUTOR -----------

class AutorCreate(BaseModel):
    nome: str
    email: str
    data_nascimento: date
    nacionalidade: str
    biografia: Optional[str] = None

class AutorUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    data_nascimento: Optional[date] = None
    nacionalidade: Optional[str] = None
    biografia: Optional[str] = None

class AutorRead(BaseModel):
    id: UUID
    nome: str
    email: str
    data_nascimento: date
    nacionalidade: str
    biografia: Optional[str] = None

    class Config:
        orm_mode = True

class AutorCount(BaseModel):
    total_autores: int

class PaginatedAutor(BaseModel):
    page: int
    limit: int
    total: int
    items: List[AutorRead]

    class Config:
        orm_mode = True

# ----------- EDITORA -----------

class EditoraCreate(BaseModel):
    nome: str
    endereco: str
    telefone: str
    email: str

class EditoraUpdate(BaseModel):
    nome: Optional[str] = None
    endereco: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None

class EditoraRead(BaseModel):
    id: UUID
    nome: str
    endereco: str
    telefone: str
    email: str

    class Config:
        orm_mode = True

class EditoraCount(BaseModel):
    total_editoras: int

class PaginatedEditoras(BaseModel):
    page: int
    limit: int
    total: int
    items: List[EditoraRead]

    class Config:
        orm_mode = True