from __future__ import annotations

from pydantic import BaseModel, Field


class SeguimientoAsignaturas(BaseModel):
    Asignatura: str
    Semestre: str
    Cantidad_Docentes: int = Field(..., alias='Cantidad Docentes')
    Cantidad_Grupos: int = Field(..., alias='Cantidad Grupos')
    Numero_Estudiantes: int = Field(..., alias='Numero Estudiantes')
    Asistencia_Típica_Estudiantes: float = Field(
        ..., alias='Asistencia Típica Estudiantes'
    )
    Horas_Lectivas: int = Field(..., alias='Horas Lectivas')
    Estudiantes_Aprobados: int = Field(..., alias='Estudiantes Aprobados')
    Estudiantes_Perdieron: int = Field(..., alias='Estudiantes Perdieron')
    Estudiantes_Desistieron: int = Field(..., alias='Estudiantes Desistieron')
    Clases_Dictadas: int = Field(..., alias='Clases Dictadas')
