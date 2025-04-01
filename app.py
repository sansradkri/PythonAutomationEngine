from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import subprocess
import datetime
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

DATABASE_URL = 'postgresql://postgres:77malhotra88@localhost/python_automation_engine'
GITHUB_TOKEN = 'token'  # Replace with your GitHub PAT
GITHUB_REPO = 'sansradkri/PythonAutomationEngine'  # Replace with your GitHub repository in the format 'owner/repo'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class ScriptResult(Base):
    __tablename__ = 'script_result'
    id = Column(Integer, primary_key=True, index=True)
    script_name = Column(String, nullable=False)
    trigger_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    result_status = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

class ScriptResultCreate(BaseModel):
    script_name: str
    trigger_time: datetime.datetime
    duration_minutes: int
    result_status: str

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("trigger_run_scripts.html", {"request": request})

import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@app.post("/run_scripts")
def run_scripts(request: Request):
    logging.debug(f"Request data: {request}")
    scripts_path = 'scripts'
    if not os.path.exists(scripts_path):
        raise HTTPException(status_code=404, detail="Scripts folder not found")

    scripts = [f for f in os.listdir(scripts_path) if os.path.isfile(os.path.join(scripts_path, f))]
    results = []
    for script in scripts:
        trigger_time = datetime.datetime.now()
        start_time = datetime.datetime.now()
        process = subprocess.Popen(['python', os.path.join(scripts_path, script)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        end_time = datetime.datetime.now()
        duration_minutes = (end_time - start_time).seconds // 60
        result_status = 'success' if process.returncode == 0 else 'failed'

        # Save result to database
        db = SessionLocal()
        new_result = ScriptResult(
            script_name=script,
            trigger_time=trigger_time,
            duration_minutes=duration_minutes,
            result_status=result_status
        )
        db.add(new_result)
        db.commit()
        db.refresh(new_result)
        db.close()
        results.append(new_result)

        # Trigger GitHub workflow
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "ref": "main",  # Replace with the branch you want to trigger the workflow on
            "inputs": {
                "script_name": script
            }
        }
        logging.debug(f"Request payload to GitHub API: {data}")
        response = requests.post(
            f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/run_scripts.yml/dispatches",
            headers=headers,
            json=data
        )
        logging.debug(f"GitHub API response: {response.status_code} - {response.text}")
        if response.status_code != 204:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to trigger workflow for {script}")

    return {"message": "Scripts executed and workflows triggered successfully", "results": results}

@app.post("/save_script_result")
def save_script_result(script_result: ScriptResultCreate):
    db = SessionLocal()
    new_result = ScriptResult(
        script_name=script_result.script_name,
        trigger_time=script_result.trigger_time,
        duration_minutes=script_result.duration_minutes,
        result_status=script_result.result_status
    )
    db.add(new_result)
    db.commit()
    db.refresh(new_result)
    db.close()
    return {"message": "Result saved successfully", "result": new_result}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
