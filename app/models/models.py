from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns
import uuid

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

class Pedido(Model):
    __keyspace__ = 'mybooks'

    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    usuario_id = columns.UUID(required=True)  #usuários precisa ter UUIDs (jana)
    data_pedido = columns.Date()
    status = columns.Text()
    valor_total = columns.Float()

class Pagamento(Model):
    __keyspace__ = 'mybooks'

    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    pedido_id = columns.UUID(required=True)  
    data_pagamento = columns.Date()
    valor = columns.Float()
    forma_pagamento = columns.Text()