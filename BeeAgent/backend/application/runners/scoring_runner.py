# backend/application/runners/scoring_runner.py
from typing import Optional
from dataclasses import dataclass
from domain.entities import ObservationStatus
from application.services.queue_service import QueueService
from application.services.scoring_service import ScoringService
import time

@dataclass
class ScoringTickResult:
    """Rezultat jednog tick-a"""
    observation_id: int
    action: str
    confidence: float
    requires_review: bool
    is_exploring: bool
    processing_time_ms: float
    
    def to_dict(self):
        return {
            "observation_id": self.observation_id,
            "action": self.action,
            "confidence": self.confidence,
            "requires_review": self.requires_review,
            "is_exploring": self.is_exploring,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": time.time()
        }

class ScoringAgentRunner:
    """
    RUNNER koji implementira agentički ciklus:
    SENSE → THINK → ACT
    """
    
    def __init__(self, queue_service: QueueService, 
                 scoring_service: ScoringService):
        self.queue_service = queue_service
        self.scoring_service = scoring_service
        self.processed_count = 0
        self.total_processing_time = 0
    
    def step(self) -> Optional[ScoringTickResult]:
        """
        Izvrši JEDAN tick agentičkog ciklusa
        Vraća: ScoringTickResult ako ima posla, None ako nema
        """
        start_time = time.time()
        
        # ===== SENSE =====
        observation = self.queue_service.dequeue_next()
        if not observation:
            return None
        
        # ===== THINK =====
        prediction = self.scoring_service.score_observation(observation)
        
        # ===== ACT =====
        self.queue_service.mark_as_processed(
            observation_id=observation.id,
            action=prediction.action.value,
            confidence=prediction.confidence
        )
        
        processing_time = (time.time() - start_time) * 1000  # u ms
        self.processed_count += 1
        self.total_processing_time += processing_time
        
        return ScoringTickResult(
            observation_id=observation.id,
            action=prediction.action.value,
            confidence=prediction.confidence,
            requires_review=prediction.requires_review,
            is_exploring=prediction.is_exploring,
            processing_time_ms=processing_time
        )
    
    def get_status(self):
        """Vrati status runnera"""
        avg_time = (self.total_processing_time / self.processed_count 
                   if self.processed_count > 0 else 0)
        
        return {
            "processed_count": self.processed_count,
            "avg_processing_time_ms": avg_time,
            "total_processing_time_ms": self.total_processing_time,
            "is_active": True
        }