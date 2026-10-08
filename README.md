# E-commerce em Microsserviços (DevOps)

Projeto acadêmico de uma aplicação de e-commerce construída com **microsserviços em FastAPI**, orquestrada com **Docker Compose** e persistindo dados em **PostgreSQL** (padrão *Database per Service*). O fluxo de pedidos usa o **padrão Saga orquestrado** para manter a consistência entre os serviços de pedido e estoque.

## Arquitetura

```
                       ┌──────────────┐
   Cliente / Postman → │  api-gateway │  :8080   (valida JWT e roteia)
                       └──────┬───────┘
          ┌───────────────────┼────────────────────┐
          ▼                   ▼                    ▼
   ┌─────────────┐     ┌──────────────┐     ┌───────────────┐
   │auth-service │     │pedido-service│ ──► │estoque-service│
   │   :8001     │     │    :8003     │HTTP │    :8002      │
   └─────────────┘     └──────┬───────┘     └───────┬───────┘
                              ▼                     ▼
                         ┌─────────┐           ┌──────────┐
                         │pedido-db│           │estoque-db│
                         │ :5433   │           │  :5432   │
                         └─────────┘           └──────────┘
```

| Serviço | Porta (host) | Responsabilidade |
|---|---|---|
| `api-gateway` | 8080 | Ponto único de entrada; valida o token JWT no `auth-service` e encaminha as requisições |
| `auth-service` | 8001 | Login e emissão/validação de tokens JWT |
| `estoque-service` | 8002 | Cadastro de produtos, reserva e estorno de estoque |
| `pedido-service` | 8003 | Criação, consulta e cancelamento de pedidos (orquestrador da Saga) |
| `estoque-db` | 5432 | PostgreSQL exclusivo do estoque |
| `pedido-db` | 5433 | PostgreSQL exclusivo de pedidos |

### Padrão Saga (orquestrada, síncrona via HTTP)

O `pedido-service` é o orquestrador: ele chama o `estoque-service` e decide o status do pedido com base na resposta.

- **T1 – Reservar estoque:** ao criar um pedido, ele nasce `PENDENTE` e o `pedido-service` chama `POST /estoque/reservar`. Resposta `200` → pedido `CONFIRMADO`; qualquer outra → `CANCELADO`.
- **C1 – Compensação:** ao cancelar um pedido que estava `CONFIRMADO`, o `pedido-service` chama `POST /estoque/estornar` para devolver a quantidade reservada.

### Database per Service

Cada serviço de domínio é dono dos seus dados: `estoque-service` usa o `estoque-db` (tabela `produtos`) e `pedido-service` usa o `pedido-db` (tabela `pedidos`). As tabelas são criadas automaticamente na inicialização de cada serviço (SQLAlchemy). O `auth-service` usa uma lista fixa de usuários de demonstração.

## Tecnologias

