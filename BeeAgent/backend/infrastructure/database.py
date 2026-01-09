# backend/infrastructure/database.py
import pyodbc
from datetime import datetime
from typing import Optional, Dict, Any
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DB_SERVER = "localhost"
DB_NAME = "BeeAgent"

def create_database_if_not_exists():
    """
    Kreiraj bazu 'BeeAgent' ako ne postoji.
    Ovo se mora pozvati PRIJE bilo kakvog konektovanja na bazu.
    """
    try:
        
        master_conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={DB_SERVER};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )
        
        logger.info(f"Povezivanje na SQL Server: {DB_SERVER}")
        master_conn = pyodbc.connect(master_conn_str)
        cursor = master_conn.cursor()
        
      
        logger.info(f"Provjeravam da li baza '{DB_NAME}' postoji...")
        cursor.execute(f"SELECT name FROM sys.databases WHERE name = '{DB_NAME}'")
        
        if not cursor.fetchone():
            logger.info(f"Kreiranje baze '{DB_NAME}'...")
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            master_conn.commit()
            logger.info(f"Baza '{DB_NAME}' uspješno kreirana")
        else:
            logger.info(f"ℹBaza '{DB_NAME}' već postoji")
        
        master_conn.close()
        return True
        
    except pyodbc.InterfaceError as e:
        logger.error(f"Nije moguće spojiti se na SQL Server: {e}")
        logger.error("Provjerite da li je SQL Server pokrenut")
        return False
    except Exception as e:
        logger.error(f"Greška pri kreiranju baze: {e}")
        return False

def get_connection():
    """Vrati konekciju za BeeAgent bazu"""
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"Trusted_Connection=yes;"
        f"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

def init_database():
    """
    Kompletna inicijalizacija baze:
    1. Kreira bazu ako ne postoji
    2. Kreira sve tabele ako ne postoje
    3. Popuni SystemSettings ako je prazno
    """

    if not create_database_if_not_exists():
        logger.error("Nije moguće nastaviti bez baze podataka")
        return False
    
 
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        logger.info("Inicijalizacija tabela...")
        
   
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES 
                          WHERE TABLE_NAME = 'Observations')
            BEGIN
                CREATE TABLE Observations (
                    Id INT IDENTITY(1,1) PRIMARY KEY,
                    Timestamp DATETIME NOT NULL DEFAULT GETDATE(),
                    Temperature FLOAT NOT NULL,
                    Humidity FLOAT NOT NULL,
                    Frames INT NOT NULL,
                    Strength INT NOT NULL,
                    Varoa BIT NOT NULL,
                    PredictedAction NVARCHAR(50) NULL,
                    Status NVARCHAR(20) DEFAULT 'queued',
                    Confidence FLOAT NULL
                )
                PRINT 'Tabela Observations kreirana'
            END
            ELSE
                PRINT 'Tabela Observations već postoji'
        """)
        
   
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES 
                          WHERE TABLE_NAME = 'Feedback')
            BEGIN
                CREATE TABLE Feedback (
                    Id INT IDENTITY(1,1) PRIMARY KEY,
                    ObservationId INT NOT NULL,
                    UserLabel NVARCHAR(50) NOT NULL,
                    Correct BIT NOT NULL,
                    Comment NVARCHAR(255) NULL,
                    CreatedAt DATETIME DEFAULT GETDATE(),
                    FOREIGN KEY (ObservationId) REFERENCES Observations(Id)
                )
                PRINT 'Tabela Feedback kreirana'
            END
            ELSE
                PRINT 'Tabela Feedback već postoji'
        """)
        
  
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES 
                          WHERE TABLE_NAME = 'SystemSettings')
            BEGIN
                CREATE TABLE SystemSettings (
                    Id INT PRIMARY KEY DEFAULT 1,
                    GoldThreshold INT DEFAULT 10,
                    EnableRetraining BIT DEFAULT 1,
                    NewGoldSinceLastTrain INT DEFAULT 0,
                    ExplorationRate FLOAT DEFAULT 0.05,
                    CONSTRAINT CK_SingleRow CHECK (Id = 1)
                )
                PRINT 'Tabela SystemSettings kreirana'
            END
            ELSE
                PRINT 'Tabela SystemSettings već postoji'
        """)
        
 
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM SystemSettings WHERE Id = 1)
            BEGIN
                INSERT INTO SystemSettings DEFAULT VALUES
                PRINT 'SystemSettings popunjen podrazumijevanim vrijednostima'
            END
            ELSE
                PRINT 'SystemSettings već ima podatke'
        """)
        
        conn.commit()
        logger.info("Baza potpuno inicijalizirana!")
        return True
        
    except pyodbc.ProgrammingError as e:
        logger.error(f"SQL greška: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Neočekivana greška: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def save_observation(temperature: float, humidity: float, frames: int, 
                     strength: int, varoa: bool, predicted_action: str, 
                     confidence: float = None) -> Optional[int]:
    """Sačuvaj opservaciju u bazu i vrati ID"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO Observations 
            (Timestamp, Temperature, Humidity, Frames, Strength, Varoa, 
             PredictedAction, Confidence, Status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'processed')
        """, (datetime.now(), temperature, humidity, frames, 
              strength, varoa, predicted_action, confidence))
        
        conn.commit()
        
        
        cursor.execute("SELECT @@IDENTITY")
        row = cursor.fetchone()
        obs_id = row[0] if row else None
        
        logger.debug(f"Opservacija #{obs_id} sačuvana")
        return obs_id
        
    except Exception as e:
        logger.error(f"Greška pri čuvanju opservacije: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def save_feedback(observation_id: int, user_label: str, 
                  correct: bool, comment: str = None) -> bool:
    """Sačuvaj feedback u bazu"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO Feedback (ObservationId, UserLabel, Correct, Comment)
            VALUES (?, ?, ?, ?)
        """, (observation_id, user_label, int(correct), comment))
        
        conn.commit()
        logger.debug(f"Feedback sačuvan za opservaciju #{observation_id}")
        return True
        
    except Exception as e:
        logger.error(f"Greška pri čuvanju feedbacka: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_next_queued_observation() -> Optional[Dict[str, Any]]:
    """Dohvati sljedeću opservaciju za obradu (QUEUE)"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT TOP 1 Id, Temperature, Humidity, Frames, Strength, Varoa
            FROM Observations 
            WHERE Status = 'queued'
            ORDER BY Timestamp ASC
        """)
        
        row = cursor.fetchone()
        
        if row:
            result = {
                'id': row[0],
                'temperature': row[1],
                'humidity': row[2],
                'frames': row[3],
                'strength': row[4],
                'varoa': bool(row[5])
            }
            logger.debug(f"Nađena queued opservacija #{result['id']}")
            return result
        
        logger.debug("Nema queued opservacija")
        return None
        
    except Exception as e:
        logger.error(f"Greška pri dohvatanju opservacije: {e}")
        return None
    finally:
        if conn:
            conn.close()

