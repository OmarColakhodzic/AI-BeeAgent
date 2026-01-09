# backend/web/main.py
from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Globalni objekti 
classifier = None
queue_service = None
scoring_service = None
runner = None
background_task = None
agent_running = False

# Import DTO-ova
from .dtos import ObservationRequest, FeedbackRequest

# Import servisa i runnera
from infrastructure.ml.classifier import BeeClassifier
from infrastructure.database import init_database, save_feedback, get_connection
from infrastructure.database import get_observation_status, get_observation_details
from domain.entities import Observation
from application.services.queue_service import QueueService
from application.services.scoring_service import ScoringService
from application.runners.scoring_runner import ScoringAgentRunner

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management za FastAPI"""
    
    global classifier, queue_service, scoring_service, runner, agent_running, background_task
    
    logger.info("Inicijalizacija BeeAgent sistema...")
    
    try:
        # 1. Inicijaliziraj bazu
        logger.info("Inicijalizacija baze podataka...")
        db_success = init_database()
        if not db_success:
            logger.error("Neuspješna inicijalizacija baze!")
        else:
            logger.info("Baza podataka spremna")
        
        # 2. Kreiraj ML klasu
        logger.info("Učitavanje ML modela...")
        classifier = BeeClassifier()
        logger.info("ML model spreman")
        
        # 3. Kreiraj servise
        logger.info("Kreiranje servisa...")
        queue_service = QueueService()
        scoring_service = ScoringService(classifier, exploration_rate=0.05)
        
        # 4. Kreiraj runnera (AGENT!)
        logger.info("Kreiranje agent runnera...")
        runner = ScoringAgentRunner(queue_service, scoring_service)
        
        # 5. Automatski pokreni agenta
        logger.info("Pokretanje background agenta...")
        agent_running = True
        background_task = asyncio.create_task(run_agent_loop())
        
        logger.info("BeeAgent sistema spreman!")
        
    except Exception as e:
        logger.error(f"Greška pri inicijalizaciji sistema: {e}")
    
    yield
    
    # Shutdown
    logger.info("Gašenje BeeAgent sistema...")
    agent_running = False
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass

# Kreiraj FastAPI app sa lifespan-om
app = FastAPI(
    title="BeeAgent API - Clean Architecture (100% Async)",
    version="2.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================
# DTO klase
# ==============================================
class QueueResponse(BaseModel):
    status: str
    observation_id: int
    message: str
    timestamp: str
    estimated_wait_time_ms: Optional[float] = None

class PredictionResultResponse(BaseModel):
    observation_id: int
    status: str
    predicted_action: Optional[str] = None
    confidence: Optional[float] = None
    processed_at: Optional[str] = None
    processing_time_ms: Optional[float] = None
    error: Optional[str] = None

class AgentStatusResponse(BaseModel):
    is_running: bool
    processed_count: int
    avg_processing_time_ms: float
    queue_size: int = 0

# ==============================================
# ASINHRONI ENDPOINTI
# ==============================================

@app.get("/")
async def root():
    return {
        "message": "BeeAgent API - 100% Asinhroni Agent",
        "version": "2.0",
        "architecture": "Clean Architecture",
        "agent_pattern": "Sense→Think→Act u background runneru",
        "api_flow": "1. POST /predict → queue, 2. GET /predictions/{id} → result"
    }

@app.post("/predict", response_model=QueueResponse)
async def predict(obs: ObservationRequest):
    """
    PURE TRANSPORT LAYER: Stavi u queue i vrati status
    """
    if not queue_service:
        raise HTTPException(status_code=503, detail="Sistema nije spreman")
    
    try:
        # Mapiraj DTO na Domain entitet
        observation = Observation.create_new(
            temperature=obs.temperature,
            humidity=obs.humidity,
            frames=obs.frames,
            strength=obs.strength,
            varoa=obs.varoa
        )
        
        # SAMO stavi u queue
        saved_obs = queue_service.enqueue(observation)
        
        logger.info(f"Opservacija #{saved_obs.id} stavljena u queue")
        
        # Vrati SAMO status
        return QueueResponse(
            status="queued",
            observation_id=saved_obs.id,
            message="Observation queued for processing by agent",
            timestamp=datetime.now().isoformat(),
            estimated_wait_time_ms=100.0  
        )
        
    except Exception as e:
        logger.error(f"Greška u /predict: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predictions/{observation_id}", response_model=PredictionResultResponse)
async def get_prediction_result(observation_id: int):
    """
    Dohvati rezultat nakon što ga agent obradi
    """
    try:
        # Dohvati status iz baze
        obs_status = get_observation_status(observation_id)
        
        if not obs_status:
            raise HTTPException(status_code=404, detail="Observation not found")
        
        # Ako je još u queue ili se procesira
        if obs_status['status'] in ['queued', 'processing']:
            return PredictionResultResponse(
                observation_id=observation_id,
                status=obs_status['status'],
                message=f"Observation is {obs_status['status']}"
            )
        
        # Ako je obrađeno
        if obs_status['status'] == 'processed':
            return PredictionResultResponse(
                observation_id=observation_id,
                status='processed',
                predicted_action=obs_status['predicted_action'],
                confidence=obs_status['confidence'],
                processed_at=obs_status['timestamp'].isoformat() if obs_status['timestamp'] else None
            )
        
        # Neočekivani status
        return PredictionResultResponse(
            observation_id=observation_id,
            status=obs_status['status'],
            error=f"Unexpected status: {obs_status['status']}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Greška: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def feedback(fb: FeedbackRequest):
    """Primi feedback za kasnije učenje"""
    try:
        success = save_feedback(
            observation_id=fb.obs_id,
            user_label=fb.user_label,
            correct=fb.correct,
            comment=fb.comment
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save feedback")
        
        # Treniraj model ako je predikcija netočna
        if not fb.correct and classifier:
            try:
                obs_details = get_observation_details(fb.obs_id)
                if obs_details:
                    features = [
                        obs_details['temperature'],
                        obs_details['humidity'],
                        obs_details['frames'],
                        obs_details['strength'],
                        int(obs_details['varoa'])
                    ]
                    classifier.train_single(features, fb.user_label)
                    logger.info(f"Model treniran sa feedbackom")
            except Exception as e:
                logger.warning(f"Nije moguće trenirati model: {e}")
        
        return {"ok": True, "message": "Feedback saved"}
        
    except Exception as e:
        logger.error(f"Greška: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/status", response_model=AgentStatusResponse)
async def get_agent_status():
    """Status background agenta"""
    try:
        queue_size = 0
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Observations WHERE Status = 'queued'")
            queue_size = cursor.fetchone()[0]
            conn.close()
        except:
            queue_size = 0
        
        if runner:
            status_info = runner.get_status()
            return AgentStatusResponse(
                is_running=agent_running,
                processed_count=status_info.get("processed_count", 0),
                avg_processing_time_ms=status_info.get("avg_processing_time_ms", 0),
                queue_size=queue_size
            )
        
        return AgentStatusResponse(
            is_running=False,
            processed_count=0,
            avg_processing_time_ms=0,
            queue_size=queue_size
        )
        
    except Exception as e:
        logger.error(f"Greška: {e}")
        return AgentStatusResponse(
            is_running=False,
            processed_count=0,
            avg_processing_time_ms=0,
            queue_size=0
        )

# ==============================================
# BACKGROUND AGENT LOOP
# ==============================================

async def run_agent_loop():
    """Glavna petlja agenta - radi u pozadini"""
    logger.info("Background agent loop pokrenut")
    
    try:
        while agent_running and runner:
            try:
                # Pokreni JEDAN tick (Sense→Think→Act)
                result = runner.step()
                
                if result:
                    logger.info(f"Agent procesirao opservaciju #{result.observation_id}")
                    await asyncio.sleep(0.05)  # Kratka pauza
                else:
                    await asyncio.sleep(2)  # Nema posla - duža pauza
                    
            except Exception as e:
                logger.error(f"Greška u agent loopu: {e}")
                await asyncio.sleep(5)
                
    except asyncio.CancelledError:
        logger.info("Agent loop prekinut")
    except Exception as e:
        logger.error(f"Kritična greška: {e}")
    finally:
        logger.info("Agent loop završen")

# ==============================================
# STARTUP
# ==============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )