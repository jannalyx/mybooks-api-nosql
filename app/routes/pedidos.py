from uuid import UUID
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from cassandra.cqlengine.query import DoesNotExist
from cassandra.util import Date as CassandraDate
from datetime import date, datetime
from app.models.models import Pedido, Usuario
from app.schemas.schemas import (
    PedidoCreate,
    PedidoUpdate,
    PedidoRead,
    PaginatedPedido,
    ContagemPedidos,
)
from app.logs.logger import get_logger

logger = get_logger("MyBooks")
router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


def serialize(pedido: Pedido) -> dict:
    data = {field: getattr(pedido, field) for field in Pedido._columns.keys()}
    cass_data = data.get("data_pedido")

    try:
        if isinstance(cass_data, (date, CassandraDate)):
            data["data_pedido"] = date.fromisoformat(str(cass_data))
        else:
            logger.warning(f"data_pedido inválido: {cass_data} ({type(cass_data)})!")
            raise ValueError("data_pedido inválido!")
    except Exception as e:
        logger.warning(f"Erro ao converter data_pedido: {e}!")
        raise

    return data


@router.get("/pedidos/{id}", response_model=PedidoRead)
def obter_pedido_por_id(id: UUID):
    try:
        pedido = Pedido.objects(id=id).get()
        return PedidoRead(**serialize(pedido))
    except DoesNotExist:
        logger.warning(f"Pedido não encontrado! ID {id}!")
        raise HTTPException(status_code=404, detail="Pedido não encontrado!")


@router.post("/", response_model=PedidoRead)
def criar_pedido(pedido: PedidoCreate):
    try:
        Usuario.objects(id=pedido.usuario_id).get()
    except DoesNotExist:
        logger.warning(f"Usuário não encontrado! ID {pedido.usuario_id}!")
        raise HTTPException(status_code=400, detail="Usuário não encontrado!")

    novo_pedido = Pedido.create(**pedido.dict())
    logger.info(f"Pedido criado: {novo_pedido.id} (Usuário {novo_pedido.usuario_id})!")
    return PedidoRead(**serialize(novo_pedido))


@router.patch("/", response_model=PedidoRead)
def atualizar_pedido(pedido_id: UUID, pedido_update: PedidoUpdate):
    try:
        pedido = Pedido.objects(id=pedido_id).get()
    except DoesNotExist:
        logger.warning(f"Tentativa de atualizar pedido inexistente! ID {pedido_id}!")
        raise HTTPException(status_code=404, detail="Pedido não encontrado!")

    update_data = pedido_update.dict(exclude_unset=True)

    if "usuario_id" in update_data:
        try:
            Usuario.objects(id=update_data["usuario_id"]).get()
        except DoesNotExist:
            logger.warning(f"Usuário não encontrado! ID {update_data['usuario_id']}!")
            raise HTTPException(status_code=400, detail="Usuário não encontrado!")

    for key, value in update_data.items():
        setattr(pedido, key, value)
    pedido.update(**update_data)

    logger.info(f"Pedido atualizado! ID {pedido_id}!")
    return PedidoRead(**serialize(pedido))


@router.get("/", response_model=PaginatedPedido)
def listar_pedidos(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    offset = (page - 1) * limit
    todos = list(Pedido.objects().all())
    total = len(todos)
    pedidos_paginados = todos[offset:offset + limit]

    logger.info(f"Listagem paginada de pedidos! Página {page}, limite {limit}!")
    return PaginatedPedido(
        page=page,
        limit=limit,
        total=total,
        items=[PedidoRead(**serialize(p)) for p in pedidos_paginados]
    )


@router.get("/ordenado", response_model=PaginatedPedido)
def listar_pedidos_ordenados(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    todos = list(Pedido.objects().all())
    todos.sort(key=lambda p: str(p.data_pedido))
    total = len(todos)
    offset = (page - 1) * limit
    pedidos_paginados = todos[offset:offset + limit]

    logger.info(f"Listagem ordenada de pedidos! Página {page}, limite {limit}!")
    return PaginatedPedido(
        page=page,
        limit=limit,
        total=total,
        items=[PedidoRead(**serialize(p)) for p in pedidos_paginados]
    )


@router.get("/count", response_model=ContagemPedidos)
def contar_pedidos():
    total = Pedido.objects().count()
    logger.info(f"Contagem de pedidos! {total}!")
    return ContagemPedidos(quantidade=total)


@router.delete("/", response_model=dict)
def deletar_pedido(pedido_id: UUID):
    try:
        pedido = Pedido.objects(id=pedido_id).get()
        pedido.delete()
        logger.info(f"Pedido deletado! ID {pedido_id}!")
        return {"message": "Pedido deletado com sucesso!"}
    except DoesNotExist:
        logger.warning(f"Tentativa de deletar pedido inexistente! ID {pedido_id}!")
        raise HTTPException(status_code=404, detail="Pedido não encontrado!")


@router.get("/filtrar", response_model=PaginatedPedido)
def filtrar_pedidos(
    usuario_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    data_pedido: Optional[str] = Query(None),
    valor_min: Optional[float] = Query(None),
    valor_max: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    pedidos = list(Pedido.objects().all())

    if usuario_id:
        pedidos = [p for p in pedidos if p.usuario_id == usuario_id]
    if status:
        pedidos = [p for p in pedidos if status.lower() in p.status.lower()]
    if data_pedido:
        try:
            data_obj = datetime.strptime(data_pedido, "%Y-%m-%d").date()
            pedidos = [p for p in pedidos if date.fromisoformat(str(p.data_pedido)) == data_obj]
        except ValueError:
            logger.warning(f"Formato inválido para data_pedido! {data_pedido}!")
            raise HTTPException(status_code=400, detail="Formato de data inválido. Use AAAA-MM-DD!")
    if valor_min is not None:
        pedidos = [p for p in pedidos if p.valor_total >= valor_min]
    if valor_max is not None:
        pedidos = [p for p in pedidos if p.valor_total <= valor_max]

    total = len(pedidos)
    if total == 0:
        raise HTTPException(status_code=404, detail="Nenhum pedido encontrado com os filtros informados!")

    offset = (page - 1) * limit
    pedidos_paginados = pedidos[offset:offset + limit]

    logger.info(f"Filtro de pedidos aplicado! Página {page}, limite {limit}, total encontrados: {total}!")
    return PaginatedPedido(
        page=page,
        limit=limit,
        total=total,
        items=[PedidoRead(**serialize(p)) for p in pedidos_paginados]
    )