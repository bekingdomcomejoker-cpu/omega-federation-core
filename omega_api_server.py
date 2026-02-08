from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from omega_orchestrator import OmegaOrchestrator, UnifiedAnalysisRequest, UnifiedAnalysisResult

app = FastAPI(title="Omega Federation API", version="2.0.0")
orchestrator = OmegaOrchestrator()

@app.get("/")
async def root():
    return {"status": "online", "version": "2.0.0", "message": "The Federation is unified."}

@app.post("/analyze", response_model=UnifiedAnalysisResult)
async def analyze(request: UnifiedAnalysisRequest):
    try:
        result = await orchestrator.analyze(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy", "qci": 0.98, "invariant": 1.89}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
