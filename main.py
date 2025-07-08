from fastapi import FastAPI
from cassandra.cqlengine.management import sync_table
from app.database.cassandra_config import connect_to_cassandra
from app.models.models import Autor, Editora
from app.routes import autores, editoras

app = FastAPI(title="MyBooks API - Cassandra")

@app.on_event("startup")
def on_startup():
    connect_to_cassandra()
    sync_table(Autor)
    sync_table(Editora)

app.include_router(autores.router)
app.include_router(editoras.router)