# backend/web/dtos.py
from pydantic import BaseModel
from typing import Optional, List

# Stari DTO-ovi (zadržati za kompatibilnost)
class ObservationRequest(BaseModel):
    temperature: float
    humidity: float
    frames: int
    strength: int
    varoa: int

class FeedbackRequest(BaseModel):
    obs_id: int
    user_label: str
    correct: bool
    comment: Optional[str] = None

# Novi DTO-ovi za async flow
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
    error: Optional[str] = None

# Legacy (za backward compatibility)
class PredictionResponse(BaseModel):
    obs_id: int
    prediction: str
    ml_prediction: str
    source: str
    exploring: bool
    confidence: Optional[float] = None