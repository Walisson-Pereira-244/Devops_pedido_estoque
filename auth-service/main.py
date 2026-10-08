"""
Auth Service
Responsável por autenticar usuários e emitir tokens JWT.
Endpoint: POST /login
"""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Auth Service")


SECRET_KEY = "chave-secreta-super-simples-para-o-projeto"
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 60


FAKE_USERS_DB = {
    "admin": "123456",
    "cliente1": "senha123",
}


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.get("/health")
def health():
    return {"status": "ok", "service": "auth-service"}


@app.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    senha_correta = FAKE_USERS_DB.get(payload.username)

    if senha_correta is None or senha_correta != payload.password:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")

    expira_em = datetime.now(timezone.utc) + timedelta(minutes=EXPIRATION_MINUTES)
    claims = {
        "sub": payload.username,
        "exp": expira_em,
    }
    token = jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)

    return TokenResponse(access_token=token)



@app.get("/validate")
def validate(token: str):
    try:
        claims = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"valid": True, "user": claims.get("sub")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
