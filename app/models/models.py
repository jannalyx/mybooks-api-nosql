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