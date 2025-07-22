from fastapi import APIRouter, HTTPException, Query, Path
from typing import List
from uuid import UUID
from cassandra.cqlengine.query import DoesNotExist
from app.models.models import PedidoPagamento
from app.schemas.schemas import PedidoPagamentoCreate, PedidoPagamentoRead
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

@router.get("/pagamentos/{pedido_id}", response_model=List[PedidoPagamentoRead])
def listar_pagamentos_de_pedido(pedido_id: UUID = Path(..., description="ID do Pedido")):
    rels = PedidoPagamento.objects(pedido_id=pedido_id)
    if rels.count() == 0:
        logger.warning(f"Nenhum pagamento vinculado ao pedido {pedido_id}")
        raise HTTPException(status_code=404, detail="Nenhum pagamento vinculado a esse pedido.")
    pagamentos = [PedidoPagamentoRead(**serialize(rel)) for rel in rels]
    logger.info(f"Listados {len(pagamentos)} pagamentos vinculados ao pedido {pedido_id}")
    return pagamentos

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
