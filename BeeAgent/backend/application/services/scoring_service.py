# backend/application/services/scoring_service.py
import random
from typing import Tuple
from domain.entities import Observation, ActionType, Prediction

class ScoringService:
    """Servis za scoring - implementira THINK fazu"""
    
    def __init__(self, classifier, exploration_rate: float = 0.05):
        self.classifier = classifier
        self.exploration_rate = exploration_rate
    
    def score_observation(self, observation: Observation) -> Prediction:
        """
        THINK fazu: izračunaj predikciju na osnovu opservacije
        
        Returns: Prediction objekat sa svim detaljima
        """
        
        features = observation.extract_features()
        
        ml_action_str, confidence = self.classifier.predict(features)
        ml_action = ActionType(ml_action_str)
        
        
        is_exploring = random.random() < self.exploration_rate
        if is_exploring:
            final_action = self._explore(ml_action)
            source = "exploration"
        else:
            final_action = ml_action
            source = "ml"
        
        
        requires_review = self._requires_review(observation, final_action, confidence)
        
        return Prediction(
            observation_id=observation.id,
            action=final_action,
            confidence=confidence,
            requires_review=requires_review,
            is_exploring=is_exploring
        )
    
    def _explore(self, current_action: ActionType) -> ActionType:
        """Eksploracija: izaberi nasumičnu drugu akciju"""
        all_actions = list(ActionType)
        other_actions = [act for act in all_actions if act != current_action]
        return random.choice(other_actions) if other_actions else current_action
    
    def _requires_review(self, obs: Observation, action: ActionType, 
                        confidence: float) -> bool:
        
        
        if confidence < 0.6:
            return True
        
        
        if obs.temperature < 5 or obs.temperature > 40:
            return True
        
        
        if obs.strength < 3:
            return True
        
        return False