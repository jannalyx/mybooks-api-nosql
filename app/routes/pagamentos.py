from uuid import UUID
from typing import Optional
from datetime import date, datetime
from cassandra.util import Date as CassandraDate
from cassandra.cqlengine.query import DoesNotExist
from fastapi import APIRouter, HTTPException, Query
from app.models.models import Pagamento, Pedido
from app.schemas.schemas import (
    PagamentoCreate,
    PagamentoUpdate,
    PagamentoRead,
    PaginatedPagamentos,
    PagamentoCount,
)
from app.logs.logger import get_logger

logger = get_logger("MyBooks")
router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])


def serialize(pagamento: Pagamento) -> dict:
    data = {field: getattr(pagamento, field) for field in Pagamento._columns.keys()}
    cass_data = data.get("data_pagamento")

    try:
        if isinstance(cass_data, (date, CassandraDate)):
            data["data_pagamento"] = date.fromisoformat(str(cass_data))
        else:
            logger.warning(f"data_pagamento inválido: {cass_data} ({type(cass_data)})!")
            raise ValueError("data_pagamento inválido!")
    except Exception as e:
        logger.warning(f"Erro ao converter data_pagamento: {e}!")
        raise

    return data


@router.get("/pagamentos/{id}", response_model=PagamentoRead)
def obter_pagamento_por_id(id: UUID):
    try:
        pagamento = Pagamento.objects(id=id).get()
        return PagamentoRead(**serialize(pagamento))
    except DoesNotExist:
        logger.warning(f"Pagamento não encontrado! ID {id}!")
        raise HTTPException(status_code=404, detail="Pagamento não encontrado!")


@router.post("/", response_model=PagamentoRead)
def criar_pagamento(pagamento: PagamentoCreate):
    try:
        Pedido.objects(id=pagamento.pedido_id).get()
    except DoesNotExist:
        logger.warning(f"Pedido não encontrado! ID {pagamento.pedido_id}!")
        raise HTTPException(status_code=400, detail="Pedido não encontrado!")

    pagamento_existente = Pagamento.objects(pedido_id=pagamento.pedido_id).allow_filtering().first()
    if pagamento_existente:
        logger.warning(f"Pagamento já existente para o pedido! ID {pagamento.pedido_id}!")
        raise HTTPException(status_code=400, detail="Já existe um pagamento para este pedido!")

    novo_pagamento = Pagamento.create(**pagamento.dict())
    logger.info(f"Pagamento criado: {novo_pagamento.id} - Pedido {novo_pagamento.pedido_id}!")
    return PagamentoRead(**serialize(novo_pagamento))


@router.patch("/", response_model=PagamentoRead)
def atualizar_pagamento(pagamento_id: UUID, pagamento_update: PagamentoUpdate):
    try:
        pagamento = Pagamento.objects(id=pagamento_id).get()
    except DoesNotExist:
        logger.warning(f"Tentativa de atualizar pagamento inexistente! ID {pagamento_id}!")
        raise HTTPException(status_code=404, detail="Pagamento não encontrado!")

    update_data = pagamento_update.dict(exclude_unset=True)

    if "pedido_id" in update_data:
        novo_pedido_id = update_data["pedido_id"]

        try:
            Pedido.objects(id=novo_pedido_id).get()
        except DoesNotExist:
            logger.warning(f"Pedido não encontrado! ID {novo_pedido_id}!")
            raise HTTPException(status_code=400, detail="Pedido não encontrado!")

        pagamentos_existentes = Pagamento.objects(pedido_id=novo_pedido_id).allow_filtering()
        for p in pagamentos_existentes:
            if p.id != pagamento_id:
                logger.warning(f"Já existe um pagamento para este pedido! ID {novo_pedido_id}!")
                raise HTTPException(status_code=400, detail="Já existe um pagamento para este pedido!")

    for key, value in update_data.items():
        setattr(pagamento, key, value)
    pagamento.update(**update_data)

    logger.info(f"Pagamento atualizado! ID {pagamento_id}!")
    return PagamentoRead(**serialize(pagamento))


