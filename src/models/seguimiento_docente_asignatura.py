from typing import List, Optional
from pydantic import BaseModel, Field

class SeguimientoDocenteAsignatura(BaseModel):
    Docente: str
    Asignatura: str
    Semestre: str
    Cantidad_Grupos: int = Field(..., alias='Cantidad Grupos')
    Numero_Estudiantes: int = Field(..., alias='Numero Estudiantes')
    Puntaje_Claridad: float = Field(..., alias='Puntaje Claridad')
    Puntaje_Metodología: float = Field(..., alias='Puntaje Metodología')
    Puntaje_Evaluación: float = Field(..., alias='Puntaje Evaluación')
    Comentarios: List[str]
    Horas_Lectivas: int = Field(..., alias='Horas Lectivas')
    Estudiantes_Aprobados: int = Field(..., alias='Estudiantes Aprobados')
    Comentarios_Estables: int = Field(..., alias='Comentarios Estables')
    Comentarios_En_Riesgo: int = Field(..., alias='Comentarios En Riesgo')
    Comentarios_En_Mejora: int = Field(..., alias='Comentarios En Mejora')
    Semestres_Desde_Ultima_Calificación: Optional[int] = Field(
        ..., alias='Semestres Desde Ultima Calificación'
    )
    Reingreso: Optional[bool]
    Indice_Reingreso: Optional[float] = Field(..., alias='Indice Reingreso')
