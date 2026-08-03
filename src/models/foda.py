from typing import List
from pydantic import BaseModel, Field

class Foda(BaseModel):
    Fortalezas: List[str]
    Oportunidades: List[str]
    Debilidades_Y_Amenazas: List[str] = Field(..., alias='Debilidades y Amenazas')
