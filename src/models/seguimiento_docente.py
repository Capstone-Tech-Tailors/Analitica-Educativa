from typing import List
from pydantic import BaseModel, Field

class SeguimientoDocente(BaseModel):
    Docente: str
    Semestre: str
    Cantidad_Asignaturas: int = Field(..., alias='Cantidad Asignaturas')
    Cantidad_Grupos: int = Field(..., alias='Cantidad Grupos')
    Numero_Estudiantes: int = Field(..., alias='Numero Estudiantes')
    Asignaturas: List[str]
    Horas_Lectivas: int = Field(..., alias='Horas Lectivas')
    Comentarios_Estables: int = Field(..., alias='Comentarios Estables')
    Comentarios_En_Riesgo: int = Field(..., alias='Comentarios En Riesgo')
    Comentarios_En_Mejora: int = Field(..., alias='Comentarios En Mejora')
    Cantidad_Semestres_sin_Sobrecarga_de_Asignaturas: int = Field(
        ..., alias='Cantidad Semestres sin Sobrecarga de Asignaturas'
    )
    Cantidad_Semestres_sin_Sobrecarga_de_Grupos: int = Field(
        ..., alias='Cantidad Semestres sin Sobrecarga de Grupos'
    )
    Cantidad_Semestres_sin_Sobrecarga_Horaria: int = Field(
        ..., alias='Cantidad Semestres sin Sobrecarga Horaria'
    )
    Indice_Carga_Asignaturas: float = Field(..., alias='Indice Carga Asignaturas')
    Indice_Carga_Grupos: float = Field(..., alias='Indice Carga Grupos')
    Indice_Carga_Horaria: float = Field(..., alias='Indice Carga Horaria')
