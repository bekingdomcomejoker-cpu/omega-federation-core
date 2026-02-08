import sqlite3
import json
import hashlib
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Statement(BaseModel):
    id: str
    content: str
    category: str  # fact | belief | symbol | imagination | narrative | unresolved | lie
    mode: str      # assertion | symbolic | hypothesis
    source: str    # user | service | agent
    timestamp: float = Field(default_factory=time.time)
    provenance: Dict[str, Any]
    hash: str

class TemporalEnvelope(BaseModel):
    statement_id: str
    valid_from: float
    valid_to: Optional[float] = None
    superseded_by: Optional[str] = None

class Relation(BaseModel):
    from_id: str
    to_id: str
    type: str  # supports | contradicts | refines | symbol_of | derived_from

class OmegaSpine:
    """
    The Canonical Spine: A 3-tier append-only memory system.
    Tier 1: Signal (Ephemeral)
    Tier 2: Spine (Append-only Ledger)
    Tier 3: Archive (Derived/Consolidated)
    """
    def __init__(self, db_path: str = "omega_spine.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Tier 2: Spine Ledger
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statements (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    category TEXT,
                    mode TEXT,
                    source TEXT,
                    timestamp REAL,
                    provenance TEXT,
                    hash TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS temporal_envelopes (
                    statement_id TEXT,
                    valid_from REAL,
                    valid_to REAL,
                    superseded_by TEXT,
                    FOREIGN KEY(statement_id) REFERENCES statements(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS relations (
                    from_id TEXT,
                    to_id TEXT,
                    type TEXT,
                    FOREIGN KEY(from_id) REFERENCES statements(id),
                    FOREIGN KEY(to_id) REFERENCES statements(id)
                )
            ''')
            conn.commit()

    def add_statement(self, content: str, category: str, mode: str, source: str, provenance: Dict[str, Any]) -> str:
        stmt_id = f"stmt_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:12]}"
        stmt_hash = hashlib.sha256(content.encode()).hexdigest()
        
        stmt = Statement(
            id=stmt_id,
            content=content,
            category=category,
            mode=mode,
            source=source,
            provenance=provenance,
            hash=stmt_hash
        )

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO statements VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (stmt.id, stmt.content, stmt.category, stmt.mode, stmt.source, stmt.timestamp, json.dumps(stmt.provenance), stmt.hash)
            )
            cursor.execute(
                "INSERT INTO temporal_envelopes (statement_id, valid_from) VALUES (?, ?)",
                (stmt.id, stmt.timestamp)
            )
            conn.commit()
        return stmt_id

    def add_relation(self, from_id: str, to_id: str, rel_type: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO relations VALUES (?, ?, ?)", (from_id, to_id, rel_type))
            conn.commit()

    def discern_truth(self, statement_id: str) -> Dict[str, Any]:
        """
        Discernment logic: check for contradictions and provenance.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Get the statement
            cursor.execute("SELECT * FROM statements WHERE id = ?", (statement_id,))
            stmt = cursor.fetchone()
            if not stmt:
                return {"error": "Statement not found"}

            # Check for contradictions
            cursor.execute("""
                SELECT s.id, s.category FROM statements s
                JOIN relations r ON (r.from_id = s.id OR r.to_id = s.id)
                WHERE (r.from_id = ? OR r.to_id = ?) AND r.type = 'contradicts'
            """, (statement_id, statement_id))
            contradictions = cursor.fetchall()

            is_lie = any(c[1] == 'fact' for c in contradictions)
            
            return {
                "statement_id": statement_id,
                "is_lie": is_lie,
                "contradictions": [c[0] for c in contradictions],
                "status": "verified" if not is_lie else "flagged"
            }

if __name__ == "__main__":
    spine = OmegaSpine()
    s1 = spine.add_statement("The sky is blue.", "fact", "assertion", "user", {"tool": "manual"})
    s2 = spine.add_statement("The sky is green.", "fact", "assertion", "agent", {"tool": "manual"})
    spine.add_relation(s1, s2, "contradicts")
    print(spine.discern_truth(s2))
