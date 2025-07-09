from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from cassandra.cqlengine.query import DoesNotExist
from app.models.models import Pedido
from datetime import datetime
from app.schemas.schemas import (
    Livro, #ainda n exite '-'
    PedidoCreate,
    PedidoRead,
    PedidoUpdate,
    PaginatedPedido,
    ContagemPedidos
)
from logs.logger import get_logger

logger = get_logger("MyBooks")
router = APIRouter(prefix="pedidos", tags=["Pedidods"])

@router.get("/pedidos/{id}", response_model=PedidoRead)
async def obter_pedido_por_id(id: UUID):
    pedido = Pedido.objects(id=id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return pedido

@router.post("/", response_model=PedidoRead)
async def criar_pedido(pedido: PedidoCreate):
    try:
        logger.info(f"Criando pedido: {pedido}")
        
        novo_pedido = Pedido.create(**pedido.dict(exclude={"livro_ids"}))

        livro_ids = pedido.livro_ids
        for livro_id in livro_ids:
            livro = Livro.objects(id=livro_id).first()
            if not livro:
                raise HTTPException(status_code=404, detail=f"Livro com ID {livro_id} não encontrado")

        novo_pedido.update(livros_ids=livro_ids)

        return novo_pedido
    except Exception as e:
        logger.error(f"Erro ao criar pedido: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao criar pedido.")
    
@router.patch("/{pedido_id}", response_model=PedidoRead)
async def atualizar_pedido(pedido_id: UUID, pedido_update: PedidoUpdate):
    pedido = Pedido.objects(id=pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    update_data = pedido_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pedido, field, value)

    pedido.save()
    return pedido

@router.get("/", response_model=PaginatedPedido)
async def listar_pedidos(page: int = 1, limit: int = 10, usuario_id: Optional[UUID] = None):
    offset = (page - 1) * limit

    query = Pedido.objects().all()
    if usuario_id:
        query = query.filter(usuario_id=usuario_id)

    total = query.count()
    pedidos = query[offset:offset + limit]

    return PaginatedPedido(page=page, limit=limit, total=total, items=pedidos)

@router.get("/contar", response_model=ContagemPedidos)
async def contar_pedidos():
    total = Pedido.objects().count()
    return ContagemPedidos(quantidade=total)

@router.delete("/{pedido_id}", response_model=dict)
async def deletar_pedido(pedido_id: UUID):
    pedido = Pedido.objects(id=pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    pedido.delete()
    return {"message": "Pedido deletado com sucesso"}

@router.get("/filtrar", response_model=PaginatedPedido)
async def filtrar_pedidos(
    usuario_id: Optional[UUID] = None,
    status: Optional[str] = None,
    data_pedido: Optional[str] = None,
    valor_min: Optional[float] = None,
    valor_max: Optional[float] = None,
    page: int = 1,
    limit: int = 10
):
    query = Pedido.objects()
    if usuario_id:
        query = query.filter(usuario_id=usuario_id)
    if status:
        query = query.filter(status__icontains=status)

    if data_pedido:
        try:
            data_obj = datetime.strptime(data_pedido, "%Y-%m-%d").date()
            query = query.filter(data_pedido=data_obj)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato inválido de data (use AAAA-MM-DD)")

    pedidos = query.all()

    if valor_min is not None:
        pedidos = [p for p in pedidos if p.valor_total >= valor_min]
    if valor_max is not None:
        pedidos = [p for p in pedidos if p.valor_total <= valor_max]

    total = len(pedidos)
    offset = (page - 1) * limit
    pedidos_paginados = pedidos[offset:offset + limit]

    return PaginatedPedido(page=page, limit=limit, total=total, items=pedidos_paginados)


