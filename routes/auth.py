import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, TutorProfile
from schemas import RegisterRequest, LoginRequest
from utils.response import success, error

router = APIRouter(prefix="/auth", tags=["Auth"])

SECRET_KEY = os.getenv("SECRET_KEY", "chave-secreta-provisoria")

@router.post("/register", status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):

    existing = db.query(User).filter(User.email == data.email.lower()).first()
    if existing:
        return error("E-mail já cadastrado.", status_code=409)

    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()

    new_user = User(
        name=data.name,
        email=data.email.lower(),
        password_hash=hashed,
        role=data.role.value
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if new_user.role == "TUTOR":
        tutor = TutorProfile(user_id=new_user.id)
        db.add(tutor)
        db.commit()

    return success(
        data={
            "id": str(new_user.id),      # ← str() aqui
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role
        },
        message="Usuário cadastrado com sucesso!",
        status_code=201
    )

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user:
        return error("Credenciais inválidas.", status_code=401)

    if not bcrypt.checkpw(data.password.encode(), user.password_hash.encode()):
        return error("Credenciais inválidas.", status_code=401)

    payload = {
        "user_id": str(user.id),
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(hours=2)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return success(data={"token": token, "user_id": str(user.id), "role": user.role})