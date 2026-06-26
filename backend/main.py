import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
from .core.orchestrator import Orchestrator
from .core.models import FindingSet
from .plugins.cfg import CFGExtractor
from .core.compiler_resolver import CompilerResolver

app = FastAPI(title="SolSec Pipeline API")
orchestrator = Orchestrator()

# Ensure uploads directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Unified Smart Contract Analysis Pipeline API"}

@app.post("/analyze", response_model=FindingSet)
async def analyze_contract(file: UploadFile = File(...)):
    if not file.filename.endswith(".sol"):
        raise HTTPException(status_code=400, detail="Only .sol files are supported")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Switch compiler version dynamically based on pragma statement
        CompilerResolver.resolve_and_switch(file_path)
        
        # Run analysis
        results = orchestrator.run_analysis(file_path)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up is optional, keeping it for now to debug if needed
        pass

@app.post("/cfg")
async def get_cfg(file: UploadFile = File(...)):
    if not file.filename.endswith(".sol"):
        raise HTTPException(status_code=400, detail="Only .sol files are supported")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Switch compiler version dynamically based on pragma statement
        CompilerResolver.resolve_and_switch(file_path)
        
        # Run CFG extractor
        extractor = CFGExtractor(file_path)
        return extractor.extract_all_cfgs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
