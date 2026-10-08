import uuid

from sqlalchemy.orm import Session

from app import estoque_client
from app.enums import StatusPedido
from app.models import PedidoORM


class PedidoNaoEncontradoError(Exception):
    pass


def criar_pedido(db: Session, codigo_produto: str, quantidade: int) -> PedidoORM:
    pedido_id = str(uuid.uuid4())
    pedido = PedidoORM(
        id=pedido_id,
        codigo_produto=codigo_produto,
        quantidade=quantidade,
        status=StatusPedido.PENDENTE.value,
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)

    # tenta reservar no estoque-service via HTTP e tbm atualiza o status do pedido
    resposta = estoque_client.reservar_no_estoque(codigo_produto, quantidade)

    pedido.status = (
        StatusPedido.CONFIRMADO.value
        if resposta.status_code == 200
        else StatusPedido.CANCELADO.value
    )
    db.commit()
    db.refresh(pedido)
    return pedido


def consultar_pedido(db: Session, pedido_id: str) -> PedidoORM:
    pedido = db.get(PedidoORM, pedido_id)
    if pedido is None:
        raise PedidoNaoEncontradoError(f"Pedido {pedido_id} não encontrado")
    return pedido


def cancelar_pedido(db: Session, pedido_id: str) -> PedidoORM:
    pedido = consultar_pedido(db, pedido_id)

    if pedido.status == StatusPedido.CONFIRMADO.value:
        # C1 da Saga: compensação, desfaz a reserva feita no estoque-service
        estoque_client.estornar_no_estoque(pedido.codigo_produto, pedido.quantidade)

    pedido.status = StatusPedido.CANCELADO.value
    db.commit()
    db.refresh(pedido)
    return pedido
