"""
Camada de SERVIÇO (regras de negócio).
Cadastrar, reservar e estornar. Nada aqui sabe o que é "HTTP" — mas agora
tudo passa por uma sessão do SQLAlchemy (db: Session), persistindo no Postgres.
"""

from sqlalchemy.orm import Session

from app.models import ProdutoORM


class EstoqueInsuficienteError(Exception):
    pass


class ProdutoNaoEncontradoError(Exception):
    pass


def cadastrar_produto(db: Session, codigo: str, nome: str, quantidade: int) -> ProdutoORM:
    produto = ProdutoORM(codigo=codigo, nome=nome, quantidade=quantidade)
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


def consultar_produto(db: Session, codigo: str) -> ProdutoORM:
    produto = db.get(ProdutoORM, codigo)
    if produto is None:
        raise ProdutoNaoEncontradoError(f"Produto {codigo} não encontrado")
    return produto


def reservar_estoque(db: Session, codigo: str, quantidade: int) -> ProdutoORM:
    produto = consultar_produto(db, codigo)
    if produto.quantidade < quantidade:
        raise EstoqueInsuficienteError(
            f"Estoque insuficiente para {codigo}: disponível {produto.quantidade}, "
            f"solicitado {quantidade}"
        )
    produto.quantidade -= quantidade
    db.commit()
    db.refresh(produto)
    return produto


def estornar_estoque(db: Session, codigo: str, quantidade: int) -> ProdutoORM:
    produto = consultar_produto(db, codigo)
    produto.quantidade += quantidade
    db.commit()
    db.refresh(produto)
    return produto
