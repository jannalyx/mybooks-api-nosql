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

class PedidoBase(BaseModel):
    usuario_id: UUID
    data_pedido: date
    status: str
    valor_total: float

class PedidoCreate(PedidoBase):
    pass

class PedidoRead(PedidoBase):
    id: UUID

class PedidoUpdate(BaseModel):
    status: Optional[str] = None
    valor_total: Optional[float] = None

class ContagemPedidos(BaseModel):
    quantidade: int

class PaginatedPedido(BaseModel):
    page: int
    limit: int
    total: int
    items: List[PedidoRead]

class PagamentoBase(BaseModel):
    pedido_id: UUID
    data_pagamento: date
    valor: float
    forma_pagamento: str

class PagamentoCreate(PagamentoBase):
    pass

class PagamentoRead(PagamentoBase):
    id: UUID

class PagamentoUpdate(BaseModel):
    valor: Optional[float] = None
    forma_pagamento: Optional[str] = None

class PaginatedPagamentos(BaseModel):
    page: int
    limit: int
    total: int
    items: List[PagamentoRead]

class PagamentoCount(BaseModel):
    total_pagamentos: int