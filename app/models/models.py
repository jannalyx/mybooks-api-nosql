from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns
import uuid
from datetime import date


class Autor(Model):
    __keyspace__ = 'mybooks'
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    nome = columns.Text(index=True)
    email = columns.Text(index=True)
    data_nascimento = columns.Date()
    nacionalidade = columns.Text()
    biografia = columns.Text(required=False)


class Editora(Model):
    __keyspace__ = 'mybooks'
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    nome = columns.Text()
    endereco = columns.Text()
    telefone = columns.Text()
    email = columns.Text()


class Livro(Model):
    __keyspace__ = 'mybooks'
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    titulo = columns.Text()
    sinopse = columns.Text(required=False)
    genero = columns.Text()
    preco = columns.Float()
    data_publicacao = columns.Date()
    autor_id = columns.UUID(index=True)
    editora_id = columns.UUID(index=True)


class Usuario(Model):
    __keyspace__ = 'mybooks'
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    nome = columns.Text(index=True)
    email = columns.Text(index=True)
    cpf = columns.Text(index=True)
    data_cadastro = columns.Date(default=date.today)


class Pedido(Model):
    __keyspace__ = 'mybooks'
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    usuario_id = columns.UUID(index=True)
    status = columns.Text()
    valor_total = columns.Float()
    data_pedido = columns.Date()
    
class Pagamento(Model):
    __keyspace__ = 'mybooks'
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    pedido_id = columns.UUID(index=True)
    valor = columns.Float()
    data_pagamento = columns.Date()
    forma_pagamento = columns.Text()

class PedidoPagamento(Model):
    __keyspace__ = 'mybooks'
    pedido_id = columns.UUID(primary_key=True, partition_key=True)
    pagamento_id = columns.UUID(primary_key=True, clustering_order="ASC")