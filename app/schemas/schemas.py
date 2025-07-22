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

# ----------- LIVRO -----------

class LivroCreate(BaseModel):
    titulo: str
    sinopse: Optional[str] = None
    genero: str
    preco: float
    data_publicacao: date
    autor_id: UUID
    editora_id: UUID

class LivroUpdate(BaseModel):
    titulo: Optional[str] = None
    sinopse: Optional[str] = None
    genero: Optional[str] = None
    preco: Optional[float] = None
    data_publicacao: Optional[date] = None
    autor_id: Optional[UUID] = None
    editora_id: Optional[UUID] = None

class LivroRead(BaseModel):
    id: UUID
    titulo: str
    sinopse: Optional[str] = None
    genero: str
    preco: float
    data_publicacao: date
    autor_id: UUID
    editora_id: UUID

    class Config:
        orm_mode = True

class LivroCount(BaseModel):
    total_livros: int

class PaginatedLivros(BaseModel):
    page: int
    limit: int
    total: int
    items: List[LivroRead]

    class Config:
        orm_mode = True
        
# ----------- USUARIO -----------

class UsuarioCreate(BaseModel):
    nome: str
    email: str
    cpf: str

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    cpf: Optional[str] = None

class UsuarioRead(BaseModel):
    id: UUID
    nome: str
    email: str
    cpf: str
    data_cadastro: date

    class Config:
        orm_mode = True

class UsuarioCount(BaseModel):
    total_usuarios: int

class PaginatedUsuario(BaseModel):
    page: int
    limit: int
    total: int
    items: List[UsuarioRead]

    class Config:
        orm_mode = True
    
# ----------- PEDIDO -----------

class PedidoCreate(BaseModel):
    usuario_id: UUID
    status: str
    valor_total: float
    data_pedido: date

class PedidoUpdate(BaseModel):
    usuario_id: Optional[UUID] = None
    status: Optional[str] = None
    valor_total: Optional[float] = None
    data_pedido: Optional[date] = None

class PedidoRead(BaseModel):
    id: UUID
    usuario_id: UUID
    status: str
    valor_total: float
    data_pedido: date

    class Config:
        orm_mode = True

class ContagemPedidos(BaseModel):
    quantidade: int

class PaginatedPedido(BaseModel):
    page: int
    limit: int
    total: int
    items: List[PedidoRead]

    class Config:
        orm_mode = True


# ----------- LIVRO_PEDIDO -----------

class PedidoLivroBase(BaseModel):
    pedido_id: UUID
    livro_id: UUID

class PedidoLivroCreate(PedidoLivroBase):
    pass

class PedidoLivroRead(PedidoLivroBase):
    class Config:
        orm_mode = True

class PaginatedPedidoLivro(BaseModel):
    page: int
    limit: int
    total: int
    items: List['LivroInfo']

    class Config:
        orm_mode = True

class LivroInfo(BaseModel):
    id: UUID
    titulo: str
    autor_nome: str

    class Config:
        orm_mode = True

# ----------- PAGAMENTO -----------

class PagamentoCreate(BaseModel):
    pedido_id: UUID
    valor: float
    data_pagamento: date
    forma_pagamento: str

class PagamentoUpdate(BaseModel):
    pedido_id: Optional[UUID] = None
    valor: Optional[float] = None
    data_pagamento: Optional[date] = None
    forma_pagamento: Optional[str] = None

class PagamentoRead(BaseModel):
    id: UUID
    pedido_id: UUID
    valor: float
    data_pagamento: date
    forma_pagamento: str

    class Config:
        orm_mode = True

class PagamentoCount(BaseModel):
    total_pagamentos: int

class PaginatedPagamentos(BaseModel):
    page: int
    limit: int
    total: int
    items: List[PagamentoRead]

    class Config:
        orm_mode = True

# ----------- PEDIDO_PAGAMENTO -----------

class PedidoPagamentoBase(BaseModel):
    pedido_id: UUID
    pagamento_id: UUID

class PedidoPagamentoCreate(PedidoPagamentoBase):
    pass

class PedidoPagamentoRead(PedidoPagamentoBase):
    class Config:
        orm_mode = True

class PedidoPagamentoCount(BaseModel):
    total_pedido_pagamentos: int

class PaginatedPedidoPagamento(BaseModel):
    page: int
    limit: int
    total: int
    items: List[PedidoPagamentoRead]

    class Config:
        orm_mode = True

# ----------- PEDIDO DETALHADO -----------

class LivroInfo(BaseModel):
    id: UUID
    titulo: str
    autor_nome: str

class PagamentoInfo(BaseModel):
    id: UUID
    valor: float
    data_pagamento: str

class PedidoDetalhado(BaseModel):
    id: UUID
    data_pedido: str 
    livros: List[LivroInfo]
    pagamentos: List[PagamentoInfo]

    class Config:
        orm_mode = True
