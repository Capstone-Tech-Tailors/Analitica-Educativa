import tempfile
import aiofiles
from fastapi import FastAPI, UploadFile

app = FastAPI()

@app.post("/upload/")
async def upload_file(file: UploadFile):
    # delete=True ensures the file vanishes when closed
    # dir=tempfile.gettempdir() keeps it in the OS temp folder
    with tempfile.NamedTemporaryFile(delete=True, dir=tempfile.gettempdir()) as temp_file:

        # 1. Write the upload to the temporary file asynchronously
        async with aiofiles.open(temp_file.name, "wb") as out_file:
            while content := await file.read(1024):
                await out_file.write(content)

        # 2. Do your processing here using the path: temp_file.name
        # (e.g., read the file back, pass the path to a library, etc.)
        file_path = temp_file.name

    # <-- The file is automatically deleted right here as we exit the 'with' block
    return {"status": "processed", "message": f"Temporary file {file_path} was cleaned up."}
