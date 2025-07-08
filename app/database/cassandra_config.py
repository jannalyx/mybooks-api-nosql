from cassandra.cqlengine import connection
from cassandra.cluster import Cluster
import os

def connect_to_cassandra():
    # Cassandra via Docker!
    CASSANDRA_HOSTS = os.getenv("CASSANDRA_HOSTS", "127.0.0.1").split(",")
    CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "mybooks")

    # Sem autenticação!
    cluster = Cluster(CASSANDRA_HOSTS, port=9042)
    session = cluster.connect()

    # Se não existir, cria o keyspace!
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE}
        WITH replication = {{
            'class': 'SimpleStrategy',
            'replication_factor': 1
        }};
    """)

    session.set_keyspace(CASSANDRA_KEYSPACE)

    # Conecta o ORM cqlengine!
    connection.set_session(session)
    print("Conectado ao Cassandra!")