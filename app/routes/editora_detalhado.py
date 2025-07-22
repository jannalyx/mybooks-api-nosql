from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.models.models import Editora, Livro, Autor
from app.schemas.schemas import EditoraComLivrosAutores
from app.logs.logger import get_logger
from cassandra.cqlengine.query import DoesNotExist

logger = get_logger("MyBooks")
router = APIRouter(prefix="/editoras", tags=["Editoras"])

@router.get("/com-livros-e-autores", response_model=List[EditoraComLivrosAutores])
def listar_editoras_com_livros_e_autores(
    limit: int = Query(10, ge=1),
    page: int = Query(1, ge=1)
):
    offset = (page - 1) * limit
    editoras = list(Editora.objects().limit(limit).offset(offset))  
    total_editoras = len(list(Editora.objects()))

    if not editoras:
        logger.warning("Nenhuma editora encontrada.")
        raise HTTPException(status_code=404, detail="Nenhuma editora encontrada.")

    resultado = []

    for editora in editoras:
        livros_obj = list(Livro.objects(editora_id=editora.id))
        livros_com_autores = []

        for livro in livros_obj:
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

        resultado.append({
            "id": editora.id,
            "nome": editora.nome,
            "endereco": editora.endereco,
            "telefone": editora.telefone,
            "email": editora.email,
            "livros": livros_com_autores,
        })

    return resultado
