"""
Camada de MODELOS (ORM).
Aqui definimos como a tabela "produtos" existe de verdade no PostgreSQL,
usando SQLAlchemy. Cada instância de ProdutoORM é uma linha da tabela.
"""

from sqlalchemy import Column, Integer, String

from app.db import Base


class ProdutoORM(Base):
    __tablename__ = "produtos"

    codigo = Column(String, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    quantidade = Column(Integer, nullable=False)
