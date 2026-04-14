import sqlite3
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "casino.db"

def get_db_connection():
    """Establece una conexión con la base de datos SQLite."""
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos y crea las tablas necesarias."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabla de usuarios unificada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            security_question TEXT,
            security_answer_hash TEXT,
            saldo REAL DEFAULT 0.0,
            historial TEXT DEFAULT '[]',
            estadisticas_globales TEXT DEFAULT '{}'
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Base de datos inicializada en: {DB_PATH}")

if __name__ == "__main__":
    init_db()
