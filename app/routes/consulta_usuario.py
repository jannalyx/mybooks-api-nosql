from fastapi import APIRouter, HTTPException, Path
from uuid import UUID
from app.models.models import Pedido, Livro, Usuario, PedidoPagamento, Pagamento, Autor, PedidoLivro
from app.schemas.schemas import PedidoDetalhado, LivroInfo, PagamentoInfo
from app.logs.logger import get_logger

router = APIRouter(prefix="/consulta-usuario", tags=["Consultas Complexas"])
logger = get_logger("MyBooks")

@router.get("/pedidos-detalhados/{usuario_id}", response_model=list[PedidoDetalhado])
def listar_pedidos_detalhados(usuario_id: UUID = Path(...)):
    usuario = Usuario.get(id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    pedidos = Pedido.objects(usuario_id=usuario_id)
    resultado = []

    for pedido in pedidos:
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

    logger.info(f"Consultados {len(resultado)} pedidos detalhados do usuário {usuario_id}")
    return resultado
