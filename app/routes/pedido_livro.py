from fastapi import APIRouter, HTTPException, Query, Path
from typing import List
from uuid import UUID
from cassandra.cqlengine.query import DoesNotExist
from app.models.models import PedidoLivro, Livro, Autor
from app.schemas.schemas import PedidoLivroCreate, PedidoLivroRead, PaginatedPedidoLivro, LivroInfo
from app.logs.logger import get_logger

logger = get_logger("MyBooks")
router = APIRouter(prefix="/pedido-livro", tags=["PedidoLivro"])


def serialize_pedido_livro(rel: PedidoLivro) -> dict:
    return {
        "pedido_id": rel.pedido_id,
        "livro_id": rel.livro_id,
    }


@router.post("/vincular", response_model=PedidoLivroRead, status_code=201)
def vincular_livro_pedido(rel: PedidoLivroCreate):
    existe = PedidoLivro.objects(pedido_id=rel.pedido_id, livro_id=rel.livro_id).count() > 0
    if existe:
        logger.warning(f"Tentativa de vincular relação existente: Pedido {rel.pedido_id} - Livro {rel.livro_id}")
        raise HTTPException(status_code=400, detail="Relação já existe.")

    nova_rel = PedidoLivro(pedido_id=rel.pedido_id, livro_id=rel.livro_id)
    nova_rel.save()
    logger.info(f"Livro vinculado ao pedido: Pedido {rel.pedido_id} - Livro {rel.livro_id}")
    return PedidoLivroRead(**serialize_pedido_livro(nova_rel))


@router.get("/livros/{pedido_id}", response_model=PaginatedPedidoLivro)
def listar_livros_de_pedido(
    pedido_id: UUID = Path(..., description="ID do Pedido"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    todos = list(PedidoLivro.objects(pedido_id=pedido_id))
    total = len(todos)
    if total == 0:
        logger.warning(f"Nenhum livro vinculado ao pedido {pedido_id}")
        raise HTTPException(status_code=404, detail="Nenhum livro vinculado a esse pedido.")

    offset = (page - 1) * limit
    rels_paginados = todos[offset:offset + limit]

    items = []
    for rel in rels_paginados:
        try:
            livro = Livro.objects(id=rel.livro_id).get()
            autor = Autor.objects(id=livro.autor_id).get()
            livro_info = LivroInfo(
                id=livro.id,
                titulo=livro.titulo,
                autor_nome=autor.nome
            )
           
            items.append(livro_info.dict())
        except DoesNotExist:
            logger.warning(f"Livro ou Autor não encontrado para livro_id {rel.livro_id}")

    logger.info(f"Listagem paginada de livros vinculados ao pedido {pedido_id}. Página {page}, limite {limit}.")
    return PaginatedPedidoLivro(
        page=page,
        limit=limit,
        total=total,
        items=items,
    )


@router.delete("/desvincular", status_code=204)
def desvincular_livro_pedido(
    pedido_id: UUID = Query(..., description="ID do Pedido"),
    livro_id: UUID = Query(..., description="ID do Livro"),
):
    try:
        rel = PedidoLivro.objects(pedido_id=pedido_id, livro_id=livro_id).get()
        rel.delete()
        logger.info(f"Relação Pedido {pedido_id} - Livro {livro_id} desvinculada com sucesso")
    except DoesNotExist:
        logger.warning(f"Tentativa de desvincular relação inexistente: Pedido {pedido_id} - Livro {livro_id}")
        raise HTTPException(status_code=404, detail="Relação não encontrada.")
