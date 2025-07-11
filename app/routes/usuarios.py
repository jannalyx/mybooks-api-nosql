from uuid import UUID
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from cassandra.cqlengine.query import DoesNotExist
from cassandra.util import Date as CassandraDate
from datetime import date
from app.models.models import Usuario
from app.schemas.schemas import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioRead,
    UsuarioCount,
    PaginatedUsuario,
)
from app.logs.logger import get_logger

logger = get_logger("MyBooks")
router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def serialize(usuario: Usuario) -> dict:
    data = {field: getattr(usuario, field) for field in Usuario._columns.keys()}
    cass_data = data.get("data_cadastro")

    try:
        if isinstance(cass_data, (date, CassandraDate)):
            data["data_cadastro"] = date.fromisoformat(str(cass_data))
        else:
            logger.warning(f"data_cadastro inválido: {cass_data} ({type(cass_data)})!")
            raise ValueError("data_cadastro inválido!")
    except Exception as e:
        logger.warning(f"Erro ao converter data_cadastro: {e}!")
        raise

    return data


@router.get("/usuarios/{id}", response_model=UsuarioRead)
def obter_usuario_por_id(id: UUID):
    try:
        usuario = Usuario.objects(id=id).get()
        return UsuarioRead(**serialize(usuario))
    except DoesNotExist:
        logger.warning(f"Usuário não encontrado! ID {id}!")
        raise HTTPException(status_code=404, detail="Usuário não encontrado!")


@router.post("/", response_model=UsuarioRead)
def criar_usuario(usuario: UsuarioCreate):
    if Usuario.objects(cpf=usuario.cpf).allow_filtering().count() > 0:
        logger.warning(f"CPF já cadastrado! {usuario.cpf}!")
        raise HTTPException(status_code=400, detail="Já existe um usuário com esse CPF!")

    novo_usuario = Usuario.create(**usuario.dict())
    logger.info(f"Usuário criado: {novo_usuario.id} - {novo_usuario.nome} ({novo_usuario.email})!")
    return UsuarioRead(**serialize(novo_usuario))


@router.patch("/", response_model=UsuarioRead)
def atualizar_usuario(usuario_id: UUID, usuario_update: UsuarioUpdate):
    try:
        usuario = Usuario.objects(id=usuario_id).get()
    except DoesNotExist:
        logger.warning(f"Tentativa de atualizar usuário inexistente! ID {usuario_id}!")
        raise HTTPException(status_code=404, detail="Usuário não encontrado!")

    update_data = usuario_update.dict(exclude_unset=True)

    if "cpf" in update_data:
        cpf_existente = Usuario.objects(cpf=update_data["cpf"]).allow_filtering()
        for u in cpf_existente:
            if u.id != usuario_id:
                logger.warning(f"CPF já em uso por outro usuário! {update_data['cpf']}!")
                raise HTTPException(status_code=400, detail="Já existe um usuário com esse CPF!")

    for key, value in update_data.items():
        setattr(usuario, key, value)
    usuario.update(**update_data)

    logger.info(f"Usuário atualizado! ID {usuario_id}!")
    return UsuarioRead(**serialize(usuario))


@router.get("/", response_model=PaginatedUsuario)
def listar_usuarios(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    offset = (page - 1) * limit
    todos = list(Usuario.objects().all())
    total = len(todos)
    usuarios_paginados = todos[offset:offset + limit]

    logger.info(f"Listagem paginada de usuários! Página {page}, limite {limit}!")
    return PaginatedUsuario(
        page=page,
        limit=limit,
        total=total,
        items=[UsuarioRead(**serialize(u)) for u in usuarios_paginados]
    )


@router.get("/ordenado", response_model=PaginatedUsuario)
def listar_usuarios_ordenados(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    todos = list(Usuario.objects().all())
    todos.sort(key=lambda u: u.nome.lower())
    total = len(todos)
    offset = (page - 1) * limit
    usuarios_paginados = todos[offset:offset + limit]

    logger.info(f"Listagem ordenada de usuários! Página {page}, limite {limit}!")
    return PaginatedUsuario(
        page=page,
        limit=limit,
        total=total,
        items=[UsuarioRead(**serialize(u)) for u in usuarios_paginados]
    )


@router.get("/count", response_model=UsuarioCount)
def contar_usuarios():
    total = Usuario.objects().count()
    logger.info(f"Contagem de usuários! {total}!")
    return UsuarioCount(total_usuarios=total)


@router.delete("/", response_model=dict)
def deletar_usuario(usuario_id: UUID):
    try:
        usuario = Usuario.objects(id=usuario_id).get()
        usuario.delete()
        logger.info(f"Usuário deletado! ID {usuario_id}!")
        return {"message": "Usuário deletado com sucesso!"}
    except DoesNotExist:
        logger.warning(f"Tentativa de deletar usuário inexistente! ID {usuario_id}!")
        raise HTTPException(status_code=404, detail="Usuário não encontrado!")


@router.get("/filtrar", response_model=PaginatedUsuario)
def filtrar_usuarios(
    nome: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    cpf: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    todos = Usuario.objects().all()
    if nome:
        todos = [u for u in todos if nome.lower() in u.nome.lower()]
    if email:
        todos = [u for u in todos if email.lower() in u.email.lower()]
    if cpf:
        todos = [u for u in todos if cpf == u.cpf]

    total = len(todos)
    if total == 0:
        raise HTTPException(status_code=404, detail="Nenhum usuário encontrado com os filtros informados!")

    offset = (page - 1) * limit
    usuarios_paginados = todos[offset:offset + limit]

    logger.info(f"Filtro de usuários aplicado! Página {page}, limite {limit}, total encontrados: {total}!")
    return PaginatedUsuario(
        page=page,
        limit=limit,
        total=total,
        items=[UsuarioRead(**serialize(u)) for u in usuarios_paginados]
    )