from fastapi import APIRouter, HTTPException, Query, Path
from typing import List
from uuid import UUID
from cassandra.cqlengine.query import DoesNotExist
from app.models.models import PedidoPagamento
from app.schemas.schemas import PedidoPagamentoCreate, PedidoPagamentoRead, PaginatedPedidoPagamento
from app.logs.logger import get_logger

logger = get_logger("MyBooks")
router = APIRouter(prefix="/pedido-pagamento", tags=["PedidoPagamento"])

def serialize(rel: PedidoPagamento) -> dict:
    return {
        "pedido_id": rel.pedido_id,
        "pagamento_id": rel.pagamento_id,
    }

@router.post("/vincular", response_model=PedidoPagamentoRead, status_code=201)
def vincular_pagamento_pedido(rel: PedidoPagamentoCreate):
    existe = PedidoPagamento.objects(pedido_id=rel.pedido_id, pagamento_id=rel.pagamento_id).count() > 0
    if existe:
        logger.warning(f"Tentativa de vincular relação existente: Pedido {rel.pedido_id} - Pagamento {rel.pagamento_id}")
        raise HTTPException(status_code=400, detail="Relação já existe.")

    nova_rel = PedidoPagamento(pedido_id=rel.pedido_id, pagamento_id=rel.pagamento_id)
    nova_rel.save()
    logger.info(f"Pagamento vinculado ao pedido: Pedido {rel.pedido_id} - Pagamento {rel.pagamento_id}")
    return PedidoPagamentoRead(**serialize(nova_rel))

@router.get("/pagamentos/{pedido_id}", response_model=PaginatedPedidoPagamento)
def listar_pagamentos_de_pedido(
    pedido_id: UUID = Path(..., description="ID do Pedido"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    todos = list(PedidoPagamento.objects(pedido_id=pedido_id))
    total = len(todos)
    if total == 0:
        logger.warning(f"Nenhum pagamento vinculado ao pedido {pedido_id}")
        raise HTTPException(status_code=404, detail="Nenhum pagamento vinculado a esse pedido.")

    offset = (page - 1) * limit
    pagamentos_paginados = todos[offset:offset + limit]

    logger.info(f"Listagem paginada de pagamentos vinculados ao pedido {pedido_id}. Página {page}, limite {limit}.")
    items = [PedidoPagamentoRead(**serialize(p)) for p in pagamentos_paginados]

    return PaginatedPedidoPagamento(
        page=page,
        limit=limit,
        total=total,
        items=items,
    )

@router.delete("/desvincular", status_code=204)
def desvincular_pagamento_pedido(
    pedido_id: UUID = Query(..., description="ID do Pedido"),
    pagamento_id: UUID = Query(..., description="ID do Pagamento"),
):
    try:
        rel = PedidoPagamento.objects(pedido_id=pedido_id, pagamento_id=pagamento_id).get()
        rel.delete()
        logger.info(f"Relação Pedido {pedido_id} - Pagamento {pagamento_id} desvinculada com sucesso")
    except DoesNotExist:
        logger.warning(f"Tentativa de desvincular relação inexistente: Pedido {pedido_id} - Pagamento {pagamento_id}")
        raise HTTPException(status_code=404, detail="Relação não encontrada.")
