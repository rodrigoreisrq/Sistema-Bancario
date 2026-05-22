from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import Session as SessionModel, Review, TutorProfile
from schemas import ReviewCreate, ReviewResponse, TutorRatingResponse
from utils.auth import get_current_user
from utils.response import success, error

router = APIRouter(prefix="/sessions", tags=["Reviews"])


# ─────────────────────────────────────────────────────────────
# POST /sessions/{id}/review
# Tutorado avalia o tutor após encerramento
# ─────────────────────────────────────────────────────────────
@router.post("/{session_id}/review", status_code=201)
def create_review(
    session_id: str,
    body: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    student_id = current_user["user_id"]

    # 1. Busca a sessão
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        return error("Sessão não encontrada.", status_code=404)

    # 2. Apenas o tutorado da sessão pode avaliar
    if session.student_id != student_id:
        return error("Apenas o tutorado da sessão pode avaliar.", status_code=403)

    # 3. Só pode avaliar sessão encerrada
    if session.status != "closed":
        return error(
            f"Só é possível avaliar sessões encerradas. Status atual: {session.status}",
            status_code=400
        )

    # 4. Unicidade — 1 review por sessão
    existing = db.query(Review).filter(Review.session_id == session_id).first()
    if existing:
        return error("Esta sessão já foi avaliada.", status_code=409)

    # 5. Cria a review
    review = Review(
        session_id=session_id,
        student_id=student_id,
        tutor_id=session.tutor_id,
        rating=body.rating,
        comment=body.comment
    )
    db.add(review)

    # 6. Recalcula média do tutor sob demanda
    db.flush()  # garante que a review está visível na query abaixo

    avg = db.query(func.avg(Review.rating)).filter(
        Review.tutor_id == session.tutor_id
    ).scalar()

    tutor_profile = db.query(TutorProfile).filter(
        TutorProfile.user_id == session.tutor_id
    ).first()

    if tutor_profile and avg is not None:
        tutor_profile.rating = round(float(avg), 2)

    db.commit()
    db.refresh(review)

    return success(
        data={
            "id":         review.id,
            "session_id": review.session_id,
            "student_id": review.student_id,
            "tutor_id":   review.tutor_id,
            "rating":     review.rating,
            "comment":    review.comment,
            "created_at": str(review.created_at),
            "tutor_new_rating": tutor_profile.rating if tutor_profile else None
        },
        message="Avaliação enviada com sucesso!",
        status_code=201
    )


# ─────────────────────────────────────────────────────────────
# GET /sessions/{id}/review
# Ver avaliação de uma sessão
# ─────────────────────────────────────────────────────────────
@router.get("/{session_id}/review")
def get_review(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        return error("Sessão não encontrada.", status_code=404)

    uid = current_user["user_id"]
    if session.student_id != uid and session.tutor_id != uid:
        return error("Sem permissão para ver esta avaliação.", status_code=403)

    review = db.query(Review).filter(Review.session_id == session_id).first()
    if not review:
        return error("Esta sessão ainda não foi avaliada.", status_code=404)

    return success(data={
        "id":         review.id,
        "session_id": review.session_id,
        "student_id": review.student_id,
        "tutor_id":   review.tutor_id,
        "rating":     review.rating,
        "comment":    review.comment,
        "created_at": str(review.created_at)
    })


# ─────────────────────────────────────────────────────────────
# GET /tutors/{tutor_id}/rating
# Média de avaliações do tutor sob demanda
# ─────────────────────────────────────────────────────────────
@router.get("/tutors/{tutor_id}/rating")
def get_tutor_rating(
    tutor_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    total = db.query(func.count(Review.id)).filter(Review.tutor_id == tutor_id).scalar()
    avg   = db.query(func.avg(Review.rating)).filter(Review.tutor_id == tutor_id).scalar()

    return success(data={
        "tutor_id":      tutor_id,
        "average_rating": round(float(avg), 2) if avg else 0.0,
        "total_reviews":  total or 0
    })
