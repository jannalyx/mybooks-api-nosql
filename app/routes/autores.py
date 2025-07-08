from uuid import UUID
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from cassandra.cqlengine.query import DoesNotExist
from cassandra.util import Date as CassandraDate
from app.models.models import Autor
from app.schemas.schemas import AutorCreate, AutorUpdate, AutorRead, AutorCount, PaginatedAutor
from app.logs.logger import get_logger

logger = get_logger("MyBooks")
router = APIRouter(prefix="/autores", tags=["Autores"])


def serialize(autor: Autor) -> dict:
    data = {field: getattr(autor, field) for field in Autor._columns.keys()}
    cass_date = data.get("data_nascimento")

    try:
        if isinstance(cass_date, (date, CassandraDate)):
            data["data_nascimento"] = date.fromisoformat(str(cass_date))
        else:
            logger.warning(f"data_nascimento inválido: {cass_date} ({type(cass_date)})!")
            raise ValueError("data_nascimento inválido!")
    except Exception as e:
        logger.warning(f"Erro ao converter data_nascimento: {e}!")
        raise

    return data


@router.get("/autores/{id}", response_model=AutorRead)
def obter_autor_por_id(id: UUID):
    try:
        autor = Autor.objects(id=id).get()
        return AutorRead(**serialize(autor))
    except DoesNotExist:
        logger.warning(f"Autor não encontrado! ID {id}!")
        raise HTTPException(status_code=404, detail="Autor não encontrado!")


@router.post("/", response_model=AutorRead)
def criar_autor(autor: AutorCreate):
    if Autor.objects(nome=autor.nome).allow_filtering().count() > 0:
        logger.warning(f"Nome já em uso! {autor.nome}!")
        raise HTTPException(status_code=400, detail="Já existe um autor com esse nome!")

    if Autor.objects(email=autor.email).allow_filtering().count() > 0:
        logger.warning(f"E-mail já em uso! {autor.email}!")
        raise HTTPException(status_code=400, detail="Já existe um autor com esse e-mail!")

    novo_autor = Autor.create(**autor.dict())
    logger.info(f"Autor criado: {novo_autor.id} - {novo_autor.nome} ({novo_autor.email})!")
    return AutorRead(**serialize(novo_autor))


@router.patch("/{autor_id}", response_model=AutorRead)
def atualizar_autor(autor_id: UUID, autor_update: AutorUpdate):
    try:
        autor = Autor.objects(id=autor_id).get()
    except DoesNotExist:
        logger.warning(f"Tentativa de atualizar autor inexistente! ID {autor_id}!")
        raise HTTPException(status_code=404, detail="Autor não encontrado!")

    update_data = autor_update.dict(exclude_unset=True)

    if "nome" in update_data:
        nome_existente = Autor.objects(nome=update_data["nome"]).allow_filtering()
        for a in nome_existente:
            if a.id != autor_id:
                logger.warning(f"Nome já em uso por outro autor! {update_data['nome']}!")
                raise HTTPException(status_code=400, detail="Já existe um autor com esse nome!")

    if "email" in update_data:
        email_existente = Autor.objects(email=update_data["email"]).allow_filtering()
        for a in email_existente:
            if a.id != autor_id:
                logger.warning(f"E-mail já em uso por outro autor! {update_data['email']}!")
                raise HTTPException(status_code=400, detail="Já existe um autor com esse e-mail!")

    for key, value in update_data.items():
        setattr(autor, key, value)
    autor.update(**update_data)

    logger.info(f"Autor atualizado! {autor_id}!")
    return AutorRead(**serialize(autor))


@router.get("/", response_model=PaginatedAutor)
def listar_autores(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    offset = (page - 1) * limit
    todos = list(Autor.objects().all())
    total = len(todos)
    autores_paginados = todos[offset:offset + limit]

    logger.info(f"Listagem paginada de autores! Página {page}, limite {limit}!")
    return PaginatedAutor(
        page=page,
        limit=limit,
        total=total,
        items=[AutorRead(**serialize(a)) for a in autores_paginados]
    )


@router.get("/count", response_model=AutorCount)
def contar_autores():
    total = Autor.objects().count()
    logger.info(f"Contagem de autores! {total}!")
    return AutorCount(total_autores=total)


@router.delete("/", response_model=dict)
def deletar_autor(autor_id: UUID):
    try:
        autor = Autor.objects(id=autor_id).get()
        autor.delete()
        logger.info(f"Autor deletado! ID {autor_id}!")
        return {"message": "Autor deletado com sucesso!"}
    except DoesNotExist:
        logger.warning(f"Tentativa de deletar autor inexistente! ID {autor_id}!")
        raise HTTPException(status_code=404, detail="Autor não encontrado!")


@router.get("/filtrar", response_model=PaginatedAutor)
def filtrar_autores(
    nome: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    data_nascimento: Optional[str] = Query(None),
    nacionalidade: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    todos = Autor.objects().all()
    if nome:
        todos = [a for a in todos if nome.lower() in a.nome.lower()]
    if email:
        todos = [a for a in todos if email.lower() in a.email.lower()]
    if nacionalidade:
        todos = [a for a in todos if nacionalidade.lower() in a.nacionalidade.lower()]

    if data_nascimento:
        try:
            data_obj = datetime.strptime(data_nascimento, "%d-%m-%Y").date()
            todos = [
                a for a in todos
                if date.fromisoformat(str(a.data_nascimento)) == data_obj
            ]
        except ValueError:
            logger.warning(f"Formato inválido para data_nascimento! {data_nascimento}!")
            raise HTTPException(status_code=400, detail="Formato de data inválido. Use DD-MM-AAAA!")

    total = len(todos)
    if total == 0:
        raise HTTPException(status_code=404, detail="Nenhum autor encontrado com os filtros informados!")

    offset = (page - 1) * limit
    autores_paginados = todos[offset:offset + limit]

    logger.info(f"Filtro aplicado! Total encontrados: {total}!")
    return PaginatedAutor(
        page=page,
        limit=limit,
        total=total,
        items=[AutorRead(**serialize(a)) for a in autores_paginados]
    )


@router.get("/ordenado", response_model=PaginatedAutor)
def listar_autores_ordenados(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    todos = list(Autor.objects().all())
    todos.sort(key=lambda a: a.nome.lower())
    total = len(todos)
    offset = (page - 1) * limit
    autores_paginados = todos[offset:offset + limit]

    logger.info(f"Listagem ordenada de autores! Página {page}, limite {limit}!")
    return PaginatedAutor(
        page=page,
        limit=limit,
        total=total,
        items=[AutorRead(**serialize(a)) for a in autores_paginados]
    )