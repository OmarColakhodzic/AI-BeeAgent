# backend/domain/entities.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class ActionType(str, Enum):
    """Domenski enum za akcije - SVE AKCIJE IZ PROJEKTA"""
    NOTHING = "nista"
    EMERGENCY_FEED = "priorihrana"
    VARROA_CHECK = "provjera_varoe"
    RELOCATION = "preseljenje"
    HARVEST = "berba"
    WATERING = "zalivanje"
    FEEDING = "hranjivanje"
    SPRAYING = "prskanje"
    INCREASE_FRAMES = "povecanje_ramova"
    DECREASE_FRAMES = "smanjenje_ramova"
    PEST_CONTROL = "kontrola_stetocina"
    LOCATION_CHANGE = "promjena_lokacije"
    HEALTH_CHECK = "provjera_zdravlja"
    COLONY_CLEANING = "ciscenje_zajednice"
    ADDITIONAL_INSPECTION = "dodatna_inspekcija"

class ObservationStatus(str, Enum):
    """Statusi opservacije za agentički ciklus"""
    QUEUED = "queued"
    PROCESSING = "processing"
    PROCESSED = "processed"
    REVIEW_NEEDED = "review_needed"

@dataclass
class Observation:
    """Domenska entitet - Opservacija"""
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    temperature: float = 0.0
    humidity: float = 0.0
    frames: int = 0
    strength: int = 0
    varoa: bool = False
    predicted_action: Optional[ActionType] = None
    confidence: Optional[float] = None
    status: ObservationStatus = ObservationStatus.QUEUED
    
    @classmethod
    def create_new(cls, temperature: float, humidity: float, frames: int, 
                   strength: int, varoa: bool) -> 'Observation':
        """Factory metoda za kreiranje nove opservacije"""
        return cls(
            timestamp=datetime.now(),
            temperature=temperature,
            humidity=humidity,
            frames=frames,
            strength=strength,
            varoa=bool(varoa)
        )
    
    def extract_features(self) -> list:
        """Ekstraktuj features za ML model"""
        return [
            self.temperature,
            self.humidity,
            self.frames,
            self.strength,
            int(self.varoa)
        ]

@dataclass
class Prediction:
    """Domenski entitet - Predikcija agenta"""
    observation_id: int
    action: ActionType
    confidence: float
    requires_review: bool = False
    is_exploring: bool = False

@dataclass
class SystemSettings:
    """Domenski entitet - Postavke sistema"""
    id: int = 1
    gold_threshold: int = 10
    enable_retraining: bool = True
    new_gold_since_last_train: int = 0
    exploration_rate: float = 0.05