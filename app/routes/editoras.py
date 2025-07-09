from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from cassandra.cqlengine.query import DoesNotExist
from app.models.models import Editora
from app.schemas.schemas import (
    EditoraCreate,
    EditoraUpdate,
    EditoraRead,
    EditoraCount,
    PaginatedEditoras
)
from logs.logger import get_logger

logger = get_logger("MyBooks")
router = APIRouter(prefix="/editoras", tags=["Editoras"])


def serialize(editora: Editora) -> dict:
    return {field: getattr(editora, field) for field in Editora._columns.keys()}


@router.get("/editoras/{id}", response_model=EditoraRead)
def obter_editora_por_id(id: UUID):
    try:
        editora = Editora.objects(id=id).get()
        return EditoraRead(**serialize(editora))
    except DoesNotExist:
        logger.warning(f"Editora não encontrada! ID {id}!")
        raise HTTPException(status_code=404, detail="Editora não encontrada!")


@router.post("/", response_model=EditoraRead)
def criar_editora(editora: EditoraCreate):
    if Editora.objects(nome=editora.nome).allow_filtering().count() > 0:
        logger.warning(f"Nome já em uso! {editora.nome}!")
        raise HTTPException(status_code=400, detail="Já existe uma editora com esse nome!")

    if Editora.objects(email=editora.email).allow_filtering().count() > 0:
        logger.warning(f"E-mail já em uso! {editora.email}!")
        raise HTTPException(status_code=400, detail="Já existe uma editora com esse e-mail!")

    nova_editora = Editora.create(**editora.dict())
    logger.info(f"Editora criada: {nova_editora.id} - {nova_editora.nome}!")
    return EditoraRead(**serialize(nova_editora))


@router.patch("/", response_model=EditoraRead)
def atualizar_editora(editora_id: UUID, editora_update: EditoraUpdate):
    try:
        editora = Editora.objects(id=editora_id).get()
    except DoesNotExist:
        logger.warning(f"Tentativa de atualizar editora inexistente! ID {editora_id}!")
        raise HTTPException(status_code=404, detail="Editora não encontrada!")

    update_data = editora_update.dict(exclude_unset=True)

    if "nome" in update_data:
        nome_existente = Editora.objects(nome=update_data["nome"]).allow_filtering()
        for e in nome_existente:
            if e.id != editora_id:
                logger.warning(f"Nome já em uso por outra editora! {update_data['nome']}!")
                raise HTTPException(status_code=400, detail="Já existe uma editora com esse nome!")

    if "email" in update_data:
        email_existente = Editora.objects(email=update_data["email"]).allow_filtering()
        for e in email_existente:
            if e.id != editora_id:
                logger.warning(f"E-mail já em uso por outra editora! {update_data['email']}!")
                raise HTTPException(status_code=400, detail="Já existe uma editora com esse e-mail!")

    for key, value in update_data.items():
        setattr(editora, key, value)
    editora.update(**update_data)

    logger.info(f"Editora atualizada! ID {editora_id}!")
    return EditoraRead(**serialize(editora))


@router.get("/", response_model=PaginatedEditoras)
def listar_editoras(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    offset = (page - 1) * limit
    todas = list(Editora.objects().all())
    total = len(todas)
    editoras_paginadas = todas[offset:offset + limit]

    logger.info(f"Listagem paginada de editoras! Página {page}, limite {limit}!")
    return PaginatedEditoras(
        page=page,
        limit=limit,
        total=total,
        items=[EditoraRead(**serialize(e)) for e in editoras_paginadas]
    )


@router.get("/ordenado", response_model=PaginatedEditoras)
def listar_editoras_ordenadas(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    todas = list(Editora.objects().all())
    todas.sort(key=lambda e: e.nome.lower())
    total = len(todas)
    offset = (page - 1) * limit
    editoras_paginadas = todas[offset:offset + limit]

    logger.info(f"Listagem ordenada de editoras! Página {page}, limite {limit}!")
    return PaginatedEditoras(
        page=page,
        limit=limit,
        total=total,
        items=[EditoraRead(**serialize(e)) for e in editoras_paginadas]
    )


@router.get("/count", response_model=EditoraCount)
def contar_editoras():
    total = Editora.objects().count()
    logger.info(f"Contagem de editoras! {total}!")
    return EditoraCount(total_editoras=total)


@router.delete("/", response_model=dict)
def deletar_editora(editora_id: UUID):
    try:
        editora = Editora.objects(id=editora_id).get()
        editora.delete()
        logger.info(f"Editora deletada! ID {editora_id}!")
        return {"message": "Editora deletada com sucesso!"}
    except DoesNotExist:
        logger.warning(f"Tentativa de deletar editora inexistente! ID {editora_id}!")
        raise HTTPException(status_code=404, detail="Editora não encontrada!")


@router.get("/filtro", response_model=PaginatedEditoras)
def filtrar_editoras(
    nome: Optional[str] = Query(None),
    endereco: Optional[str] = Query(None),
    telefone: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    todas = Editora.objects().all()
    if nome:
        todas = [e for e in todas if nome.lower() in e.nome.lower()]
    if endereco:
        todas = [e for e in todas if endereco.lower() in e.endereco.lower()]
    if telefone:
        todas = [e for e in todas if telefone in e.telefone]
    if email:
        todas = [e for e in todas if email.lower() in e.email.lower()]

    total = len(todas)
    if total == 0:
        raise HTTPException(status_code=404, detail="Nenhuma editora encontrada com os filtros informados!")

    offset = (page - 1) * limit
    editoras_paginadas = todas[offset:offset + limit]

    logger.info(
        f"Filtro de editoras aplicado! Página {page}, limite {limit}, total encontrados: {total}!"
    )
    return PaginatedEditoras(
        page=page,
        limit=limit,
        total=total,
        items=[EditoraRead(**serialize(e)) for e in editoras_paginadas]
    )