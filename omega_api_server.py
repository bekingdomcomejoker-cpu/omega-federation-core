from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time
import logging
from omega_orchestrator import OmegaOrchestrator, UnifiedAnalysisRequest, UnifiedAnalysisResult
from omega_predictive import OmegaPredictiveModeling

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OmegaAPIServer")

# Initialize FastAPI app
app = FastAPI(
    title="Omega Federation v2.0",
    description="Truth-Seeking Intelligence Platform",
    version="2.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator and predictive modeling
orchestrator = OmegaOrchestrator()
predictive_modeling = OmegaPredictiveModeling()
start_time = time.time()

class HealthResponse(BaseModel):
    status: str
    qci: float
    density: float
    engines: List[str]
    uptime: float

@app.get("/")
async def root():
    return {
        "name": "Omega Federation v2.0",
        "description": "Truth-Seeking Intelligence Platform",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze",
            "predictions": "/predictions",
            "spine": "/spine/statements",
            "recommendations": "/recommendations",
            "metrics": "/record-metric"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint returning system status."""
    uptime = time.time() - start_time
    return HealthResponse(
        status="operational",
        qci=0.92,
        density=3.5,
        engines=["star", "aletheia", "omnissiah", "kingdom", "alphabet"],
        uptime=uptime
    )

@app.post("/analyze", response_model=UnifiedAnalysisResult)
async def analyze(request: UnifiedAnalysisRequest):
    """Unified analysis endpoint for the five-engine federation."""
    try:
        result = await orchestrator.analyze(request)
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predictions")
async def get_predictions():
    """Get latest predictive analysis results."""
    try:
        results = await predictive_modeling.run_predictive_cycle()
        return results
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/spine/statements")
async def get_spine_statements(category: Optional[str] = None, limit: int = 10):
    """Retrieve statements from the Spine ledger."""
    try:
        import sqlite3
        conn = sqlite3.connect("omega_spine.db")
        cursor = conn.cursor()
        
        if category:
            cursor.execute(
                "SELECT id, content, category, timestamp FROM statements WHERE category = ? ORDER BY timestamp DESC LIMIT ?",
                (category, limit)
            )
        else:
            cursor.execute(
                "SELECT id, content, category, timestamp FROM statements ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
        
        rows = cursor.fetchall()
        conn.close()
        
        statements = [
            {
                "id": row[0],
                "content": row[1],
                "category": row[2],
                "timestamp": row[3]
            }
            for row in rows
        ]
        return {"statements": statements, "count": len(statements)}
    except Exception as e:
        logger.error(f"Spine query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommendations")
async def get_recommendations():
    """Get actionable recommendations based on latest predictions."""
    try:
        recommendations = predictive_modeling.get_recommendations()
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Recommendation generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/record-metric")
async def record_metric(metric_name: str, value: float, metadata: Optional[dict] = None):
    """Record a system metric for predictive analysis."""
    try:
        predictive_modeling.record_metric(metric_name, value, metadata)
        return {"status": "recorded", "metric": metric_name, "value": value}
    except Exception as e:
        logger.error(f"Metric recording failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
