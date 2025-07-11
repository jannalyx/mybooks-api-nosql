from uuid import UUID
from typing import Optional
from datetime import date
from cassandra.util import Date as CassandraDate
from fastapi import APIRouter, HTTPException, Query
from cassandra.cqlengine.query import DoesNotExist
from app.models.models import Livro, Autor, Editora
from app.schemas.schemas import LivroCreate, LivroUpdate, LivroRead, LivroCount, PaginatedLivros
from app.logs.logger import get_logger

logger = get_logger("MyBooks")
router = APIRouter(prefix="/livros", tags=["Livros"])


def serialize(livro: Livro) -> dict:
    data = {field: getattr(livro, field) for field in Livro._columns.keys()}
    cass_date = data.get("data_publicacao")

    try:
        if isinstance(cass_date, (date, CassandraDate)):
            data["data_publicacao"] = date.fromisoformat(str(cass_date))
        else:
            logger.warning(f"data_publicacao inválido: {cass_date} ({type(cass_date)})!")
            raise ValueError("data_publicacao inválido!")
    except Exception as e:
        logger.warning(f"Erro ao converter data_publicacao: {e}!")
        raise

    return data


@router.get("/livros/{id}", response_model=LivroRead)
def obter_livro_por_id(id: UUID):
    try:
        livro = Livro.objects(id=id).get()
        return LivroRead(**serialize(livro))
    except DoesNotExist:
        logger.warning(f"Livro não encontrado! ID {id}!")
        raise HTTPException(status_code=404, detail="Livro não encontrado!")


@router.post("/", response_model=LivroRead)
def criar_livro(livro: LivroCreate):
    try:
        Autor.objects(id=livro.autor_id).get()
    except DoesNotExist:
        logger.warning(f"Autor não encontrado! ID {livro.autor_id}!")
        raise HTTPException(status_code=400, detail="Autor não encontrado!")

    try:
        Editora.objects(id=livro.editora_id).get()
    except DoesNotExist:
        logger.warning(f"Editora não encontrada! ID {livro.editora_id}!")
        raise HTTPException(status_code=400, detail="Editora não encontrada!")

    novo_livro = Livro.create(**livro.dict())
    logger.info(f"Livro criado: {novo_livro.id} - {novo_livro.titulo}!")
    return LivroRead(**serialize(novo_livro))


@router.patch("/", response_model=LivroRead)
def atualizar_livro(livro_id: UUID, livro_update: LivroUpdate):
    try:
        livro = Livro.objects(id=livro_id).get()
    except DoesNotExist:
        logger.warning(f"Tentativa de atualizar livro inexistente! ID {livro_id}!")
        raise HTTPException(status_code=404, detail="Livro não encontrado!")

    update_data = livro_update.dict(exclude_unset=True)

    if "titulo" in update_data:
        titulo_existente = Livro.objects(titulo=update_data["titulo"]).allow_filtering()
        for l in titulo_existente:
            if l.id != livro_id:
                logger.warning(f"Título já em uso por outro livro! {update_data['titulo']}!")
                raise HTTPException(status_code=400, detail="Já existe um livro com esse título!")

    if "autor_id" in update_data:
        try:
            Autor.objects(id=update_data["autor_id"]).get()
        except DoesNotExist:
            logger.warning(f"Autor não encontrado! ID {update_data['autor_id']}!")
            raise HTTPException(status_code=400, detail="Autor não encontrado!")

    if "editora_id" in update_data:
        try:
            Editora.objects(id=update_data["editora_id"]).get()
        except DoesNotExist:
            logger.warning(f"Editora não encontrada! ID {update_data['editora_id']}!")
            raise HTTPException(status_code=400, detail="Editora não encontrada!")

    for key, value in update_data.items():
        setattr(livro, key, value)
    livro.update(**update_data)

    logger.info(f"Livro atualizado! ID {livro_id}!")
    return LivroRead(**serialize(livro))


@router.get("/", response_model=PaginatedLivros)
def listar_livros(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    offset = (page - 1) * limit
    todos = list(Livro.objects().all())
    total = len(todos)
    livros_paginados = todos[offset:offset + limit]

    logger.info(f"Listagem paginada de livros! Página {page}, limite {limit}!")
    return PaginatedLivros(
        page=page,
        limit=limit,
        total=total,
        items=[LivroRead(**serialize(l)) for l in livros_paginados]
    )


@router.get("/count", response_model=LivroCount)
def contar_livros():
    total = Livro.objects().count()
    logger.info(f"Contagem de livros! {total}!")
    return LivroCount(total_livros=total)


@router.delete("/", response_model=dict)
def deletar_livro(livro_id: UUID):
    try:
        livro = Livro.objects(id=livro_id).get()
        livro.delete()
        logger.info(f"Livro deletado! ID {livro_id}!")
        return {"message": "Livro deletado com sucesso!"}
    except DoesNotExist:
        logger.warning(f"Tentativa de deletar livro inexistente! ID {livro_id}!")
        raise HTTPException(status_code=404, detail="Livro não encontrado!")


@router.get("/filtro", response_model=PaginatedLivros)
def filtrar_livros(
    titulo: Optional[str] = Query(None),
    genero: Optional[str] = Query(None),
    preco_min: Optional[float] = Query(None),
    preco_max: Optional[float] = Query(None),
    autor_id: Optional[UUID] = Query(None),
    editora_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    livros = Livro.objects().all()

    if titulo:
        livros = [l for l in livros if titulo.lower() in l.titulo.lower()]
    if genero:
        livros = [l for l in livros if genero.lower() in l.genero.lower()]
    if preco_min is not None:
        livros = [l for l in livros if l.preco >= preco_min]
    if preco_max is not None:
        livros = [l for l in livros if l.preco <= preco_max]
    if autor_id:
        livros = [l for l in livros if l.autor_id == autor_id]
    if editora_id:
        livros = [l for l in livros if l.editora_id == editora_id]

    total = len(livros)
    if total == 0:
        raise HTTPException(status_code=404, detail="Nenhum livro encontrado com os filtros informados!")

    offset = (page - 1) * limit
    livros_paginados = livros[offset:offset + limit]

    logger.info(f"Filtro de livros aplicado! Página {page}, limite {limit}, total encontrados: {total}!")
    return PaginatedLivros(
        page=page,
        limit=limit,
        total=total,
        items=[LivroRead(**serialize(l)) for l in livros_paginados]
    )


@router.get("/ordenado", response_model=PaginatedLivros)
def listar_livros_ordenados(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    todos = list(Livro.objects().all())
    todos.sort(key=lambda l: l.titulo.lower())
    total = len(todos)
    offset = (page - 1) * limit
    livros_paginados = todos[offset:offset + limit]

    logger.info(f"Listagem ordenada de livros! Página {page}, limite {limit}!")
    return PaginatedLivros(
        page=page,
        limit=limit,
        total=total,
        items=[LivroRead(**serialize(l)) for l in livros_paginados]
    )