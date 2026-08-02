import tempfile
import aiofiles
import logging
import pandas as pd

from fastapi import FastAPI, UploadFile, Depends, HTTPException, BackgroundTasks, Response, status
from db.session import get_session as db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select, func, distinct, case, asc, desc
from models.clase import Clase

from utils import (
    agregar_metricas_generales_docente,
    completar_semestres, agregar_metricas_docente_por_asignatura,
    period_to_string
)

gunicorn_logger = logging.getLogger("gunicorn.error")
logger = logging.getLogger("uvicorn.error")
logger.handlers = gunicorn_logger.handlers
logger.setLevel(gunicorn_logger.level)
app = FastAPI(title="Analítica Académica")

@app.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Confirms the FastAPI application process is up."""
    return {"status": "online"}

@app.get("/health/ready")
async def readiness_probe(response: Response, db: AsyncSession = Depends(db_session)):
    """Verifies database readiness using pg_isready."""
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            return {"status": "healthy", "database": "ok"}
    except Exception:
        pass
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "unhealthy", "database": "down"}

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
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(db_session)
):
    offset_value = (page - 1) * limit
    stmt = (
        select(
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
        ).group_by(Clase.id_docente, Clase.semestre)
        .order_by(asc("Docente"), asc("Semestre"))
        .offset(offset_value)
        .limit(limit)
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


@app.get("/seguimiento_docente_por_asignatura")
async def seguimiento_docente_por_asignatura(
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(db_session)
):
    offset_value = (page - 1) * limit
    stmt = (
        select(
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
        ).group_by(Clase.id_docente, Clase.semestre, Clase.asignatura)
        .order_by(asc("Docente"), asc("Asignatura"), asc("Semestre"))
        .offset(offset_value)
        .limit(limit)
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
        .dropna(subset=["Reingreso"])
    )

    df["Semestre"] = df["Semestre"].apply(period_to_string).astype("category")

    return df.convert_dtypes().to_dict(orient="records")

@app.get("/seguimiento_asignaturas")
async def seguimiento_asignaturas(
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(db_session)
):
    offset_value = (page - 1) * limit
    stmt = (
        select(
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
        ).group_by(Clase.asignatura, Clase.semestre)
        .order_by(asc("Asignatura"), asc("Semestre"))
        .offset(offset_value)
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()
    df = pd.DataFrame(rows)

    if df.empty:
        return []

    return df.convert_dtypes().to_dict(orient="records")
