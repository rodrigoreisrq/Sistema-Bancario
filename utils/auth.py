import os
import jwt
from fastapi import HTTPException, Header

SECRET_KEY = os.getenv("SECRET_KEY", "chave-secreta-provisoria")


def get_current_user(authorization: str = Header(None)) -> dict:
    """
    Lê o JWT do header Authorization e retorna o payload.
    Uso: current_user: dict = Depends(get_current_user)
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente.")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Formato inválido. Use: Bearer <token>")

    try:
        payload = jwt.decode(parts[1], SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido.")
