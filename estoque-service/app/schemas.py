"""
Camada de SCHEMAS.
Define o formato dos dados que a API espera RECEBER (request)
e o que ela vai DEVOLVER (response).
"""

from pydantic import BaseModel


class ProdutoCreate(BaseModel):
    codigo: str
    nome: str
    quantidade: int


class ReservaRequest(BaseModel):
    codigo: str
    quantidade: int


class EstornoRequest(BaseModel):
    codigo: str
    quantidade: int


class ProdutoResponse(BaseModel):
    """Schema de saída: converte o objeto ORM (ProdutoORM) em JSON."""

    codigo: str
    nome: str
    quantidade: int

    model_config = {"from_attributes": True}
