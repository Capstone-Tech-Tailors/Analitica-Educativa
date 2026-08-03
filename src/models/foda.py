from pydantic import BaseModel, Field

class Foda(BaseModel):
    Fortalezas: int
    Oportunidades: int
    Debilidades_Y_Amenazas: int = Field(..., alias='Debilidades y Amenazas')
