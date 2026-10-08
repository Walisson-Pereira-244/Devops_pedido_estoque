
from sqlalchemy import Column, Integer, String

from app.db import Base


class PedidoORM(Base):
    __tablename__ = "pedidos"

    id = Column(String, primary_key=True, index=True)
    codigo_produto = Column(String, nullable=False)
    quantidade = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
