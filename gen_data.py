import time
from neo4j import GraphDatabase
from pymongo import MongoClient
import random
import faker

# Inicializando o Faker para gerar dados fictícios
fake = faker.Faker()

# Configuração do Neo4j
class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_user(self, user_id, name):
        with self.driver.session() as session:
            session.run("CREATE (u:User {id: $id, name: $name})", id=user_id, name=name)

    def create_friendship(self, user1_id, user2_id):
        with self.driver.session() as session:
            session.run("""
                MATCH (u1:User {id: $user1_id}), (u2:User {id: $user2_id})
                CREATE (u1)-[:FRIENDS_WITH]->(u2)
            """, user1_id=user1_id, user2_id=user2_id)

    def delete_all_data(self):
        with self.driver.session() as session:
            # Remove todos os nós e relacionamentos
            session.run("MATCH (n) DETACH DELETE n;")
            print("Todos os dados no Neo4j foram excluídos.")

# Configuração do MongoDB
class MongoDBConnection:
    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.db = self.client["social_network"]
        self.posts = self.db["posts"]

    def close(self):
        self.client.close()

    def create_post(self, user_id, content):
        post = {
            "user_id": user_id,
            "content": content,
            "timestamp": time.time()
        }
        self.posts.insert_one(post)

    def delete_all_data(self):
        # Exclui todos os documentos na coleção posts
        self.posts.delete_many({})
        print("Todos os dados no MongoDB foram excluídos.")

# Função para popular os bancos com dados de teste
def populate_data(neo4j_conn, mongo_conn, num_users=100, num_posts_per_user=10):
    # Criando usuários no Neo4j
    for i in range(num_users):
        neo4j_conn.create_user(i, fake.name())

    # Criando amizades aleatórias no Neo4j
    for i in range(num_users):
        num_friends = random.randint(1, 10)
        friends = random.sample(range(num_users), num_friends)
        for friend_id in friends:
            if friend_id != i:
                neo4j_conn.create_friendship(i, friend_id)

    # Criando postagens no MongoDB
    for i in range(num_users):
        for _ in range(num_posts_per_user):
            mongo_conn.create_post(i, fake.text(max_nb_chars=200))

# Função principal para gerar dados
def main():
    # Conexões aos bancos (ajuste as credenciais conforme seu ambiente)
    neo4j_conn = Neo4jConnection("bolt://localhost:7687", "neo4j", "admin123")
    mongo_conn = MongoDBConnection("mongodb://localhost:27017/")

    # Verifica se já existem dados no Neo4j e MongoDB, e exclui-os se necessário
    print("Verificando dados existentes e excluindo, se necessário...")
    neo4j_conn.delete_all_data()
    mongo_conn.delete_all_data()

    print("Populando os bancos com dados de teste...")
    populate_data(neo4j_conn, mongo_conn, num_users=20, num_posts_per_user=2)

    # Fechando conexões
    neo4j_conn.close()
    mongo_conn.close()

if __name__ == "__main__":
    main()
