# codigo/config/db.py
"""
Conector DB centralizado.
"""
from __future__ import annotations
import os
from typing import Any, Dict
import pymysql
from dotenv import load_dotenv

# Carga variables de entorno
load_dotenv()

def get_db_config() -> Dict[str, Any]:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", ""),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
    }

def connect():
    return pymysql.connect(**get_db_config())
