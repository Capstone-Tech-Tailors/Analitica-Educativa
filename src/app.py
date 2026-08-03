import tempfile
import aiofiles
import logging
import pandas as pd
import platformdirs
import torch

from fastapi import FastAPI, UploadFile, Depends, HTTPException, BackgroundTasks, Response, Body, status
from db.session import get_session as db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select, func, distinct, case, text
from aiofiles import os as asyncos
from contextlib import asynccontextmanager

from models.clase import Clase
from models.seguimiento_docente import SeguimientoDocente
from models.seguimiento_asignaturas import SeguimientoAsignaturas
from models.seguimiento_docente_asignatura import SeguimientoDocenteAsignatura

from models.comentario_clasificado import ComentarioClasificado
from models.foda import Foda
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

from utils import (
    agregar_metricas_generales_docente,
    completar_semestres, agregar_metricas_docente_por_asignatura,
    period_to_string
)

gunicorn_logger = logging.getLogger("gunicorn.error")
logger = logging.getLogger("uvicorn.error")
logger.handlers = gunicorn_logger.handlers
logger.setLevel(gunicorn_logger.level)


ml_models = dict()

@asynccontextmanager
async def lifespan(app: FastAPI):

    HF_DEVICE = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    HF_MAX_LEN = 64

    models_directory = (platformdirs.user_publicshare_path() / "ml_models")
    models_directory.mkdir(parents=True, exist_ok=True)
    
    modelo_sentimientos_path = (models_directory / "sentimientos")
    if modelo_sentimientos_path.exists() and any(modelo_sentimientos_path.iterdir()):

        try:
            tokenizador_disco = AutoTokenizer.from_pretrained(modelo_sentimientos_path)
            modelo_disco = AutoModelForSequenceClassification.from_pretrained(modelo_sentimientos_path)
            ml_models["sentimientos"] = pipeline(
                "sentiment-analysis", model=modelo_disco, tokenizer=tokenizador_disco,
                device=HF_DEVICE, truncation=True, max_length=HF_MAX_LEN
            )
        except Exception as ex:
            logger.exception("Error al cargar modelo de sentimientos")

    yield
    ml_models.clear()

app = FastAPI(title="Analítica Académica", lifespan=lifespan)