- Python 3.11/3.12 + [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn
- SQLAlchemy 2 + psycopg2 + PostgreSQL 14
- PyJWT (autenticação)
- httpx / requests (comunicação entre serviços)
- Docker e Docker Compose
- Pytest + pytest-cov (testes)

## Estrutura do projeto

```
.
├── docker-compose.yml
├── api-gateway/
│   ├── Dockerfile
│   └── main.py
├── auth-service/
│   ├── Dockerfile
│   └── main.py
├── estoque-service/
│   ├── Dockerfile
│   ├── app/
│   │   ├── db.py        # conexão com o Postgres (DATABASE_URL)
│   │   ├── models.py    # modelo ORM (tabela produtos)
│   │   ├── schemas.py   # schemas Pydantic
│   │   ├── service.py   # regras de negócio
│   │   └── main.py      # rotas
│   └── tests/
└── pedido-service/
    ├── Dockerfile
    ├── app/
    │   ├── config.py          # URL do estoque-service
    │   ├── db.py              # conexão com o Postgres (DATABASE_URL)
    │   ├── enums.py           # StatusPedido
    │   ├── estoque_client.py  # cliente HTTP do estoque-service (Saga)
    │   ├── models.py          # modelo ORM (tabela pedidos)
    │   ├── schemas.py
    │   ├── service.py         # regras de negócio / Saga
    │   └── main.py
    └── tests/
```

## Como executar

Pré-requisito: [Docker](https://www.docker.com/) com Docker Compose v2.

```bash
git clone <url-do-repositorio>
cd <pasta-do-projeto>

docker compose up --build
```

Para recomeçar do zero (apagando os dados dos bancos):

```bash
docker compose down -v
docker compose up --build
```

Verifique se está tudo no ar:

```bash
docker compose ps
curl http://localhost:8080/health
```

## Usuários de demonstração

| Usuário | Senha |
|---|---|
| `admin` | `123456` |
| `cliente1` | `senha123` |

> ⚠️ Credenciais e segredos fixos no código/compose servem apenas para fins didáticos. Em produção, use variáveis de ambiente, secrets e senhas com hash.

## Endpoints (via api-gateway, porta 8080)

Todas as rotas, exceto `/login` e `/health`, exigem o header `Authorization: Bearer <token>`.

| Método | Rota | Descrição |
|---|---|---|
| POST | `/login` | Autentica e retorna o token JWT |
| POST | `/produtos` | Cadastra um produto |
| GET | `/produtos/{codigo}` | Consulta um produto |
| POST | `/estoque/reservar` | Reserva estoque |
| POST | `/estoque/estornar` | Estorna estoque |
| POST | `/pedidos` | Cria um pedido (dispara a Saga) |
| GET | `/pedidos/{id}` | Consulta um pedido |
| PUT | `/pedidos/{id}/cancelar` | Cancela um pedido (compensação se estava confirmado) |

## Exemplo de uso (fluxo completo)

```bash
# 1) Login
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "123456"}'
# copie o access_token retornado

# 2) Cadastrar produto
curl -X POST http://localhost:8080/produtos \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"codigo": "P1", "nome": "Camiseta", "quantidade": 10}'

# 3) Criar pedido (T1: reserva 3 unidades → status CONFIRMADO)
curl -X POST http://localhost:8080/pedidos \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"codigo_produto": "P1", "quantidade": 3}'

# 4) Conferir estoque (deve estar com 7)
curl http://localhost:8080/produtos/P1 -H "Authorization: Bearer SEU_TOKEN"

# 5) Cancelar o pedido (C1: estorna as 3 unidades)
curl -X PUT http://localhost:8080/pedidos/ID_DO_PEDIDO/cancelar \
  -H "Authorization: Bearer SEU_TOKEN"

# 6) Conferir estoque novamente (volta a 10)
curl http://localhost:8080/produtos/P1 -H "Authorization: Bearer SEU_TOKEN"
```

Para criar um pedido sem estoque suficiente, use uma quantidade maior que o saldo (ex.: `999`): o pedido é criado já com status `CANCELADO`.

### Conferindo os dados direto no banco

```bash
docker compose exec estoque-db psql -U admin_estoque -d estoque_db -c "SELECT * FROM produtos;"
docker compose exec pedido-db psql -U admin_pedido -d pedido_db -c "SELECT * FROM pedidos;"
```

## Testes

Os testes usam SQLite em memória (não precisam do Postgres) e fazem *mock* das chamadas HTTP ao `estoque-service`.

```bash
docker compose exec estoque-service pytest tests/ --cov=app --cov-report=term-missing
docker compose exec pedido-service pytest tests/ --cov=app --cov-report=term-missing
```

## Limitações conhecidas

- A Saga é síncrona via HTTP: não há retry, fila de mensagens nem log persistido da saga.
- Se a reserva for feita no estoque mas a resposta se perder (timeout), o pedido pode ficar `CANCELADO` sem que o estorno seja disparado.
- O `auth-service` usa usuários fixos em memória e o segredo do JWT está no código.
- Não há migrações de banco (as tabelas são criadas com `create_all`).

## Licença

Projeto acadêmico, sem licença definida.
