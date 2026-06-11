import sqlite3
from contextlib import contextmanager
from typing import Optional


DB_PATH = "soap_notes.db"


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def managed_connection(db_path: str = DB_PATH):
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str = DB_PATH) -> None:
    with managed_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                document_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evolutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                soap_note TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        """)


def create_patient(name: str, document_id: str, db_path: str = DB_PATH) -> int:
    with managed_connection(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO patients (name, document_id) VALUES (?, ?)",
            (name, document_id),
        )
        return cursor.lastrowid


def get_patient(patient_id: int, db_path: str = DB_PATH) -> Optional[dict]:
    with managed_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
        return dict(row) if row else None


def update_patient(patient_id: int, name: str, document_id: str, db_path: str = DB_PATH) -> bool:
    with managed_connection(db_path) as conn:
        cursor = conn.execute(
            "UPDATE patients SET name = ?, document_id = ? WHERE id = ?",
            (name, document_id, patient_id),
        )
        return cursor.rowcount > 0


def delete_patient(patient_id: int, db_path: str = DB_PATH) -> bool:
    with managed_connection(db_path) as conn:
        cursor = conn.execute(
            "DELETE FROM patients WHERE id = ?", (patient_id,)
        )
        return cursor.rowcount > 0


def create_evolution(patient_id: int, soap_note: str, db_path: str = DB_PATH) -> int:
    with managed_connection(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO evolutions (patient_id, soap_note) VALUES (?, ?)",
            (patient_id, soap_note),
        )
        return cursor.lastrowid


def get_evolution(evolution_id: int, db_path: str = DB_PATH) -> Optional[dict]:
    with managed_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM evolutions WHERE id = ?", (evolution_id,)
        ).fetchone()
        return dict(row) if row else None


def get_evolutions_by_patient(patient_id: int, db_path: str = DB_PATH) -> list[dict]:
    with managed_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM evolutions WHERE patient_id = ? ORDER BY created_at DESC",
            (patient_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def update_evolution(evolution_id: int, soap_note: str, db_path: str = DB_PATH) -> bool:
    with managed_connection(db_path) as conn:
        cursor = conn.execute(
            "UPDATE evolutions SET soap_note = ? WHERE id = ?",
            (soap_note, evolution_id),
        )
        return cursor.rowcount > 0


def delete_evolution(evolution_id: int, db_path: str = DB_PATH) -> bool:
    with managed_connection(db_path) as conn:
        cursor = conn.execute(
            "DELETE FROM evolutions WHERE id = ?", (evolution_id,)
        )
        return cursor.rowcount > 0