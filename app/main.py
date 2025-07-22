from fastapi import FastAPI
from app.logs.setup_logger import setup_logging

setup_logging()

from cassandra.cqlengine.management import sync_table
from app.database.cassandra_config import connect_to_cassandra
from app.models.models import Autor, Editora, Livro, Usuario, Pedido, Pagamento, PedidoPagamento
from app.routes import autores, editoras, livros, usuarios, pedidos, pagamentos, pedido_pagamento, pedido_livro
from app.routes import consulta_usuario  

app = FastAPI(title="MyBooks API - Cassandra")

@app.on_event("startup")
def on_startup():
    connect_to_cassandra()
    sync_table(Autor)
    sync_table(Editora)
    sync_table(Livro)
    sync_table(Usuario)
    sync_table(Pedido)
    sync_table(Pagamento)
    sync_table(PedidoPagamento)  

app.include_router(autores.router)
app.include_router(editoras.router)
app.include_router(livros.router)
app.include_router(usuarios.router)
app.include_router(pedidos.router)
app.include_router(pagamentos.router)
app.include_router(pedido_pagamento.router)
app.include_router(pedido_livro.router)
app.include_router(consulta_usuario.router)  
