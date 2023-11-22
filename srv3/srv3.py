from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import os
import psycopg2

app = FastAPI()

# Connexion à la base de données PostgreSQL
conn = psycopg2.connect(
    dbname="srvdb",
    user="postgres",
    password="12345",
    host="localhost"
)
cursor = conn.cursor()

# Define the path to the 'files' folder
files_folder = "files"


def insert_file_info(serveur_id, file_name):
    try:
        cursor.execute("INSERT INTO files (serveur_id, name) VALUES (%s, %s) RETURNING id;", (serveur_id, file_name))
        conn.commit()
        file_id = cursor.fetchone()[0]
        return file_id
    except Exception as e:
        conn.rollback()
        raise e


@app.get("/telecharger/{file_name}")
async def telecharger_file(file_name: str):
    file_path = os.path.join(files_folder, file_name)

    if os.path.isfile(file_path):
        return FileResponse(file_path, media_type="application/octet-stream", filename=file_name)
    else:
        raise HTTPException(status_code=404, detail="Fichier non trouvé")


@app.post("/uploader/")
async def uploader(file: UploadFile = File(...), serveur_id: int = 3):
    try:
        file_path = os.path.join(files_folder, file.filename)
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        # Insert file information into the database
        file_id = insert_file_info(serveur_id, file.filename)

        return {"message": "Fichier téléchargé avec succès", "file_id": file_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
