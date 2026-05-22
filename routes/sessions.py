from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User, TutorProfile, Session as SessionModel, SessionReport
from schemas import SessionCreate, CloseSessionRequest, CancelSessionRequest
from utils.auth import get_current_user
from utils.response import success, error

router = APIRouter(prefix="/sessions", tags=["Sessions"])


# ─────────────────────────────────────────────────────────────
# POST /sessions/
# Tutorado solicita sessão com um tutor
# ─────────────────────────────────────────────────────────────
@router.post("/", status_code=201)
def create_session(
    body: SessionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    student_id = current_user["user_id"]

    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        return error("Usuário não encontrado.", status_code=404)
    if student.credits < 1:
        return error("Créditos insuficientes para solicitar uma sessão.", status_code=402)

    tutor = db.query(User).filter(
        User.id == body.tutor_id,
        User.role == "TUTOR"
    ).first()
    if not tutor:
        return error("Tutor não encontrado.", status_code=404)

    tutor_profile = db.query(TutorProfile).filter(
        TutorProfile.user_id == body.tutor_id
    ).first()
    if not tutor_profile or not tutor_profile.is_online:
        return error("Tutor está offline no momento.", status_code=409)

    tutor_busy = db.query(SessionModel).filter(
        SessionModel.tutor_id == body.tutor_id,
        SessionModel.status.in_(["pending", "active"])
    ).first()
    if tutor_busy:
        return error("Tutor já está em uma sessão.", status_code=409)

    student_busy = db.query(SessionModel).filter(
        SessionModel.student_id == student_id,
        SessionModel.status.in_(["pending", "active"])
    ).first()
    if student_busy:
        return error("Você já possui uma sessão em andamento.", status_code=409)

    student.credits -= 1

    new_session = SessionModel(
        student_id=student_id,
        tutor_id=body.tutor_id,
        status="pending"
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return success(
        data={
            "id":                new_session.id,
            "student_id":        new_session.student_id,
            "tutor_id":          new_session.tutor_id,
            "status":            new_session.status,
            "created_at":        str(new_session.created_at),
            "credits_restantes": student.credits
        },
        message="Sessão solicitada com sucesso!",
        status_code=201
    )


# ─────────────────────────────────────────────────────────────
# PATCH /sessions/{id}/activate
# Tutor aceita e ativa a sessão (pending → active)
# ─────────────────────────────────────────────────────────────
@router.patch("/{session_id}/activate")
def activate_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()

    if not session:
        return error("Sessão não encontrada.", status_code=404)
    if session.tutor_id != current_user["user_id"]:
        return error("Apenas o tutor pode ativar esta sessão.", status_code=403)
    if session.status != "pending":
        return error(f"Sessão não pode ser ativada. Status atual: {session.status}", status_code=400)

    session.status = "active"
    db.commit()
    db.refresh(session)

    return success(
        data={
            "id":         session.id,
            "student_id": session.student_id,
            "tutor_id":   session.tutor_id,
            "status":     session.status,
            "created_at": str(session.created_at)
        },
        message="Sessão ativada com sucesso!"
    )


# ─────────────────────────────────────────────────────────────
# POST /sessions/{id}/close
# Tutor encerra com relatório obrigatório (active → closed)
# ─────────────────────────────────────────────────────────────
@router.post("/{session_id}/close", status_code=201)
def close_session(
    session_id: str,
    body: CloseSessionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()

    if not session:
        return error("Sessão não encontrada.", status_code=404)
    if session.tutor_id != current_user["user_id"]:
        return error("Apenas o tutor pode encerrar a sessão.", status_code=403)
    if session.status != "active":
        return error(
            f"Só é possível encerrar sessões em status 'active'. Status atual: {session.status}",
            status_code=400
        )

    now = datetime.utcnow()
    session.status     = "closed"
    session.closed_at  = now
    session.updated_at = now

    report = SessionReport(
        session_id=session_id,
        tutor_id=current_user["user_id"],
        content=body.content,
        duration_minutes=body.duration_minutes,
        student_performance=body.student_performance.value,
        notes=body.notes
    )
    db.add(report)
    db.commit()
    db.refresh(session)
    db.refresh(report)

    return success(
        data={
            "session": {
                "id":         session.id,
                "student_id": session.student_id,
                "tutor_id":   session.tutor_id,
                "status":     session.status,
                "closed_at":  str(session.closed_at)
            },
            "report": {
                "id":                  report.id,
                "content":             report.content,
                "duration_minutes":    report.duration_minutes,
                "student_performance": report.student_performance,
                "notes":               report.notes,
                "created_at":          str(report.created_at)
            }
        },
        message="Sessão encerrada com sucesso!",
        status_code=201
    )


# ─────────────────────────────────────────────────────────────
# PATCH /sessions/{id}/cancel
# Cancela uma sessão — tutor ou tutorado podem cancelar
# Devolve 1 crédito ao tutorado se a sessão ainda estava "pending"
# ─────────────────────────────────────────────────────────────
@router.patch("/{session_id}/cancel")
def cancel_session(
    session_id: str,
    body: CancelSessionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()

    if not session:
        return error("Sessão não encontrada.", status_code=404)

    uid = current_user["user_id"]
    if session.tutor_id != uid and session.student_id != uid:
        return error("Apenas tutor ou aluno podem cancelar esta sessão.", status_code=403)

    if session.status not in ["pending", "active"]:
        return error(
            f"Sessão com status '{session.status}' não pode ser cancelada.",
            status_code=400
        )

    # Devolve crédito se ainda estava "pending" (tutor não havia aceitado)
    credit_refunded = False
    if session.status == "pending":
        student = db.query(User).filter(User.id == session.student_id).first()
        if student:
            student.credits += 1
            credit_refunded = True

    # Agora muda o status
    session.status               = "canceled"
    session.cancellation_reason  = body.reason if body and body.reason else None
    session.updated_at           = datetime.utcnow()

    db.commit()
    db.refresh(session)

    return success(
        data={
            "id":                  session.id,
            "student_id":          session.student_id,
            "tutor_id":            session.tutor_id,
            "status":              session.status,
            "cancellation_reason": session.cancellation_reason,
            "credit_refunded":     credit_refunded,
            "updated_at":          str(session.updated_at)
        },
        message="Sessão cancelada com sucesso!"
    )


# ─────────────────────────────────────────────────────────────
# GET /sessions/
# Lista sessões do usuário logado
# ─────────────────────────────────────────────────────────────
@router.get("/")
def list_sessions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    uid  = current_user["user_id"]
    role = current_user["role"]

    if role == "TUTOR":
        sessions = db.query(SessionModel).filter(
            SessionModel.tutor_id == uid
        ).order_by(SessionModel.created_at.desc()).all()
    else:
        sessions = db.query(SessionModel).filter(
            SessionModel.student_id == uid
        ).order_by(SessionModel.created_at.desc()).all()

    return success(data=[
        {
            "id":                  s.id,
            "student_id":          s.student_id,
            "tutor_id":            s.tutor_id,
            "status":              s.status,
            "created_at":          str(s.created_at),
            "updated_at":          str(s.updated_at),
            "closed_at":           str(s.closed_at) if s.closed_at else None,
            "cancellation_reason": s.cancellation_reason
        }
        for s in sessions
    ])


# ─────────────────────────────────────────────────────────────
# GET /sessions/{id}
# Detalhes de uma sessão específica
# ─────────────────────────────────────────────────────────────
@router.get("/{session_id}")
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()\

    if not session:
        return error("Sessão não encontrada.", status_code=404)

    uid = current_user["user_id"]
    if session.tutor_id != uid and session.student_id != uid:
        return error("Sem permissão para ver esta sessão.", status_code=403)

    tutor = db.query(User).filter(User.id == session.tutor_id).first()
    tutor_profile = db.query(TutorProfile).filter(
        TutorProfile.user_id == session.tutor_id
    ).first() if tutor else None

    return success(data={
        "id":                  session.id,
        "student_id":          session.student_id,
        "tutor_id":            session.tutor_id,
        "tutor_name":          tutor.name if tutor else None,
        "tutor_technologies":  tutor_profile.technologies if tutor_profile else [],
        "status":              session.status,
        "created_at":          str(session.created_at),
        "updated_at":          str(session.updated_at),
        "closed_at":           str(session.closed_at) if session.closed_at else None,
        "cancellation_reason": session.cancellation_reason,
        "notes":               session.notes
    })