def update_observation_status(observation_id: int, status: str) -> bool:
    """Ažuriraj status opservacije"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE Observations 
            SET Status = ?
            WHERE Id = ?
        """, (status, observation_id))
        
        conn.commit()
        logger.debug(f"Status opservacije #{observation_id} promijenjen u '{status}'")
        return True
        
    except Exception as e:
        logger.error(f"Greška pri ažuriranju statusa: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_database_info() -> Dict[str, Any]:
    """Vrati informacije o bazi"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
       
        cursor.execute("SELECT COUNT(*) FROM Observations")
        obs_count = cursor.fetchone()[0]
        
       
        cursor.execute("SELECT COUNT(*) FROM Observations WHERE Status = 'queued'")
        queued_count = cursor.fetchone()[0]
        
        
        cursor.execute("SELECT COUNT(*) FROM Feedback")
        feedback_count = cursor.fetchone()[0]
        
        return {
            "database": DB_NAME,
            "server": DB_SERVER,
            "observations": obs_count,
            "queued": queued_count,
            "feedback": feedback_count
        }
        
    except Exception as e:
        logger.error(f"Greška pri dohvatanju informacija: {e}")
        return {"error": str(e)}
    finally:
        if conn:
            conn.close()

# Auto-inicijalizacija kada se modul učitava
if __name__ == "__main__":
    print("Pokrećem inicijalizaciju baze...")
    success = init_database()
    if success:
        print("Inicijalizacija završena uspješno!")
    else:
        print("Inicijalizacija nije uspjela")


def get_observation_status(observation_id: int) -> Optional[Dict[str, Any]]:
    """Dohvati status i rezultat opservacije"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT Id, Timestamp, PredictedAction, Confidence, Status
            FROM Observations 
            WHERE Id = ?
        """, observation_id)
        
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row[0],
                'timestamp': row[1],
                'predicted_action': row[2],
                'confidence': row[3],
                'status': row[4]
            }
        return None
        
    except Exception as e:
        logger.error(f"Greška pri dohvatanju statusa: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_observation_details(observation_id: int) -> Optional[Dict[str, Any]]:
    """Dohvati sve detalje opservacije"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT Id, Timestamp, Temperature, Humidity, Frames, 
                   Strength, Varoa, PredictedAction, Confidence, Status
            FROM Observations 
            WHERE Id = ?
        """, observation_id)
        
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row[0],
                'timestamp': row[1],
                'temperature': row[2],
                'humidity': row[3],
                'frames': row[4],
                'strength': row[5],
                'varoa': bool(row[6]),
                'predicted_action': row[7],
                'confidence': row[8],
                'status': row[9]
            }
        return None
        
    except Exception as e:
        logger.error(f"Greška pri dohvatanju detalja: {e}")
        return None
    finally:
        if conn:
            conn.close()