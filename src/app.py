import tempfile
import aiofiles
import logging
import pandas as pd

from fastapi import FastAPI, UploadFile, Depends, HTTPException, BackgroundTasks
from db.session import get_session as db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select, func, distinct, case, asc, desc
from models.clase import Clase

gunicorn_logger = logging.getLogger("gunicorn.error")
logger = logging.getLogger("uvicorn.error")
logger.handlers = gunicorn_logger.handlers
logger.setLevel(gunicorn_logger.level)
app = FastAPI(title="Analítica Académica")

async def bulk_update(csv_file: str, db: AsyncSession):
    logger.info("Entered bulk update")
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
    logger.info("Entered /etl")
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV.")

    file_path: str = ""
    with tempfile.NamedTemporaryFile(delete=False, dir=tempfile.gettempdir()) as temp_file:

        async with aiofiles.open(temp_file.name, "wb") as out_file:
            while content := await file.read(1024):
                await out_file.write(content)

        file_path = temp_file.name

    background_tasks.add_task(bulk_update,file_path, db)

    return {"status": "processing", "message": f"File {file.filename} was uploaded."}

def agregar_metricas_generales_docente(muestras_docente):
    muestras = muestras_docente.copy(deep=True)
    muestras.reset_index(inplace=True) # drop multi-index

    muestras.reset_index(inplace=True)  # creates 'index' column with original positions
    muestras["Max Acumulado Cantidad Asignaturas"] = muestras["Cantidad Asignaturas"].cummax()
    muestras["Max Acumulado Cantidad Grupos"] = muestras["Cantidad Grupos"].cummax()
    muestras["Max Acumulado Horas Lectivas"] = muestras["Horas Lectivas"].cummax()

    # Campos temporales para hacerle seguimiento a la primera occurencia de maximos locales
    mask_materias = (muestras["Cantidad Asignaturas"] == muestras["Max Acumulado Cantidad Asignaturas"])
    mask_grupos = (muestras["Cantidad Grupos"] == muestras["Max Acumulado Cantidad Grupos"])
    mask_horas_lectivas = (muestras["Horas Lectivas"] == muestras["Max Acumulado Horas Lectivas"])
    muestras["last_max_idx_materias"] = muestras["index"].where(mask_materias).ffill().astype(int)
    muestras["last_max_idx_grupos"] = muestras["index"].where(mask_grupos).ffill().astype(int)
    muestras["last_max_idx_horas_lectivas"] = muestras["index"].where(mask_horas_lectivas).ffill().astype(int)

    muestras["Cantidad Semestres sin Sobrecarga de Asignaturas"] = muestras["index"] - muestras["last_max_idx_materias"]
    muestras["Cantidad Semestres sin Sobrecarga de Grupos"] = muestras["index"] - muestras["last_max_idx_grupos"]
    muestras["Cantidad Semestres sin Sobrecarga Horaria"] = muestras["index"] - muestras["last_max_idx_horas_lectivas"]

    muestras["Indice de Carga Asignaturas"] = muestras["Cantidad Asignaturas"] / muestras["Max Acumulado Cantidad Asignaturas"]
    muestras["Indice de Carga Grupos"] = muestras["Cantidad Grupos"] / muestras["Max Acumulado Cantidad Grupos"]
    muestras["Indice de Carga Horaria"] = muestras["Horas Lectivas"] / muestras["Max Acumulado Horas Lectivas"]

    muestras.drop(columns=[
        "index",
        "Max Acumulado Cantidad Asignaturas",
        "Max Acumulado Cantidad Grupos",
        "Max Acumulado Horas Lectivas",
        "last_max_idx_materias", "last_max_idx_grupos", "last_max_idx_horas_lectivas"
    ], inplace=True)
    muestras.set_index(["Docente"], inplace=True)
    return muestras

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
    df = pd.DataFrame(rows)

    df = (
        df.set_index(["Docente"], append=False)
        .groupby(level=["Docente"], group_keys=False)
        .apply(agregar_metricas_generales_docente, include_groups=False)
        .reset_index()
    )

    return df.to_dict(orient="records")


@app.get("/seguimiento_docente_por_asignatura")
async def seguimiento_docente_por_asignatura(
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(db_session)
):
    offset_value = (page - 1) * limit
    stmt = (
        select(Clase)
        .offset(offset_value)
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.scalars().all()

    df = pd.DataFrame([row.__dict__ for row in rows])

    # Clean up SQLAlchemy internal state keys if necessary
    if not df.empty:
        df = df.drop(columns=["_sa_instance_state"], errors="ignore")

    return df.to_dict(orient="records")
