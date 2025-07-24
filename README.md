# Projeto MyBooks API NoSQL

## Descrição

Este projeto é uma API RESTful desenvolvida com **FastAPI** para gerenciamento de um domínio de livros utilizando banco de dados **NoSQL (Apache Cassandra)**.

A aplicação simula relacionamentos entre entidades como usuários, livros, editoras, autores, pedidos e pagamentos, utilizando identificadores UUID para garantir a consistência.

A estrutura foi organizada em camadas: models, schemas, routers e logs.

---

## Funcionalidades

- CRUD completo das entidades principais
- Relacionamentos simulados via UUIDs
- Endpoints para consultas compostas (joins manuais)
- Estrutura modular (models, schemas, routers, logs)
- Integração com banco **Cassandra** via `cqlengine`

---

## Tecnologias Utilizadas

- Python 3.10+
- FastAPI
- Apache Cassandra
- Docker e Docker Compose
- CQLEngine (Object Mapper)
- Pydantic

---

## Como executar o projeto

1. Clone o repositório e navegue até o diretório do projeto:

bash
git clone https://github.com/jannalyx/mybooks-api-nosql.git
cd mybooks-api-nosq



2. Instale as dependências:

bash
pip install -r requirements.txt



3. Suba o banco Cassandra com Docker:

bash
docker-compose up -d



4. Aguarde o Cassandra iniciar e entre no terminal do container para verificar

bash
docker exec -it cassandra-db cqlsh



5. Rode a aplicação:

bash
uvicorn app.main:app --reload



6. Acesse a documentação interativa:

bash
http://localhost:8000/docs