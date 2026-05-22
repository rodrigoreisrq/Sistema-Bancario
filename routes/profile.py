import os
import jwt
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User, TutorProfile
from schemas import ProfileUpdateRequest, ProfileResponse, TutorProfileUpdateRequest, TutorProfileDetailResponse
from utils.response import success, error

router = APIRouter(prefix="/profile", tags=["Profile"])

SECRET_KEY = os.getenv("SECRET_KEY", "chave-secreta-provisoria")

def get_current_user(db: Session = Depends(get_db), authorization: str = Header(None)):
    """Extrai usuário do token JWT no header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    try:
        # Remover "Bearer " do token se presente
        token = authorization
        if token.startswith("Bearer "):
            token = token[7:]
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado"
        )
    
    return user


@router.get("/")
def get_profile(
    current_user: User = Depends(get_current_user)
):
    """Retorna perfil do usuário autenticado"""
    
    return success(
        data={
            "id": str(current_user.id),
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "credits": current_user.credits,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        },
        message="Perfil carregado com sucesso!"
    )


@router.put("/")
def update_profile(
    data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza perfil do usuário autenticado"""
    
    # Se nome foi fornecido, atualizar
    if data.name is not None:
        current_user.name = data.name
    
    # Se email foi fornecido, validar duplicidade
    if data.email is not None:
        email_lower = data.email.lower()
        
        # Verificar se email já existe (e não é o do próprio usuário)
        existing = db.query(User).filter(
            User.email == email_lower,
            User.id != current_user.id
        ).first()
        
        if existing:
            return error(
                "Este e-mail já está em uso.",
                status_code=409
            )
        
        current_user.email = email_lower
    
    db.commit()
    db.refresh(current_user)
    
    return success(
        data={
            "id": str(current_user.id),
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "credits": current_user.credits,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        },
        message="Perfil atualizado com sucesso!"
    )


@router.put("/tutor")
def update_tutor_profile(
    data: TutorProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza perfil do tutor autenticado"""
    
    # Verificar se usuário é tutor
    if current_user.role != "TUTOR":
        return error(
            "Apenas tutores podem editar este perfil.",
            status_code=403
        )
    
    # Buscar perfil do tutor
    tutor_profile = db.query(TutorProfile).filter(
        TutorProfile.user_id == current_user.id
    ).first()
    
    if not tutor_profile:
        return error(
            "Perfil do tutor não encontrado",
            status_code=404
        )
    
    # Se bio foi fornecida, atualizar
    if data.bio is not None:
        tutor_profile.bio = data.bio.strip()
    
    # Se tecnologias foram fornecidas, atualizar
    if data.technologies is not None:
        tutor_profile.technologies = [t.strip() for t in data.technologies]
    
    # Se is_online foi fornecido, atualizar
    if data.is_online is not None:
        tutor_profile.is_online = data.is_online
    
    db.commit()
    db.refresh(tutor_profile)
    
    return success(
        data={
            "user_id": str(current_user.id),
            "user_name": current_user.name,
            "bio": tutor_profile.bio,
            "technologies": tutor_profile.technologies,
            "is_online": tutor_profile.is_online,
            "rating": tutor_profile.rating
        },
        message="Perfil do tutor atualizado com sucesso!"
    )

