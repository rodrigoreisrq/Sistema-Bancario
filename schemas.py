from pydantic import BaseModel, EmailStr, field_validator
from enum import Enum
from typing import List, Optional
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────

class RoleEnum(str, Enum):
    student = "STUDENT"
    tutor   = "TUTOR"

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: RoleEnum

    @field_validator('password')
    def senha_minima(cls, v):
        if len(v) < 8:
            raise ValueError('Senha deve ter no mínimo 8 caracteres.')
        return v

class RegisterResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    message: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    token: str
    user_id: str
    role: str


# ── Profile ───────────────────────────────────────────────────

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

    @field_validator('name')
    def nome_valido(cls, v):
        if v is not None and len(v.strip()) < 3:
            raise ValueError('Nome deve ter no mínimo 3 caracteres.')
        return v.strip() if v else v

class ProfileResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    credits: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Tutor Profile ────────────────────────────────────────────

class TutorProfileUpdateRequest(BaseModel):
    bio: Optional[str] = None
    technologies: Optional[List[str]] = None
    is_online: Optional[bool] = None

    @field_validator('bio')
    def bio_valido(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 10:
                raise ValueError('Bio deve ter no mínimo 10 caracteres.')
            if len(v) > 500:
                raise ValueError('Bio deve ter no máximo 500 caracteres.')
        return v

    @field_validator('technologies')
    def tecnologias_validas(cls, v):
        if v is not None:
            if len(v) == 0:
                raise ValueError('Deve selecionar pelo menos uma tecnologia.')
            if len(v) > 10:
                raise ValueError('Máximo 10 tecnologias permitidas.')
            if not all(isinstance(t, str) and len(t.strip()) > 0 for t in v):
                raise ValueError('Todas as tecnologias devem ser strings não vazias.')
        return v

class TutorProfileDetailResponse(BaseModel):
    user_id: str
    user_name: str
    bio: str
    technologies: List[str]
    is_online: bool
    rating: float

    class Config:
        from_attributes = True


# ── Tutors ────────────────────────────────────────────────────

class TutorResponse(BaseModel):
    id: str
    name: str
    bio: Optional[str]
    technologies: Optional[List[str]]
    is_online: bool
    rating: float

    class Config:
        from_attributes = True

class TutorListResponse(BaseModel):
    tutors: List[TutorResponse]
    total: int
    page: int
    page_size: int

class TutorDetailResponse(BaseModel):
    id: str
    name: str
    email: str
    bio: str
    technologies: List[str]
    is_online: bool
    rating: float
    total_sessions: int
    reviews_count: int

    class Config:
        from_attributes = True


# ── Sessions ──────────────────────────────────────────────────

class SessionCreate(BaseModel):
    tutor_id: str

class CancelSessionRequest(BaseModel):
    reason: Optional[str] = None

class SessionResponse(BaseModel):
    id:                  str
    student_id:          str
    tutor_id:            str
    status:              str
    created_at:          datetime
    updated_at:          Optional[datetime] = None
    closed_at:           Optional[datetime] = None
    cancellation_reason: Optional[str] = None

    class Config:
        from_attributes = True


# ── Session Reports ───────────────────────────────────────────

class StudentPerformanceEnum(str, Enum):
    excellent = "excellent"
    good      = "good"
    fair      = "fair"
    poor      = "poor"
    not_rated = "not_rated"

class CloseSessionRequest(BaseModel):
    content:             str
    duration_minutes:    Optional[int] = None
    student_performance: StudentPerformanceEnum = StudentPerformanceEnum.not_rated
    notes:               Optional[str] = None

    @field_validator("content")
    def content_minimo(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("O relatório deve ter no mínimo 10 caracteres.")
        return v.strip()

    @field_validator("duration_minutes")
    def duration_valida(cls, v):
        if v is not None and (v < 1 or v > 480):
            raise ValueError("Duração deve estar entre 1 e 480 minutos.")
        return v

class SessionReportResponse(BaseModel):
    id:                  str
    session_id:          str
    tutor_id:            str
    content:             str
    duration_minutes:    Optional[int]
    student_performance: str
    notes:               Optional[str]
    created_at:          datetime

    class Config:
        from_attributes = True


# ── Reviews ───────────────────────────────────────────────────

class ReviewCreate(BaseModel):
    rating:  int
    comment: Optional[str] = None

    @field_validator("rating")
    def rating_valido(cls, v):
        if v < 1 or v > 5:
            raise ValueError("A avaliação deve ser entre 1 e 5 estrelas.")
        return v

    @field_validator("comment")
    def comment_tamanho(cls, v):
        if v is not None and len(v.strip()) > 500:
            raise ValueError("O comentário deve ter no máximo 500 caracteres.")
        return v.strip() if v else v

class ReviewResponse(BaseModel):
    id:         str
    session_id: str
    student_id: str
    tutor_id:   str
    rating:     int
    comment:    Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class TutorRatingResponse(BaseModel):
    tutor_id:      str
    average_rating: float
    total_reviews:  int
