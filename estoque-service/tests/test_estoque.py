import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


engine_teste = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocalTeste = sessionmaker(autocommit=False, autoflush=False, bind=engine_teste)


def _get_db_teste():
    db = SessionLocalTeste()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _get_db_teste

client = TestClient(app)


@pytest.fixture(autouse=True)
def recriar_tabelas():
    Base.metadata.create_all(bind=engine_teste)
    yield
    Base.metadata.drop_all(bind=engine_teste)


def test_health():
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_cadastrar_produto():
    resposta = client.post(
        "/produtos", json={"codigo": "P1", "nome": "Camiseta", "quantidade": 10}
    )
    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["codigo"] == "P1"
    assert dados["quantidade"] == 10


def test_consultar_produto_existente():
    client.post("/produtos", json={"codigo": "P2", "nome": "Boné", "quantidade": 5})
    resposta = client.get("/produtos/P2")
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Boné"


def test_consultar_produto_inexistente():
    resposta = client.get("/produtos/NAO_EXISTE")
    assert resposta.status_code == 404


def test_reservar_estoque_com_saldo_suficiente():
    client.post("/produtos", json={"codigo": "P3", "nome": "Tênis", "quantidade": 20})
    resposta = client.post("/estoque/reservar", json={"codigo": "P3", "quantidade": 5})
    assert resposta.status_code == 200
    assert resposta.json()["produto"]["quantidade"] == 15


def test_reservar_estoque_insuficiente_retorna_400():
    client.post("/produtos", json={"codigo": "P4", "nome": "Bolsa", "quantidade": 2})
    resposta = client.post("/estoque/reservar", json={"codigo": "P4", "quantidade": 10})
    assert resposta.status_code == 400


def test_estornar_estoque():
    client.post("/produtos", json={"codigo": "P5", "nome": "Meia", "quantidade": 10})
    client.post("/estoque/reservar", json={"codigo": "P5", "quantidade": 4})
    resposta = client.post("/estoque/estornar", json={"codigo": "P5", "quantidade": 4})
    assert resposta.status_code == 200
    assert resposta.json()["produto"]["quantidade"] == 10
