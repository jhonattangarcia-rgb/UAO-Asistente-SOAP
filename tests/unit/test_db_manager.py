import sqlite3
import pytest
from services.db_manager import (
    create_patient,
    get_patient,
    update_patient,
    delete_patient,
    create_evolution,
    get_evolution,
    get_evolutions_by_patient,
    update_evolution,
    delete_evolution,
)


@pytest.fixture
def db(monkeypatch):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

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
    conn.commit()

    import services.db_manager as db_module

    def fake_connection(db_path=None):
        return conn

    monkeypatch.setattr(db_module, "get_connection", fake_connection)

    import services.db_manager as mod
    from contextlib import contextmanager

    @contextmanager
    def fake_managed_connection(db_path=None):
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    monkeypatch.setattr(db_module, "managed_connection", fake_managed_connection)

    yield conn
    conn.close()


def test_create_and_get_patient(db):
    patient_id = create_patient("Maria Lopez", "12345678")
    patient = get_patient(patient_id)
    assert patient["name"] == "Maria Lopez"
    assert patient["document_id"] == "12345678"


def test_update_patient(db):
    patient_id = create_patient("Maria Lopez", "12345678")
    result = update_patient(patient_id, "Maria Garcia", "99999999")
    assert result is True
    patient = get_patient(patient_id)
    assert patient["name"] == "Maria Garcia"


def test_delete_patient(db):
    patient_id = create_patient("Maria Lopez", "12345678")
    result = delete_patient(patient_id)
    assert result is True
    assert get_patient(patient_id) is None


def test_get_patient_not_found(db):
    assert get_patient(999) is None


def test_create_and_get_evolution(db):
    patient_id = create_patient("Maria Lopez", "12345678")
    evolution_id = create_evolution(patient_id, "S: fiebre. O: T 38.5. A: infeccion. P: antibiotico.")
    evolution = get_evolution(evolution_id)
    assert evolution["soap_note"] == "S: fiebre. O: T 38.5. A: infeccion. P: antibiotico."
    assert evolution["patient_id"] == patient_id


def test_update_evolution(db):
    patient_id = create_patient("Maria Lopez", "12345678")
    evolution_id = create_evolution(patient_id, "nota inicial")
    result = update_evolution(evolution_id, "nota actualizada")
    assert result is True
    evolution = get_evolution(evolution_id)
    assert evolution["soap_note"] == "nota actualizada"


def test_delete_evolution(db):
    patient_id = create_patient("Maria Lopez", "12345678")
    evolution_id = create_evolution(patient_id, "nota inicial")
    result = delete_evolution(evolution_id)
    assert result is True
    assert get_evolution(evolution_id) is None


def test_get_evolutions_by_patient(db):
    patient_id = create_patient("Maria Lopez", "12345678")
    create_evolution(patient_id, "nota 1")
    create_evolution(patient_id, "nota 2")
    evolutions = get_evolutions_by_patient(patient_id)
    assert len(evolutions) == 2


def test_get_evolution_not_found(db):
    assert get_evolution(999) is None