import tempfile
import aiofiles
import logging
import pandas as pd

from fastapi import FastAPI, UploadFile, Depends, HTTPException, BackgroundTasks
from db.session import get_session as db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from models.clase import Clase

gunicorn_logger = logging.getLogger("gunicorn.error")
logger = logging.getLogger("uvicorn.error")
logger.handlers = gunicorn_logger.handlers
logger.setLevel(gunicorn_logger.level)
app = FastAPI(title="Analitica Academica")

async def bulk_update(csv_file: str, db: AsyncSession):
    logger.info("Entered bulk update")
    campos_clase = Clase.__table__.columns.keys()

    with pd.read_csv(csv_file, sep=",", encoding="utf-8", header="infer", chunksize=500) as reader:
        for chunk in reader:
            if chunk.empty:
                continue
            try:
                chunk.drop_duplicates(subset="id_curso_grupo", keep="first", inplace=True)
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
