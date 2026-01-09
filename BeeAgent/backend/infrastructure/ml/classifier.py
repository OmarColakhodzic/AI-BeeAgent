# backend/infrastructure/ml/classifier.py
import joblib
import numpy as np
import os
from typing import List, Tuple, Optional
from sklearn.linear_model import SGDClassifier

class BeeClassifier:
    """ML klasa - infrastruktura (crna kutija)"""
    
    def __init__(self, model_file: str = "model.joblib"):
        self.model_file = model_file
        self.model: Optional[SGDClassifier] = None
        self.classes = [
            "nista", "priorihrana", "provjera_varoe", "preseljenje", "berba",
            "zalivanje", "hranjivanje", "prskanje", "povecanje_ramova",
            "smanjenje_ramova", "kontrola_stetocina", "promjena_lokacije",
            "provjera_zdravlja", "ciscenje_zajednice", "dodatna_inspekcija"
        ]
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Učitaj postojeći model ili kreiraj novi"""
        if os.path.exists(self.model_file):
            self.model = joblib.load(self.model_file)
            print(f"✓ Model učitan iz {self.model_file}")
        else:
            self.model = SGDClassifier(max_iter=1000, random_state=42)
            self._initialize_with_examples()
            joblib.dump(self.model, self.model_file)
            print(f"✓ Model inicijaliziran")
    
    def _initialize_with_examples(self):
        """Inicijalizacija s osnovnim primjerima"""
        X_init = []
        y_init = []
        
        
        for action in self.classes:
            if action == "nista":
                X_init.append([20, 60, 10, 5, 0])
            elif action == "priorihrana":
                X_init.append([10, 70, 5, 2, 0])
            elif action == "provjera_varoe":
                X_init.append([22, 75, 12, 6, 1])
            elif action == "provjera_zdravlja":
                X_init.append([25, 80, 15, 4, 1])
            elif action == "zalivanje":
                X_init.append([33, 50, 10, 6, 0])
            elif action == "hranjivanje":
                X_init.append([18, 65, 8, 3, 0])
            elif action == "povecanje_ramova":
                X_init.append([20, 65, 15, 9, 0])
            elif action == "smanjenje_ramova":
                X_init.append([22, 70, 25, 8, 0])
            elif action == "dodatna_inspekcija":
                X_init.append([20, 70, 12, 7, 0])
            else:
                X_init.append([20, 65, 10, 5, 0])
            
            y_init.append(action)
        
        self.model.partial_fit(np.array(X_init), np.array(y_init), classes=self.classes)
    
    def predict(self, features: List[float]) -> Tuple[str, float]:
        """Napravi predikciju za date features"""
        x = np.array(features).reshape(1, -1)
        prediction = self.model.predict(x)[0]
        
        try:
            probabilities = self.model.predict_proba(x)[0]
            class_index = self.classes.index(prediction)
            confidence = probabilities[class_index]
        except:
            confidence = 1.0
        
        return prediction, float(confidence)
    
    def train_single(self, features: List[float], label: str):
        """Treniraj model s jednim primjerom"""
        X = np.array(features).reshape(1, -1)
        y = np.array([label])
        self.model.partial_fit(X, y, classes=self.classes)
        joblib.dump(self.model, self.model_file)
        print(f"✓ Model treniran za: {label}")
    
    def train_batch(self, X_batch: np.ndarray, y_batch: np.ndarray):
        """Treniraj model s batch-om podataka"""
        self.model.partial_fit(X_batch, y_batch, classes=self.classes)
        joblib.dump(self.model, self.model_file)
        print(f"✓ Model treniran na {len(y_batch)} primjera")
    
    def get_model_info(self):
        """Vrati informacije o modelu"""
        return {
            "model_type": "SGDClassifier",
            "classes": self.classes,
            "model_file": self.model_file,
            "exists": os.path.exists(self.model_file)
        }