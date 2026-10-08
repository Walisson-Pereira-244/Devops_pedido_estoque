"""
Camada de CONTROLLER/ROTAS.
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app import service
from app.db import get_db, init_db
from app.schemas import EstornoRequest, ProdutoCreate, ProdutoResponse, ReservaRequest


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cria as tabelas no Postgres assim que a aplicação sobe."""
    init_db()
    yield


app = FastAPI(title="Estoque Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/produtos", status_code=201, response_model=ProdutoResponse)
def criar_produto(produto: ProdutoCreate, db: Session = Depends(get_db)):
    """RF04 - Cadastro de Produto."""
    return service.cadastrar_produto(
        db, codigo=produto.codigo, nome=produto.nome, quantidade=produto.quantidade
    )


@app.get("/produtos/{codigo}", response_model=ProdutoResponse)
def obter_produto(codigo: str, db: Session = Depends(get_db)):
    try:
        return service.consultar_produto(db, codigo)
    except service.ProdutoNaoEncontradoError as erro:
        raise HTTPException(status_code=404, detail=str(erro))


@app.post("/estoque/reservar")
def reservar(reserva: ReservaRequest, db: Session = Depends(get_db)):
    """RF05 - Reserva de Estoque. 200 se houver saldo, 400 se não."""
    try:
        produto = service.reservar_estoque(db, reserva.codigo, reserva.quantidade)
        return {"status": "reservado", "produto": ProdutoResponse.model_validate(produto)}
    except service.ProdutoNaoEncontradoError as erro:
        raise HTTPException(status_code=404, detail=str(erro))
    except service.EstoqueInsuficienteError as erro:
        raise HTTPException(status_code=400, detail=str(erro))


@app.post("/estoque/estornar")
def estornar(estorno: EstornoRequest, db: Session = Depends(get_db)):
    """RF06 - Estorno de Estoque (ação compensatória da Saga)."""
    try:
        produto = service.estornar_estoque(db, estorno.codigo, estorno.quantidade)
        return {"status": "estornado", "produto": ProdutoResponse.model_validate(produto)}
    except service.ProdutoNaoEncontradoError as erro:
        raise HTTPException(status_code=404, detail=str(erro))
