import time
import statistics
import random
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from neo4j import GraphDatabase
from pymongo import MongoClient
from faker import Faker

fake = Faker()

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def find_common_friends(self, user1_id, user2_id):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u1:User {id: $user1_id})-[:FRIENDS_WITH]->(common)<-[:FRIENDS_WITH]-(u2:User {id: $user2_id})
                RETURN common.id
            """, user1_id=user1_id, user2_id=user2_id)
            return [record["common.id"] for record in result]

    def recommend_friends(self, user_id):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:FRIENDS_WITH]->(f)-[:FRIENDS_WITH]->(recommended)
                WHERE NOT (u)-[:FRIENDS_WITH]->(recommended) AND u <> recommended
                RETURN DISTINCT recommended.id
            """, user_id=user_id)
            return [record["recommended.id"] for record in result]

    def insert_friendship(self, user1_id, user2_id):
        with self.driver.session() as session:
            session.run("""
                MATCH (u1:User {id: $user1_id}), (u2:User {id: $user2_id})
                CREATE (u1)-[:FRIENDS_WITH {since: $since}]->(u2)
            """, user1_id=user1_id, user2_id=user2_id, since=fake.date_this_year())

    def create_post(self, post_id):
        with self.driver.session() as session:
            session.run("CREATE (p:Post {id: $post_id})", post_id=post_id)

class MongoDBConnection:
    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.db = self.client["social_network"]
        self.posts = self.db["posts"]

    def find_posts_by_tag(self, tag):
        return list(self.posts.find({"tags": tag}))

    def find_popular_posts(self, min_likes=50):
        return list(self.posts.find({"likes": {"$gte": min_likes}}))

    def count_posts_by_user(self, user_id):
        return self.posts.count_documents({"user_id": user_id})

    def insert_post(self, post):
        self.posts.insert_one(post)

def run_benchmarks(neo4j_conn, mongo_conn, max_users=1000, sizes=[100, 500, 1000], num_tests=5):
    results = {
        "neo4j_common_friends": {size: [] for size in sizes},
        "mongo_posts_by_tag": {size: [] for size in sizes},
        "neo4j_insert_friend": {size: [] for size in sizes},
        "mongo_insert_post": {size: [] for size in sizes},
        "neo4j_recommend_friends": {size: [] for size in sizes},
        "mongo_popular_posts": {size: [] for size in sizes}
    }

    post_counter = max_users * 10  # ID inicial para novas postagens

    for size in sizes:
        print(f"\n=== Testando com {size} usuários (limite dentro de {max_users} existentes) ===")
        user1, user2 = 0, 1
        tag = random.choice(["tech", "food", "travel", "sports", "music"])

        for _ in range(2):  # Warm-up
            neo4j_conn.find_common_friends(user1, user2)
            mongo_conn.find_posts_by_tag(tag)

        for _ in range(num_tests):
            # Limitar IDs aos usuários dentro do tamanho testado
            start = time.time()
            neo4j_conn.find_common_friends(user1, user2)
            results["neo4j_common_friends"][size].append(time.time() - start)

            start = time.time()
            mongo_conn.find_posts_by_tag(tag)
            results["mongo_posts_by_tag"][size].append(time.time() - start)

            new_user_id = random.randint(0, size - 1)  # Limita o intervalo ao tamanho atual
            start = time.time()
            neo4j_conn.insert_friendship(user1, new_user_id)
            results["neo4j_insert_friend"][size].append(time.time() - start)

            start = time.time()
            new_post = {
                "id": post_counter,
                "user_id": user1,
                "content": fake.text(max_nb_chars=200),
                "date": fake.date_time_this_year(),
                "likes": 0,
                "tags": [tag]
            }
            mongo_conn.insert_post(new_post)
            neo4j_conn.create_post(post_counter)
            results["mongo_insert_post"][size].append(time.time() - start)
            post_counter += 1

            start = time.time()
            neo4j_conn.recommend_friends(user1)
            results["neo4j_recommend_friends"][size].append(time.time() - start)

            start = time.time()
            mongo_conn.find_popular_posts(min_likes=50)
            results["mongo_popular_posts"][size].append(time.time() - start)

    analyze_results(results, sizes, num_tests)
    visualize_results(results, sizes)

def analyze_results(results, sizes, num_tests):
    print("\n=== Análise dos Resultados ===")
    summary = []
    for op, times_by_size in results.items():
        for size in sizes:
            times = times_by_size[size]
            mean = statistics.mean(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0
            summary.append({
                "Operação": op,
                "Tamanho": size,
                "Média (s)": mean,
                "Desvio Padrão (s)": std_dev,
                "Mínimo (s)": min(times),
                "Máximo (s)": max(times)
            })
            print(f"{op} ({size} usuários): Média {mean:.6f}s, Desvio Padrão {std_dev:.6f}s")

    df = pd.DataFrame(summary)
    print("\n=== Tabela Comparativa ===")
    print(df.to_string(index=False))

def visualize_results(results, sizes):
    plt.figure(figsize=(12, 6))
    means = {
        op: [statistics.mean(results[op][size]) for size in sizes]
        for op in ["neo4j_common_friends", "mongo_posts_by_tag"]
    }
    x = range(len(sizes))
    width = 0.35
    plt.bar([i - width/2 for i in x], means["neo4j_common_friends"], width, label="Neo4j: Amigos em Comum")
    plt.bar([i + width/2 for i in x], means["mongo_posts_by_tag"], width, label="MongoDB: Posts por Tag")
    plt.xticks(x, sizes)
    plt.xlabel("Número de Usuários Testados")
    plt.ylabel("Tempo Médio (s)")
    plt.title("Comparação de Tempo de Consulta")
    plt.legend()
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(12, 6))
    for op in results.keys():
        means = [statistics.mean(results[op][size]) for size in sizes]
        plt.plot(sizes, means, marker='o', label=op)
    plt.xlabel("Número de Usuários Testados")
    plt.ylabel("Tempo Médio (s)")
    plt.title("Escalabilidade: Tempo vs Tamanho Testado")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(12, 6))
    flat_data = {op: [t for size in sizes for t in results[op][size]] for op in results.keys()}
    sns.boxplot(data=pd.DataFrame(flat_data))
    plt.xticks(rotation=45)
    plt.title("Distribuição dos Tempos de Resposta")
    plt.ylabel("Tempo (s)")
    plt.tight_layout()
    plt.show()

def main():
    neo4j_conn = Neo4jConnection("bolt://localhost:7687", "neo4j", "admin123")
    mongo_conn = MongoDBConnection("mongodb://localhost:27017/")

    # Gera os dados uma vez para o tamanho máximo
    from generate_fake_data import generate_fake_data
    max_users = 1000
    generate_fake_data(num_users=max_users)

    # Executa o benchmark limitando os usuários testados
    run_benchmarks(neo4j_conn, mongo_conn, max_users=max_users, sizes=[100, 500, 1000])

    neo4j_conn.close()
    mongo_conn.client.close()

if __name__ == "__main__":
    main()