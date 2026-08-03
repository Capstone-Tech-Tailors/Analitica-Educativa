from pydantic import BaseModel

class ComentarioClasificado(BaseModel):
    comentario: str
    sentimiento: str
    probabilidad: float
