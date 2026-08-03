from pydantic import BaseModel

class SentimientoClasificado(BaseModel):
    sentimiento: str
    label: str
    score: float
