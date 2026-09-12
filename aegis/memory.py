import sqlite3
import math
import time
from typing import Optional, Tuple, Dict, Any, List
from config import MEMORY_DB_PATH, SAFETY_BOUNDARIES

class EpisodicMemoryGraph:
    def __init__(self, db_path=MEMORY_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # UI Landmark Muscle Memory Nodes
        cur.execute('''
            CREATE TABLE IF NOT EXISTS muscle_memory_nodes (
                element_id TEXT PRIMARY KEY,
                target_app TEXT,
                coord_x INTEGER,
                coord_y INTEGER,
                confidence REAL,
                execution_count INTEGER DEFAULT 0,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Self-Healing & Adaptation Log
        cur.execute('''
            CREATE TABLE IF NOT EXISTS self_healing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                element_id TEXT,
                old_x INTEGER,
                old_y INTEGER,
                new_x INTEGER,
                new_y INTEGER,
                drift_distance REAL,
                healed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def register_or_update_node(self, element_id: str, target_app: str, x: int, y: int, confidence: float = 1.0):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO muscle_memory_nodes (element_id, target_app, coord_x, coord_y, confidence, execution_count, last_used)
            VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(element_id) DO UPDATE SET
                coord_x = excluded.coord_x,
                coord_y = excluded.coord_y,
                confidence = excluded.confidence,
                execution_count = execution_count + 1,
                last_used = CURRENT_TIMESTAMP
        ''', (element_id, target_app, x, y, confidence))
        conn.commit()
        conn.close()

    def query_node(self, element_id: str) -> Optional[Tuple[int, int]]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT coord_x, coord_y, confidence FROM muscle_memory_nodes WHERE element_id = ?", (element_id,))
        row = cur.fetchone()
        conn.close()
        if row and row[2] >= SAFETY_BOUNDARIES["MUSCLE_MEMORY_MIN_CONFIDENCE"]:
            return (row[0], row[1])
        return None

    def detect_drift(self, cached_pos: Tuple[int, int], current_pos: Tuple[int, int]) -> Tuple[bool, float]:
        dx = current_pos[0] - cached_pos[0]
        dy = current_pos[1] - cached_pos[1]
        dist = math.sqrt(dx * dx + dy * dy)
        # Anything more than 15px is considered a UI relocation/drift
        is_drift = dist > 15.0
        return is_drift, dist

    def record_healing_event(self, element_id: str, old_pos: Tuple[int, int], new_pos: Tuple[int, int], dist: float):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO self_healing_log (element_id, old_x, old_y, new_x, new_y, drift_distance)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (element_id, old_pos[0], old_pos[1], new_pos[0], new_pos[1], dist))
        
        # Update node coordinates in muscle memory
        cur.execute('''
            UPDATE muscle_memory_nodes 
            SET coord_x = ?, coord_y = ?, confidence = 1.0, last_used = CURRENT_TIMESTAMP
            WHERE element_id = ?
        ''', (new_pos[0], new_pos[1], element_id))
        
        conn.commit()
        conn.close()

    def get_healing_history(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT element_id, old_x, old_y, new_x, new_y, drift_distance, healed_at FROM self_healing_log ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "element_id": r[0],
                "from": (r[1], r[2]),
                "to": (r[3], r[4]),
                "drift_px": round(r[5], 1),
                "timestamp": r[6]
            }
            for r in rows
        ]
