import datetime

from sqlalchemy import String, Text, Integer, Float, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Clase(Base):
    __tablename__ = "clases"

    # Primary & Indexed keys
    id_curso_grupo: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    id_docente: Mapped[str] = mapped_column(String(100), index=True)
    asignatura: Mapped[str] = mapped_column(String(100), index=True)
    semestre: Mapped[str] = mapped_column(String(10), index=True)

    numero_estudiantes: Mapped[int] = mapped_column(Integer)
    puntaje_claridad: Mapped[float] = mapped_column(Float)
    puntaje_metodologia: Mapped[float] = mapped_column(Float)
    puntaje_evaluacion: Mapped[float] = mapped_column(Float)

    # PostgreSQL Text field
    comentario: Mapped[str] = mapped_column(Text)

    # Metadata and schedules
    tendencia_desempeno: Mapped[str] = mapped_column(String(10))
    clases_pactadas: Mapped[int] = mapped_column(Integer)
    clases_dictadas: Mapped[int] = mapped_column(Integer)
    dias_clase: Mapped[str] = mapped_column(String(100))

    # Time limits
    hora_inicio: Mapped[datetime.time] = mapped_column(Time())
    hora_fin: Mapped[datetime.time] = mapped_column(Time())
    franja_horaria: Mapped[str] = mapped_column(String(10))

    # Performance numbers
    promedio_asistencias_estudiantes: Mapped[float] = mapped_column(Float)
    numero_estudiantes_aprobaron: Mapped[int] = mapped_column(Integer)
    numero_estudiantes_perdieron: Mapped[int] = mapped_column(Integer)
    numero_estudiantes_desistieron: Mapped[int] = mapped_column(Integer)
