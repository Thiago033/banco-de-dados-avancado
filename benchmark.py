import time
from neo4j import GraphDatabase
from pymongo import MongoClient

# Configuração do Neo4j
class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def find_common_friends(self, user1_id, user2_id):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u1:User {id: $user1_id})-[:FRIENDS_WITH]->(common)<-[:FRIENDS_WITH]-(u2:User {id: $user2_id})
                RETURN common.name
            """, user1_id=user1_id, user2_id=user2_id)
            return [record["common.name"] for record in result]

# Configuração do MongoDB
class MongoDBConnection:
    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.db = self.client["social_network"]
        self.posts = self.db["posts"]

    def close(self):
        self.client.close()

    def find_posts_by_user(self, user_id):
        return list(self.posts.find({"user_id": user_id}))

# Função para executar benchmarks
def run_benchmarks(neo4j_conn, mongo_conn, user1_id=0, user2_id=1):
    # Benchmark Neo4j - Busca de amigos em comum
    start_time = time.time()
    common_friends = neo4j_conn.find_common_friends(user1_id, user2_id)
    neo4j_time = time.time() - start_time
    print(f"Neo4j - Amigos em comum: {len(common_friends)} encontrados em {neo4j_time:.4f} segundos")

    # Benchmark MongoDB - Busca de postagens por usuário
    start_time = time.time()
    posts = mongo_conn.find_posts_by_user(user1_id)
    mongo_time = time.time() - start_time
    print(f"MongoDB - {len(posts)} postagens encontradas em {mongo_time:.4f} segundos")

# Função principal para rodar os benchmarks
def main():
    # Conexões aos bancos (ajuste as credenciais conforme seu ambiente)
    neo4j_conn = Neo4jConnection("bolt://localhost:7687", "neo4j", "admin123")
    mongo_conn = MongoDBConnection("mongodb://localhost:27017/")

    print("\nExecutando benchmarks...")
    run_benchmarks(neo4j_conn, mongo_conn)

    # Fechando conexões
    neo4j_conn.close()
    mongo_conn.close()

if __name__ == "__main__":
    main()
