from uuid import UUID
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from app.models.models import Pagamento
from app.schemas.schemas import (
    PagamentoCreate, PagamentoUpdate,
    PaginatedPagamentos, PagamentoCount
)
from logs.logger import get_logger

logger = get_logger("MyBooks")
router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])

@router.get("/{id}", response_model=Pagamento)
async def obter_pagamento_por_id(id: UUID):
    pagamento = Pagamento.objects(id=id).first()
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return pagamento

@router.post("/", response_model=Pagamento)
async def criar_pagamento(pagamento: PagamentoCreate):
    try:
        novo_pagamento = Pagamento.create(**pagamento.dict())
        logger.info(f"Pagamento criado: {novo_pagamento.id} - Pedido {novo_pagamento.pedido_id}")
        return novo_pagamento
    except Exception as e:
        logger.error("Erro ao criar pagamento", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao criar pagamento")

@router.patch("/{pagamento_id}", response_model=Pagamento)
async def atualizar_pagamento(pagamento_id: UUID, pagamento_update: PagamentoUpdate):
    pagamento = Pagamento.objects(id=pagamento_id).first()
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    update_data = pagamento_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pagamento, key, value)

    pagamento.save()
    logger.info(f"Pagamento atualizado: {pagamento.id}")
    return pagamento

@router.get("/", response_model=PaginatedPagamentos)
async def listar_pagamentos(
    pedido_id: Optional[UUID] = None,
    page: int = 1,
    limit: int = 10
):
    offset = (page - 1) * limit

    query = Pagamento.objects()
    if pedido_id:
        query = query.filter(pedido_id=pedido_id)

    total = query.count()
    pagamentos = query[offset:offset + limit]

    return PaginatedPagamentos(page=page, limit=limit, total=total, items=pagamentos)

@router.get("/contar", response_model=PagamentoCount)
async def contar_pagamentos():
    total = Pagamento.objects().count()
    return PagamentoCount(total_pagamentos=total)

@router.delete("/{pagamento_id}", response_model=dict)
async def deletar_pagamento(pagamento_id: UUID):
    pagamento = Pagamento.objects(id=pagamento_id).first()
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    pagamento.delete()
    logger.info(f"Pagamento deletado: ID {pagamento_id}")
    return {"message": "Pagamento deletado com sucesso"}

@router.get("/filtrar", response_model=PaginatedPagamentos)
async def filtrar_pagamentos(
    pedido_id: Optional[UUID] = None,
    data_pagamento: Optional[str] = None,
    valor_min: Optional[float] = None,
    valor_max: Optional[float] = None,
    forma_pagamento: Optional[str] = None,
    page: int = 1,
    limit: int = 10
):
    query = Pagamento.objects()
    filtros_aplicados = []

    if pedido_id:
        query = query.filter(pedido_id=pedido_id)
        filtros_aplicados.append(f"pedido_id={pedido_id}")
    if forma_pagamento:
        query = query.filter(forma_pagamento__icontains=forma_pagamento)
        filtros_aplicados.append(f"forma_pagamento={forma_pagamento}")

    pagamentos = query.all()

    if data_pagamento:
        try:
            data_obj = datetime.strptime(data_pagamento, "%Y-%m-%d").date()
            pagamentos = [p for p in pagamentos if p.data_pagamento == data_obj]
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato inválido de data (use AAAA-MM-DD)")

    if valor_min is not None:
        pagamentos = [p for p in pagamentos if p.valor >= valor_min]
    if valor_max is not None:
        pagamentos = [p for p in pagamentos if p.valor <= valor_max]

    total = len(pagamentos)
    offset = (page - 1) * limit
    pagamentos_paginados = pagamentos[offset:offset + limit]

    return PaginatedPagamentos(page=page, limit=limit, total=total, items=pagamentos_paginados)