@app.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Confirms the FastAPI application process is up."""
    return {"status": "online"}

@app.get("/health/ready")
async def readiness_probe(response: Response, db: AsyncSession = Depends(db_session)):
    """Verifies database readiness."""
    try:
        result = await db.scalar(text("SELECT 1"))
        if result == 1:
            return {"status": "healthy", "database": "ok"}
    except Exception:
        logger.error(f"Database is unreachable or unavailable.")

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "unhealthy", "database": "down"}

@app.post("/predecir_sentimientos")
def predecir_sentimientos(comentarios: list[str] | str | None = Body(default=None)) -> list[ComentarioClasificado]:
    if "sentimientos" not in ml_models:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Modelo no fue encontrado en el Almacenamiento")
    
    if not comentarios:
        raise HTTPException(status_code=400, detail="Debe mandar los comentarios de los estudiantes")
    
    clasificaciones = ml_models["sentimientos"](comentarios)
    pretty_labels = {
        "NEG": "En riesgo",
        "NEU": "Estable",
        "POS": "Mejora"
    }
    
    response = []
    for idx, clasificacion in enumerate(clasificaciones):
        response.append({
            "comentario": comentarios[idx] if len(clasificaciones) > 1 else comentarios,
            "sentimiento": pretty_labels[clasificaciones["label"]],
            "probabilidad": clasificaciones["score"]
        })

    return response

@app.post("/analisis_foda")
def analisis_foda(comentarios: list[str]) -> list[Foda]:
    data = pd.DataFrame(predecir_sentimientos(comentarios))
    foda = data.groupby(["sentimiento"]).agg(
        Comentarios=("comentario", lambda x: tuple(x.dropna().unique()))
    )
    return {
        "Fortalezas": list(foda.loc["Mejora", "Comentarios"]),
        "Oportunidades": list(foda.loc["Estable", "Comentarios"]),
        "Debilidades y Amenazas": list(foda.loc["En riesgo", "Comentarios"])
    }

async def bulk_update(csv_file: str, db: AsyncSession):
    campos_clase = Clase.__table__.columns.keys()

    with pd.read_csv(csv_file, sep=",", encoding="utf-8", header="infer", chunksize=500) as reader:
        for chunk in reader:
            if chunk.empty:
                continue
            try:
                chunk.drop_duplicates(subset="id_curso_grupo", keep="first", inplace=True)
                chunk["hora_inicio"] = chunk["hora_inicio"].apply(lambda val: pd.to_datetime(val, format="%H:%M").time())
                chunk["hora_fin"] = chunk["hora_fin"].apply(lambda val: pd.to_datetime(val, format="%H:%M").time())
                data = chunk[campos_clase].to_dict(orient="records")
                insert_stmt = pg_insert(Clase).values(data)
                upsert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=["id_curso_grupo"],
                    set_={
                        campo: insert_stmt.excluded[campo]
                        for campo in campos_clase if campo != "id_curso_grupo"
                    }
                )
                await db.execute(upsert_stmt)
                await db.commit()
            except Exception:
                logger.error("Bulk update error", exc_info=True)
                await db.rollback()

    await asyncos.remove(csv_file)

@app.post("/etl")
async def etl(file: UploadFile, background_tasks: BackgroundTasks, db: AsyncSession = Depends(db_session)):
    if not file.filename.endswith('.csv'):
        logger.error("Archivo subido NO fue un CSV")
        raise HTTPException(status_code=400, detail="File must be a CSV.")

    file_path: str = ""
    with tempfile.NamedTemporaryFile(delete=False, dir=tempfile.gettempdir()) as temp_file:

        async with aiofiles.open(temp_file.name, "wb") as out_file:
            while content := await file.read(1024):
                await out_file.write(content)

        file_path = temp_file.name

    background_tasks.add_task(bulk_update, file_path, db)

    return {"status": "processing", "message": f"File {file.filename} was uploaded."}

@app.get("/seguimiento_docente")
async def seguimiento_docente(
    page: int | None = None,
    limit: int | None = None,
    docente: str | None = None,
    semestre: str | None = None,
    db: AsyncSession = Depends(db_session)
) -> list[SeguimientoDocente]:

    if page and not limit:
        raise HTTPException(
            status_code=400, 
            detail="Must specify limit when specifying page"
        )

    stmt = select(
        Clase.id_docente.label("Docente"),
        Clase.semestre.label("Semestre"),
        func.count(distinct(Clase.asignatura)).label("Cantidad Asignaturas"),
        func.count(Clase.id_curso_grupo).label("Cantidad Grupos"),
        func.sum(Clase.numero_estudiantes).label("Numero Estudiantes"),
        func.array_agg(distinct(Clase.asignatura)).label("Asignaturas"),
        func.sum(
            Clase.clases_dictadas * (func.extract("epoch", Clase.hora_fin - Clase.hora_inicio) / 3600.0)
        ).label("Horas Lectivas"),
        func.sum(case((Clase.tendencia_desempeno == "Estable", 1), else_=0)).label("Comentarios Estables"),
        func.sum(case((Clase.tendencia_desempeno == "En riesgo", 1), else_=0)).label("Comentarios En Riesgo"),
        func.sum(case((Clase.tendencia_desempeno == "Mejora", 1), else_=0)).label("Comentarios En Mejora"),
    )

    stmt = grouping_and_paginating(stmt, page, limit,
        id_docente=docente, semestre=semestre
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()
    df = pd.DataFrame(rows).convert_dtypes()

    if df.empty:
        return []

    df = (
        df.set_index(["Docente"], append=False)
        .groupby(level=["Docente"], group_keys=False)
        .apply(agregar_metricas_generales_docente, include_groups=False)
        .reset_index()
    )

    return df.convert_dtypes().to_dict(orient="records")


@app.get("/seguimiento_docente/count")
async def seguimiento_docente_count(
    docente: str | None = None,
    semestre: str | None = None,
    db: AsyncSession = Depends(db_session)
) -> int:
    return await count(db, id_docente=docente, semestre=semestre)

@app.get("/seguimiento_docente_por_asignatura")
async def seguimiento_docente_por_asignatura(
    page: int | None = None,
    limit: int | None = None,
    docente: str | None = None,
    asignatura: str | None = None,
    db: AsyncSession = Depends(db_session)
) -> list[SeguimientoDocenteAsignatura]:

    if page and not limit:
        raise HTTPException(
            status_code=400, 
            detail="Must specify limit when specifying page"
        )

    stmt = select(
        Clase.id_docente.label("Docente"),
        Clase.semestre.label("Semestre"),
        Clase.asignatura.label("Asignatura"),
        func.count(Clase.id_curso_grupo).label("Cantidad Grupos"),
        func.sum(Clase.numero_estudiantes).label("Numero Estudiantes"),
        func.avg(Clase.puntaje_claridad).label("Puntaje Claridad"),
        func.avg(Clase.puntaje_metodologia).label("Puntaje Metodología"),
        func.avg(Clase.puntaje_evaluacion).label("Puntaje Evaluación"),
        func.array_agg(distinct(Clase.comentario)).label("Comentarios"),
        func.sum(
            Clase.clases_dictadas * (func.extract("epoch", Clase.hora_fin - Clase.hora_inicio) / 3600.0)
        ).label("Horas Lectivas"),
        func.sum(Clase.numero_estudiantes_aprobaron).label("Estudiantes Aprobados"),
        func.sum(case((Clase.tendencia_desempeno == "Estable", 1), else_=0)).label("Comentarios Estables"),
        func.sum(case((Clase.tendencia_desempeno == "En riesgo", 1), else_=0)).label("Comentarios En Riesgo"),
        func.sum(case((Clase.tendencia_desempeno == "Mejora", 1), else_=0)).label("Comentarios En Mejora"),
    )

    stmt = grouping_and_paginating(stmt, page, limit,
        id_docente=docente, asignatura=asignatura, semestre=None
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()
    df = pd.DataFrame(rows).convert_dtypes()

    if df.empty:
        return []

    df["Semestre"] = df["Semestre"].apply(
        lambda s: pd.Period(s.strip().replace("-1", "Q1").replace("-2", "Q3"), freq="2Q-DEC")
    ).astype("period[2Q-DEC]")

    df = (
        df.set_index(["Docente", "Asignatura"], append=False)
        .groupby(level=["Docente", "Asignatura"], group_keys=False)
        .apply(completar_semestres, include_groups=False)
        .reset_index()
    )

    df = (
        df.set_index(["Docente", "Asignatura"], append=False)
        .groupby(level=["Docente", "Asignatura"], group_keys=False)
        .apply(agregar_metricas_docente_por_asignatura, include_groups=False)
        .reset_index()
        .dropna(subset=["Comentarios"])
    )

    df["Semestre"] = df["Semestre"].apply(period_to_string).astype("category")

    return df.convert_dtypes().to_dict(orient="records")

@app.get("/seguimiento_docente_por_asignatura/count")
async def seguimiento_docente_por_asignatura_count(
    docente: str | None = None,
    asignatura: str | None = None,
    db: AsyncSession = Depends(db_session)
) -> int:
    return await count(db, id_docente=docente, asignatura=asignatura, semestre=None)

@app.get("/seguimiento_asignaturas")
async def seguimiento_asignaturas(
    page: int | None = None,
    limit: int | None = None,
    semestre: str | None = None,
    asignatura: str | None = None,
    db: AsyncSession = Depends(db_session)
) -> list[SeguimientoAsignaturas]:
    
    if page and not limit:
        raise HTTPException(
            status_code=400, 
            detail="Must specify limit when specifying page"
        )

    stmt = select(
        Clase.asignatura.label("Asignatura"),
        Clase.semestre.label("Semestre"),
        func.count(distinct(Clase.id_docente)).label("Cantidad Docentes"),
        func.count(Clase.id_curso_grupo).label("Cantidad Grupos"),
        func.sum(Clase.numero_estudiantes).label("Numero Estudiantes"),
        func.sum(Clase.promedio_asistencias_estudiantes).label("Asistencia Típica Estudiantes"),
        func.sum(
            Clase.clases_dictadas * (func.extract("epoch", Clase.hora_fin - Clase.hora_inicio) / 3600.0)
        ).label("Horas Lectivas"),
        func.sum(Clase.numero_estudiantes_aprobaron).label("Estudiantes Aprobados"),
        func.sum(Clase.numero_estudiantes_perdieron).label("Estudiantes Perdieron"),
        func.sum(Clase.numero_estudiantes_desistieron).label("Estudiantes Desistieron"),
        func.sum(Clase.clases_dictadas).label("Clases Dictadas"),
    )

    stmt = grouping_and_paginating(stmt, page, limit,
        asignatura=asignatura, semestre=semestre
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()
    df = pd.DataFrame(rows)

    if df.empty:
        return []

    return df.convert_dtypes().to_dict(orient="records")

@app.get("/seguimiento_asignaturas/count")
async def seguimiento_asignaturas_count(
    semestre: str | None = None,
    asignatura: str | None = None,
    db: AsyncSession = Depends(db_session)
) -> int:
    return await count(db, asignatura=asignatura, semestre=semestre)


async def count(db: AsyncSession, **fields) -> int:
    conditions = []
    main_select_fields = []
    for field, value in fields.items():
        main_select_fields.append(getattr(Clase, field))
        if not value:
            continue
        conditions.append(getattr(Clase, field) == value)

    subq = select(*main_select_fields)
    
    if len(conditions) > 0:
        subq = subq.where(*conditions)
        
    subq = subq.group_by(*main_select_fields).subquery()
    
    result = await db.execute(select(func.count()).select_from(subq))

    return result.scalar() or 0


def grouping_and_paginating(stmt, page: int, limit: int, **fields):
    conditions = []
    main_select_fields = []
    for field, value in fields.items():
        main_select_fields.append(getattr(Clase, field))
        if not value:
            continue
        conditions.append(getattr(Clase, field) == value)

    if len(conditions) > 0:
        stmt = stmt.where(*conditions)

    stmt = stmt.group_by(*main_select_fields).order_by(*[
        select_field.asc() for select_field in main_select_fields
    ])

    if page and limit:
        offset_value = (page - 1) * limit
        stmt = stmt.limit(limit).offset(offset_value)
    elif limit:
        stmt = stmt.limit(limit).offset(0)

    return stmt
