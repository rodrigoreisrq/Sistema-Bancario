import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Float, Text, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from database import Base


class User(Base):
    __tablename__ = "users"

    id            = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name          = Column(String, nullable=False)
    email         = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role          = Column(String, nullable=False)
    credits       = Column(Integer, default=5)
    created_at    = Column(DateTime, default=datetime.utcnow)


class TutorProfile(Base):
    __tablename__ = "tutor_profiles"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id      = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    bio          = Column(Text, default="Sem bio informada.")
    technologies = Column(ARRAY(String), default=list)
    is_online    = Column(Boolean, default=False)
    rating       = Column(Float, default=0.0)
    created_at   = Column(DateTime, default=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id                    = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id            = Column(String, ForeignKey("users.id"), nullable=False)
    tutor_id              = Column(String, ForeignKey("users.id"), nullable=False)
    status                = Column(String, nullable=False, default="pending")
    notes                 = Column(String(200), nullable=True)
    cancellation_reason   = Column(Text, nullable=True)
    created_at            = Column(DateTime, default=datetime.utcnow)
    updated_at            = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at             = Column(DateTime, nullable=True)


class SessionReport(Base):
    __tablename__ = "session_reports"

    id                  = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id          = Column(String, ForeignKey("sessions.id"), nullable=False, unique=True)
    tutor_id            = Column(String, ForeignKey("users.id"), nullable=False)
    content             = Column(Text, nullable=False)
    duration_minutes    = Column(Integer, nullable=True)
    student_performance = Column(String, default="not_rated")
    notes               = Column(Text, nullable=True)
    created_at          = Column(DateTime, default=datetime.utcnow)
    updated_at          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Review(Base):
    __tablename__ = "reviews"

    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False, unique=True)
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    tutor_id   = Column(String, ForeignKey("users.id"), nullable=False)
    rating     = Column(Integer, nullable=False)   # 1 a 5
    comment    = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
