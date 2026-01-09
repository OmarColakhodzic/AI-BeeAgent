# backend/application/runners/retrain_runner.py
from typing import Optional
from domain.entities import SystemSettings

class RetrainAgentRunner:
    
    def __init__(self, settings_repo, training_service):
        self.settings_repo = settings_repo
        self.training_service = training_service
    
    def step(self) -> Optional[dict]:
        
        settings = self.settings_repo.get_system_settings()
        
        
        should_retrain = (
            settings.enable_retraining and 
            settings.new_gold_since_last_train >= settings.gold_threshold
        )
        
        if not should_retrain:
            return None
        
        
        new_version = self.training_service.train_model()
        
        
        settings.new_gold_since_last_train = 0
        self.settings_repo.save_settings(settings)
        
        return {"model_version": new_version, "retrained": True}