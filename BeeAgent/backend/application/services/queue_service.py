# backend/application/services/queue_service.py
from typing import Optional
from domain.entities import Observation, ObservationStatus
from infrastructure.database import get_connection
import logging

logger = logging.getLogger(__name__)

class QueueService:
    """Servis za upravljanje redom (queue) opservacija"""
    
    def enqueue(self, observation: Observation) -> Observation:
        """Stavi opservaciju u red za obradu"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO Observations 
                (Timestamp, Temperature, Humidity, Frames, Strength, Varoa, Status)
                OUTPUT INSERTED.Id
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                observation.timestamp, observation.temperature,
                observation.humidity, observation.frames,
                observation.strength, observation.varoa,
                ObservationStatus.QUEUED.value
            ))
            
            observation.id = cursor.fetchone()[0]
            conn.commit()
            
            logger.info(f"Opservacija #{observation.id} stavljena u queue")
            return observation
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Greška pri enqueue: {e}")
            raise e
        finally:
            conn.close()
    
    def dequeue_next(self) -> Optional[Observation]:
        """Uzmi sljedeću opservaciju iz reda"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            
            cursor.execute("""
                UPDATE TOP (1) Observations 
                SET Status = 'processing'
                OUTPUT INSERTED.Id, INSERTED.Timestamp, INSERTED.Temperature, 
                       INSERTED.Humidity, INSERTED.Frames, INSERTED.Strength, 
                       INSERTED.Varoa
                WHERE Status = 'queued'
            """)
            
            row = cursor.fetchone()
            conn.commit()
            
            if not row:
                return None
            
            return Observation(
                id=row[0],
                timestamp=row[1],
                temperature=row[2],
                humidity=row[3],
                frames=row[4],
                strength=row[5],
                varoa=bool(row[6]),
                status=ObservationStatus.PROCESSING
            )
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Greška pri dequeue: {e}")
            return None
        finally:
            conn.close()
    
    def mark_as_processed(self, observation_id: int, action: str, confidence: float):
        """Označi opservaciju kao obrađenu - POPRAVLJENO!"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            
            cursor.execute("""
                UPDATE Observations 
                SET PredictedAction = ?, 
                    Confidence = ?,
                    Status = 'processed'
                WHERE Id = ?
            """, (action, confidence, observation_id))
            
            conn.commit()
            logger.info(f"Opservacija #{observation_id} processed: {action}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Greška pri mark_as_processed: {e}")
            
        finally:
            conn.close()