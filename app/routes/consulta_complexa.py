from fastapi import APIRouter, HTTPException, Path, Query
from typing import List
from uuid import UUID
from cassandra.cqlengine.query import DoesNotExist
from app.models.models import Pedido, Livro, Usuario, PedidoPagamento, Pagamento, Autor, PedidoLivro, Editora
from app.schemas.schemas import PedidoDetalhado, LivroInfo, PagamentoInfo, EditoraComLivrosAutores
from app.logs.logger import get_logger

router = APIRouter(prefix="/consulta-usuario", tags=["Consultas Complexas"])
logger = get_logger("MyBooks")


@router.get("/pedidos-detalhados/{usuario_id}", response_model=dict)
def listar_pedidos_detalhados(
    usuario_id: UUID = Path(...),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1)
):
    usuario = Usuario.get(id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    pedidos = list(Pedido.objects(usuario_id=usuario_id))
    total = len(pedidos)

    # calcula offset para paginação
    offset = (page - 1) * limit
    pedidos_paginados = pedidos[offset:offset + limit]

    resultado = []

    for pedido in pedidos_paginados:
        rels_pedido_livro = PedidoLivro.objects(pedido_id=pedido.id)
        livros_info = []
        for rel in rels_pedido_livro:
            livro = Livro.get(id=rel.livro_id)
            autor = Autor.get(id=livro.autor_id)
            livros_info.append(LivroInfo(id=livro.id, titulo=livro.titulo, autor_nome=autor.nome))

        rels_pagamento = PedidoPagamento.objects(pedido_id=pedido.id)
        pagamentos_info = []
        for rel in rels_pagamento:
            pagamento = Pagamento.get(id=rel.pagamento_id)
            pagamentos_info.append(
                PagamentoInfo(
                    id=pagamento.id,
                    valor=pagamento.valor,
                    data_pagamento=str(pagamento.data_pagamento)
                )
            )

        resultado.append(
            PedidoDetalhado(
                id=pedido.id,
                data_pedido=str(pedido.data_pedido),
                livros=livros_info,
                pagamentos=pagamentos_info
            )
        )

    logger.info(f"Consultados {len(resultado)} pedidos detalhados do usuário {usuario_id} na página {page} com limite {limit}")

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "items": resultado
    }

@router.get("/editora-detalhado/{editora_id}", response_model=EditoraComLivrosAutores)
def obter_editora_com_livros_e_autores(
    editora_id: UUID = Path(..., description="ID da editora"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1)
):
    try:
        editora = Editora.objects(id=editora_id).get()
    except DoesNotExist:
        logger.warning(f"Editora não encontrada: {editora_id}")
        raise HTTPException(status_code=404, detail="Editora não encontrada")

    livros_completos = list(Livro.objects(editora_id=editora.id))
    total_livros = len(livros_completos)

    offset = (page - 1) * limit
    livros_paginados = livros_completos[offset:offset+limit]

    livros_com_autores = []
    for livro in livros_paginados:
        try:
            autor = Autor.objects(id=livro.autor_id).get()
            autor_info = {
                "id": autor.id,
                "nome": autor.nome,
            }
        except DoesNotExist:
            logger.warning(f"Autor não encontrado para livro {livro.id}")
            autor_info = None

        livro_info = {
            "id": livro.id,
            "titulo": livro.titulo,
            "autor": autor_info,
        }
        livros_com_autores.append(livro_info)

    resultado = {
        "id": editora.id,
        "nome": editora.nome,
        "endereco": editora.endereco,
        "telefone": editora.telefone,
        "email": editora.email,
        "livros": livros_com_autores,
        "page": page,
        "limit": limit,
        "total_livros": total_livros
    }

    return resultado
