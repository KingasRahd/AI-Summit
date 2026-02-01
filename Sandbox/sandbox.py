from fastapi import FastAPI,UploadFile,File,Form
import json
from pathlib import Path
import random

app=FastAPI()

UPLOAD_DIR = Path("Recieved_Resume")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.get('/get_jobs')
def get_data():
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

@app.post('/apply')
def random_selection(file:UploadFile=File(...), job_id:str=Form(...)):

    file_name='Original.pdf'
    file_path = UPLOAD_DIR/file_name

    if file.content_type=="application/pdf":
        print('file recieved')

    success = random.choice([True, False])

    if success:
        return {
            "status": "success",
            "job_id": job_id
        }
    else:
        return {
            "status": "failed",
            "job_id": job_id
        }