# Projeto de Integração entre Neo4j e MongoDB

Este projeto tem como objetivo a integração entre os bancos de dados **Neo4j** e **MongoDB** para simulação de dados de uma rede social, permitindo a realização de benchmarks de desempenho para consultas em ambos os bancos. A seguir, estão os passos necessários para configurar o ambiente e executar os scripts.

## Passo 1: Preparação do Ambiente

### 1.1. Instalar o Neo4j
Baixe e instale o [Neo4j](https://neo4j.com/download/) em sua máquina ou use uma instância em nuvem como o [Neo4j Aura](https://neo4j.com/aura/).

No Windows, você pode usar o **Neo4j Desktop** ou o **Docker** para rodar o Neo4j.

Após a instalação, inicie o Neo4j Desktop ou a instância Docker e configure um banco de dados. O URI de conexão padrão é `bolt://localhost:7687` e o usuário padrão é `neo4j` com a senha `neo4j` (essa senha pode ser alterada conforme necessário).

### 1.2. Instalar o MongoDB
Baixe e instale o [MongoDB](https://www.mongodb.com/try/download/community) ou use uma instância em nuvem como o [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).

Após a instalação, inicie o MongoDB localmente.

### 1.3. Instalar as Bibliotecas Python
No terminal, instale as bibliotecas Python necessárias com o comando:

```bash
pip install neo4j pymongo faker
```

- **neo4j**: Biblioteca para se conectar ao Neo4j.
- **pymongo**: Biblioteca para se conectar ao MongoDB.
- **faker**: Biblioteca para gerar dados fictícios.

## Passo 2: Criar e Executar os Scripts

### 2.1. Script para Gerar Dados Falsos
Crie um script Python chamado `gerar_dados.py` para gerar dados de usuários, amizades e postagens para os bancos de dados.

Esse script realiza as seguintes ações:
- Conecta-se ao Neo4j e MongoDB.
- Exclui os dados antigos de ambos os bancos.
- Gera 100 usuários, cria amizades aleatórias e cria 10 postagens por usuário.
- Popula os bancos com esses dados.

### 2.2. Script para Executar os Benchmarks
Crie outro script Python chamado `executar_benchmarks.py` para executar os benchmarks de desempenho.

Esse script realiza as seguintes ações:
- Conecta-se ao Neo4j e MongoDB.
- Realiza consultas de benchmarks para:
  - **Neo4j**: Encontra amigos em comum entre dois usuários.
  - **MongoDB**: Encontra postagens de um usuário.
- Exibe os tempos de resposta das consultas.

## Passo 3: Executando os Scripts

### 3.1. Gerar Dados
Abra o terminal e navegue até o diretório onde o script `gerar_dados.py` está localizado.

Execute o script para gerar os dados com o comando:

```bash
python gerar_dados.py
```

Isso irá:
- Excluir os dados existentes no Neo4j e MongoDB.
- Gerar 100 usuários, criar amizades e postagens.

### 3.2. Executar os Benchmarks
Após gerar os dados, execute o script de benchmarks para medir o desempenho das consultas:

```bash
python executar_benchmarks.py
```

Isso irá:
- Executar os benchmarks, mostrando os tempos de resposta para as consultas no Neo4j e MongoDB.

## Passo 4: Consultas

### No Neo4j

Para consultar os amigos de um usuário específico no Neo4j, use a seguinte consulta Cypher, assumindo que os amigos estão armazenados como um relacionamento do tipo `FRIENDS_WITH`:

```cypher
MATCH (u:User {id: 0})-[:FRIENDS_WITH]->(friend)
RETURN friend
```

**Explicação da Consulta:**
- `MATCH (u:User {id: 0})`: Encontra o usuário com ID igual a 0.
- `-[:FRIENDS_WITH]->`: O relacionamento `FRIENDS_WITH` indica a amizade entre os usuários.
- `RETURN friend`: Retorna todos os amigos encontrados.

Para consultar amigos em comum entre dois usuários (por exemplo, usuários com ID 0 e ID 1), use a seguinte consulta:

```cypher
MATCH (u1:User {id: 0})-[:FRIENDS_WITH]->(common)<-[:FRIENDS_WITH]-(u2:User {id: 1})
RETURN common
```

### No MongoDB

Para realizar consultas no MongoDB usando o **mongosh**, siga os passos abaixo:

#### Passo 1: Abrir o `mongosh`
Abra o **mongosh** no terminal. Se não estiver instalado, baixe do [site oficial do MongoDB](https://www.mongodb.com/try/download/shell).

Execute o comando:

```bash
mongosh
```

#### Passo 2: Conectar ao Banco de Dados
Conecte-se à instância do MongoDB. Para uma instalação local padrão, use o comando:

```bash
mongosh "mongodb://localhost:27017/"
```

#### Passo 3: Selecionar o Banco de Dados
Escolha o banco de dados com o comando:

```javascript
use social_network
```

#### Passo 4: Consultar as Postagens

- **Consulta Básica**: Para encontrar todas as postagens:

```javascript
db.posts.find()
```

- **Consultar Postagens de um Usuário Específico**: Para consultar postagens de um usuário com `user_id = 0`:

```javascript
db.posts.find({ "user_id": 0 })
```

- **Limitar o Número de Postagens**: Para obter as 5 primeiras postagens de um usuário:

```javascript
db.posts.find({ "user_id": 0 }).limit(5)
```

- **Projeção (Exibir Campos Específicos)**: Para exibir apenas o conteúdo e o timestamp das postagens:

```javascript
db.posts.find({ "user_id": 0 }, { "content": 1, "timestamp": 1 })
```

#### Passo 5: Fechar a Conexão
Após realizar as consultas, saia do **mongosh** com o comando:

```javascript
exit
```

## Conclusão
Este projeto permite a integração de dois tipos diferentes de bancos de dados (Neo4j e MongoDB) e oferece uma maneira de comparar o desempenho de consultas entre eles em um cenário de rede social fictícia.