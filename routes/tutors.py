from fastapi import APIRouter, Depends, Query, Header, HTTPException, status, Path
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from database import get_db
from models import User, TutorProfile, Session as SessionModel, Review
from utils.response import success, error
from typing import List, Optional
import os
import jwt

router = APIRouter(prefix="/tutors", tags=["Tutors"])

SECRET_KEY = os.getenv("SECRET_KEY", "chave-secreta-provisoria")

def get_current_user(db: Session = Depends(get_db), authorization: str = Header(None)):
    """Extrai usuário do token JWT no header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    try:
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
def list_tutors(
    db: Session = Depends(get_db),
    online_only: bool = Query(False, description="Filtrar apenas tutores online"),
    search: str = Query(None, description="Buscar por nome ou tecnologia"),
    technologies: Optional[List[str]] = Query(None, description="Filtrar por tecnologias (múltiplas selecionáveis)"),
    page: int = Query(1, ge=1, description="Página atual"),
    page_size: int = Query(10, ge=1, le=50, description="Itens por página")
):
    query = (
        db.query(User, TutorProfile)
        .join(TutorProfile, TutorProfile.user_id == User.id)
        .filter(User.role == "TUTOR")
    )

    # Filtro online
    if online_only:
        query = query.filter(TutorProfile.is_online == True)

    # Busca por nome ou tecnologia
    if search:
        query = query.filter(
            User.name.ilike(f"%{search}%") |
            TutorProfile.technologies.any(search)
        )

    # Filtro por tecnologias (múltiplas)
    if technologies:
        tech_filters = [TutorProfile.technologies.any(tech) for tech in technologies]
        query = query.filter(or_(*tech_filters))

    # Total antes de paginar
    total = query.count()

    # Paginação
    tutors = query.offset((page - 1) * page_size).limit(page_size).all()

    data = {
        "tutors": [
            {
                "id": str(user.id),
                "name": user.name,
                "bio": profile.bio,
                "technologies": profile.technologies,
                "is_online": profile.is_online,
                "rating": profile.rating
            }
            for user, profile in tutors
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }

    return success(data=data, message="Tutores listados com sucesso!")


@router.get("/available")
def list_available_tutors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: str = Query(None, description="Buscar por nome ou tecnologia"),
    technologies: Optional[List[str]] = Query(None, description="Filtrar por tecnologias"),
    page: int = Query(1, ge=1, description="Página atual"),
    page_size: int = Query(10, ge=1, le=50, description="Itens por página")
):
    """Retorna apenas tutores disponíveis (online) - Requer autenticação"""
    
    query = (
        db.query(User, TutorProfile)
        .join(TutorProfile, TutorProfile.user_id == User.id)
        .filter(User.role == "TUTOR")
        .filter(TutorProfile.is_online == True)  # Apenas online
    )
    
    # Busca por nome ou tecnologia
    if search:
        query = query.filter(
            User.name.ilike(f"%{search}%") |
            TutorProfile.technologies.any(search)
        )
    
    # Filtro por tecnologias (múltiplas)
    if technologies:
        tech_filters = [TutorProfile.technologies.any(tech) for tech in technologies]
        query = query.filter(or_(*tech_filters))
    
    # Total antes de paginar
    total = query.count()
    
    # Paginação
    tutors = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Mensagem baseada em resultado
    message = (
        "Nenhum tutor disponível no momento." if total == 0
        else "Tutores disponíveis carregados com sucesso!"
    )
    
    data = {
        "tutors": [
            {
                "id": str(user.id),
                "name": user.name,
                "bio": profile.bio,
                "technologies": profile.technologies,
                "rating": profile.rating
            }
            for user, profile in tutors
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }
    
    return success(data=data, message=message)


@router.get("/{tutor_id}")
def get_tutor_detail(
    tutor_id: str = Path(..., description="UUID do tutor"),
    db: Session = Depends(get_db)
):
    """Retorna perfil detalhado de um tutor"""
    
    # Buscar usuário tutor
    user = db.query(User).filter(
        User.id == tutor_id,
        User.role == "TUTOR"
    ).first()
    
    if not user:
        return error("Tutor não encontrado", status_code=404)
    
    # Buscar perfil do tutor
    tutor_profile = db.query(TutorProfile).filter(
        TutorProfile.user_id == tutor_id
    ).first()
    
    if not tutor_profile:
        return error("Tutor profile not found", status_code=404)
    
    # Contar sessões completadas
    total_sessions = db.query(func.count(SessionModel.id)).filter(
        SessionModel.tutor_id == tutor_id,
        SessionModel.status == "completed"
    ).scalar() or 0
    
    # Contar reviews
    reviews_count = db.query(func.count(Review.id)).filter(
        Review.tutor_id == tutor_id
    ).scalar() or 0
    
    return success(
        data={
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "bio": tutor_profile.bio,
            "technologies": tutor_profile.technologies,
            "is_online": tutor_profile.is_online,
            "rating": tutor_profile.rating,
            "total_sessions": total_sessions,
            "reviews_count": reviews_count
        },
        message="Perfil do tutor carregado com sucesso!"
    )