import tempfile
import aiofiles
import logging
import pandas as pd

from fastapi import FastAPI, UploadFile, Depends, HTTPException, BackgroundTasks
from db.session import get_session as db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select, func, distinct
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

# @app.get("/seguimiento_docente")
# async def seguimiento_docente(
#     page: int = 1,
#     limit: int = 50,
#     db: AsyncSession = Depends(db_session)
# ):
#     offset_value = (page - 1) * limit
#     stmt = (
#         select(
#             func.count(distinct(Clase.asignatura)).label("Cantidad de Asignaturas"),
#             func.count(Clase.id_curso_grupo).label("Cantidad de Grupos"),
#             func.sum(Clase.numero_estudiantes).label("Numero de Estudiantes"),
#             func.sum(Clase.clases_dictadas * (Clase.hora_fin - Clase.hora_inicio))
#         ).group_by(["id_docente", "semestre"])
#         .offset(offset_value)
#         .limit(limit)
#     )
#
#     result = await db.execute(stmt)
#     rows = result.scalars().all()
#
#     df = pd.DataFrame([row.__dict__ for row in rows])
#
#     # Clean up SQLAlchemy internal state keys if necessary
#     if not df.empty:
#         df = df.drop(columns=["_sa_instance_state"], errors="ignore")
#
#     return df.to_dict(orient="records")


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
