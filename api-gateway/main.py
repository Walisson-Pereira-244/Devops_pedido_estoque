
import os

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="API Gateway")

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
PEDIDO_SERVICE_URL = os.getenv("PEDIDO_SERVICE_URL", "http://pedido-service:8000")
ESTOQUE_SERVICE_URL = os.getenv("ESTOQUE_SERVICE_URL", "http://estoque-service:8000")


ROTAS_PUBLICAS = {"/login", "/health"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "api-gateway"}


async def validar_token(request: Request):
   
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não informado")

    token = auth_header.split(" ", 1)[1]

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{AUTH_SERVICE_URL}/validate", params={"token": token})

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


async def encaminhar(request: Request, destino_base: str, caminho: str):
    
    url = f"{destino_base}{caminho}"
    body = await request.body()

    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method=request.method,
            url=url,
            content=body,
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            params=request.query_params,
        )

    return JSONResponse(status_code=resp.status_code, content=resp.json() if resp.content else {})



@app.post("/login")
async def login(request: Request):
    return await encaminhar(request, AUTH_SERVICE_URL, "/login")



@app.api_route("/pedidos", methods=["POST"])
async def criar_pedido(request: Request):
    await validar_token(request)
    return await encaminhar(request, PEDIDO_SERVICE_URL, "/pedidos")


@app.api_route("/pedidos/{pedido_id}", methods=["GET"])
async def consultar_pedido(pedido_id: str, request: Request):
    await validar_token(request)
    return await encaminhar(request, PEDIDO_SERVICE_URL, f"/pedidos/{pedido_id}")


@app.api_route("/pedidos/{pedido_id}/cancelar", methods=["PUT"])
async def cancelar_pedido(pedido_id: str, request: Request):
    await validar_token(request)
    return await encaminhar(request, PEDIDO_SERVICE_URL, f"/pedidos/{pedido_id}/cancelar")



@app.api_route("/produtos", methods=["POST"])
async def cadastrar_produto(request: Request):
    await validar_token(request)
    return await encaminhar(request, ESTOQUE_SERVICE_URL, "/produtos")


@app.api_route("/produtos/{codigo}", methods=["GET"])
async def consultar_produto(codigo: str, request: Request):
    await validar_token(request)
    return await encaminhar(request, ESTOQUE_SERVICE_URL, f"/produtos/{codigo}")


@app.api_route("/estoque/reservar", methods=["POST"])
async def reservar_estoque(request: Request):
    await validar_token(request)
    return await encaminhar(request, ESTOQUE_SERVICE_URL, "/estoque/reservar")


@app.api_route("/estoque/estornar", methods=["POST"])
async def estornar_estoque(request: Request):
    await validar_token(request)
    return await encaminhar(request, ESTOQUE_SERVICE_URL, "/estoque/estornar")
