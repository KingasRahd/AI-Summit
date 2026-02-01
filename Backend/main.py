from fastapi import FastAPI,UploadFile,File,HTTPException,Body,Form
import fitz
from fastapi.responses import JSONResponse
from typing import List,Dict
from schema import Constraint
import json
from agent import workflow
from pathlib import Path
import shutil

UPLOAD_DIR = Path("Resume")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


app=FastAPI()

@app.post('/input_data')
async def start(file:UploadFile=File(...), data:str=Form(...)):
    if file.content_type!="application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF resumes allowed")
    
    file_name='Original.pdf'
    file_path = UPLOAD_DIR/file_name

    #pdf_bytes=await file.read()
    with open(file_path, "wb") as f:
        f.write(await file.read())

    text=''
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()

    constraints=Constraint.model_validate(json.loads(data))


    response=await workflow.ainvoke({
        'resume':text,
        'constraint':constraints.model_dump(),
        'file_path':file_path
        })

    successful=response['successful']
    failure=response['failure']
    
    return {'successful':successful,'failure':failure}