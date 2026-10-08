import requests

from app.config import ESTOQUE_SERVICE_URL


def reservar_no_estoque(codigo_produto: str, quantidade: int) -> requests.Response:
    return requests.post(
        f"{ESTOQUE_SERVICE_URL}/estoque/reservar",
        json={"codigo": codigo_produto, "quantidade": quantidade},
        timeout=5,
    )


def estornar_no_estoque(codigo_produto: str, quantidade: int) -> requests.Response:
    return requests.post(
        f"{ESTOQUE_SERVICE_URL}/estoque/estornar",
        json={"codigo": codigo_produto, "quantidade": quantidade},
        timeout=5,
    )
