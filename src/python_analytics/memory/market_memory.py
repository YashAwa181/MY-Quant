import sqlite3
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors

class MarketMemory:
    def __init__(self, db_path: str = "market_memory.db"):
        """
        Initializes the internal knowledge base to store and retrieve historical market episodes.
        """
        self.conn = sqlite3.connect(db_path)
        self._initialize_db()

    def _initialize_db(self):
        """Creates the historical database schema if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                regime TEXT,
                start_time TEXT,
                end_time TEXT,
                duration_bars INTEGER,
                max_pullback REAL,
                profit_opportunity REAL,
                outcome TEXT,
                trend_strength REAL,
                momentum REAL,
                volatility REAL,
                compression REAL,
                liquidity REAL,
                confidence REAL
            )
        ''')
        self.conn.commit()

    def log_episode(self, episode_data: dict):
        """Saves a completed market episode into the historical database."""
        df = pd.DataFrame([episode_data])
        df.to_sql('episodes', self.conn, if_exists='append', index=False)


class SimilarityEngine:
    def __init__(self, db_path: str = "market_memory.db"):
        """
        Builds a market fingerprint from current measurements and searches the 
        database for historical matches.
        """
        self.conn = sqlite3.connect(db_path)
        
    def _load_fingerprints(self) -> pd.DataFrame:
        """Loads all historical fingerprints from the Market Memory database."""
        query = '''
            SELECT id, outcome, profit_opportunity, 
                   trend_strength, momentum, volatility, compression, liquidity, confidence 
            FROM episodes
        '''
        return pd.read_sql_query(query, self.conn)

    def find_similar_episode(self, current_fingerprint: list, n_neighbors: int = 1) -> dict:
        """
        Uses K-Nearest Neighbors to find the most similar historical market environment.
        """
        df = self._load_fingerprints()
        
        if len(df) < n_neighbors:
            return {"Status": "Gathering historical data. Not enough episodes logged."}

        # Isolate the numeric fingerprint features
        features = df[['trend_strength', 'momentum', 'volatility', 'compression', 'liquidity', 'confidence']]
        
        # Initialize Scikit-Learn's Nearest Neighbors algorithm
        knn = NearestNeighbors(n_neighbors=n_neighbors, metric='euclidean')
        knn.fit(features)
        
        # Search the database for the closest mathematical match to the live fingerprint
        distances, indices = knn.kneighbors([current_fingerprint])
        
        best_match_idx = indices[0][0]
        distance = distances[0][0]
        
        # Convert Euclidean distance to a 0-100% Similarity Score
        max_possible_distance = 100.0 
        similarity_pct = max(0, 100 - (distance / max_possible_distance * 100))
        
        matched_episode = df.iloc[best_match_idx]
        
        return {
            "Similar Episode ID": int(matched_episode['id']),
            "Similarity": f"{round(similarity_pct, 1)}%",
            "Outcome": matched_episode['outcome'],
            "Expected Profit/Loss Opportunity": f"{matched_episode['profit_opportunity']} points"
        }

if __name__ == "__main__":
    # 1. Initialize the internal knowledge base
    memory = MarketMemory()
    
    # 2. Simulate logging a completed historical episode[cite: 2]
    historical_episode = {
        "regime": "Trend",
        "start_time": "09:35",
        "end_time": "13:10",
        "duration_bars": 215,
        "max_pullback": 23.0,
        "profit_opportunity": 412.0,
        "outcome": "Momentum Exhaustion",
        "trend_strength": 87.0,
        "momentum": 82.0,
        "volatility": 65.0,
        "compression": 15.0,
        "liquidity": 80.0,
        "confidence": 94.0
    }
    memory.log_episode(historical_episode)
    
    # 3. Initialize the Similarity Engine
    engine = SimilarityEngine()
    
    # 4. Simulate a live market fingerprint (Current live measurements from modules 1-8)[cite: 2]
    # Format: [Trend, Momentum, Volatility, Compression, Liquidity, Confidence]
    live_fingerprint = [85.0, 79.0, 68.0, 18.0, 75.0, 91.0]
    
    print("\n--- Similarity Engine Search ---")
    results = engine.find_similar_episode(live_fingerprint)
    for key, value in results.items():
        print(f"{key}: {value}")