import random
from faker import Faker
from neo4j import GraphDatabase
from pymongo import MongoClient

fake = Faker()

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_user(self, user):
        with self.driver.session() as session:
            session.run("CREATE (u:User {id: $id, name: $name, age: $age, location: $location})", **user)

    def create_friendship(self, user1_id, user2_id):
        with self.driver.session() as session:
            session.run("""
                MATCH (u1:User {id: $user1_id}), (u2:User {id: $user2_id})
                CREATE (u1)-[:FRIENDS_WITH {since: $since}]->(u2)
            """, user1_id=user1_id, user2_id=user2_id, since=fake.date_this_year())

    def create_post(self, post_id):
        with self.driver.session() as session:
            session.run("CREATE (p:Post {id: $post_id})", post_id=post_id)

    def create_like(self, user_id, post_id):
        with self.driver.session() as session:
            session.run("""
                MATCH (u:User {id: $user_id}), (p:Post {id: $post_id})
                CREATE (u)-[:LIKES]->(p)
            """, user_id=user_id, post_id=post_id)

class MongoDBConnection:
    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.db = self.client["social_network"]
        self.posts = self.db["posts"]

    def insert_post(self, post):
        self.posts.insert_one(post)

def generate_fake_data(num_users=1000, avg_friends=10, num_posts_factor=10):
    neo4j_conn = Neo4jConnection("bolt://localhost:7687", "neo4j", "admin123")
    mongo_conn = MongoDBConnection("mongodb://localhost:27017/")

    # Limpar os bancos antes de gerar novos dados
    print("Limpando bancos de dados...")
    with neo4j_conn.driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    mongo_conn.posts.drop()

    print(f"Criando {num_users} usuários...")
    users = []
    for i in range(num_users):
        user = {"id": i, "name": fake.name(), "age": random.randint(18, 65), "location": fake.city()}
        neo4j_conn.create_user(user)
        users.append(user)

    print("Criando amizades...")
    for user in users:
        num_friends = random.randint(1, avg_friends * 2)
        friends = random.sample(range(num_users), min(num_friends, num_users - 1))
        for friend_id in friends:
            if friend_id != user["id"]:
                neo4j_conn.create_friendship(user["id"], friend_id)

    print("Criando postagens e interações...")
    num_posts = num_users * num_posts_factor
    tag_options = ["tech", "food", "travel", "sports", "music"]
    for i in range(num_posts):
        user_id = random.randint(0, num_users - 1)
        post = {
            "id": i,
            "user_id": user_id,
            "content": fake.text(max_nb_chars=200),
            "date": fake.date_time_this_year(),
            "likes": random.randint(0, 100),
            "tags": random.sample(tag_options, k=3)
        }
        mongo_conn.insert_post(post)
        neo4j_conn.create_post(i)
        num_likes = random.randint(0, min(10, num_users - 1))
        likers = random.sample(range(num_users), num_likes)
        for liker_id in likers:
            neo4j_conn.create_like(liker_id, i)

    neo4j_conn.close()
    mongo_conn.client.close()
    print(f"Dados fictícios gerados com sucesso para {num_users} usuários!")

if __name__ == "__main__":
    generate_fake_data(num_users=1000)  # Gera 1000 usuários uma vez