@router.get("/", response_model=PaginatedPagamentos)
def listar_pagamentos(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    offset = (page - 1) * limit
    todos = list(Pagamento.objects().all())
    total = len(todos)
    pagamentos_paginados = todos[offset:offset + limit]

    logger.info(f"Listagem paginada de pagamentos! Página {page}, limite {limit}!")
    return PaginatedPagamentos(
        page=page,
        limit=limit,
        total=total,
        items=[PagamentoRead(**serialize(p)) for p in pagamentos_paginados]
    )


@router.get("/ordenado", response_model=PaginatedPagamentos)
def listar_pagamentos_ordenados(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    todos = list(Pagamento.objects().all())
    todos.sort(key=lambda p: str(p.data_pagamento))
    total = len(todos)
    offset = (page - 1) * limit
    pagamentos_paginados = todos[offset:offset + limit]

    logger.info(f"Listagem ordenada de pagamentos! Página {page}, limite {limit}!")
    return PaginatedPagamentos(
        page=page,
        limit=limit,
        total=total,
        items=[PagamentoRead(**serialize(p)) for p in pagamentos_paginados]
    )


@router.get("/count", response_model=PagamentoCount)
def contar_pagamentos():
    total = Pagamento.objects().count()
    logger.info(f"Contagem de pagamentos! {total}!")
    return PagamentoCount(total_pagamentos=total)


@router.delete("/", response_model=dict)
def deletar_pagamento(pagamento_id: UUID):
    try:
        pagamento = Pagamento.objects(id=pagamento_id).get()
        pagamento.delete()
        logger.info(f"Pagamento deletado! ID {pagamento_id}!")
        return {"message": "Pagamento deletado com sucesso!"}
    except DoesNotExist:
        logger.warning(f"Tentativa de deletar pagamento inexistente! ID {pagamento_id}!")
        raise HTTPException(status_code=404, detail="Pagamento não encontrado!")


@router.get("/filtrar", response_model=PaginatedPagamentos)
def filtrar_pagamentos(
    pedido_id: Optional[UUID] = Query(None),
    forma_pagamento: Optional[str] = Query(None),
    data_pagamento: Optional[str] = Query(None),
    valor_min: Optional[float] = Query(None),
    valor_max: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    pagamentos = list(Pagamento.objects().all())

    if pedido_id:
        pagamentos = [p for p in pagamentos if p.pedido_id == pedido_id]
    if forma_pagamento:
        pagamentos = [p for p in pagamentos if forma_pagamento.lower() in p.forma_pagamento.lower()]
    if data_pagamento:
        try:
            data_obj = datetime.strptime(data_pagamento, "%Y-%m-%d").date()
            pagamentos = [p for p in pagamentos if date.fromisoformat(str(p.data_pagamento)) == data_obj]
        except ValueError:
            logger.warning(f"Formato inválido para data_pagamento! {data_pagamento}!")
            raise HTTPException(status_code=400, detail="Formato de data inválido. Use AAAA-MM-DD!")
    if valor_min is not None:
        pagamentos = [p for p in pagamentos if p.valor >= valor_min]
    if valor_max is not None:
        pagamentos = [p for p in pagamentos if p.valor <= valor_max]

    total = len(pagamentos)
    if total == 0:
        raise HTTPException(status_code=404, detail="Nenhum pagamento encontrado com os filtros informados!")

    offset = (page - 1) * limit
    pagamentos_paginados = pagamentos[offset:offset + limit]

    logger.info(f"Filtro de pagamentos aplicado! Página {page}, limite {limit}, total encontrados: {total}!")
    return PaginatedPagamentos(
        page=page,
        limit=limit,
        total=total,
        items=[PagamentoRead(**serialize(p)) for p in pagamentos_paginados]
    )