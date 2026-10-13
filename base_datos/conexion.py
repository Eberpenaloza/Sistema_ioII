"""Conexión y consultas a la base de datos SQLite (boulevard.db)."""
import sqlite3
from pathlib import Path

import pandas as pd

RUTA_BD = Path(__file__).resolve().parent.parent / "boulevard.db"


def ejecutar(sql, parametros=()):
    """Ejecuta una sentencia y devuelve el id de la última fila insertada."""
    with sqlite3.connect(RUTA_BD) as con:
        return con.execute(sql, parametros).lastrowid


def ejecutar_varios(sql, filas):
    """Ejecuta una sentencia para varias filas."""
    with sqlite3.connect(RUTA_BD) as con:
        con.executemany(sql, filas)


def consultar(sql, parametros=()):
    """Ejecuta una consulta y devuelve el resultado como DataFrame."""
    with sqlite3.connect(RUTA_BD) as con:
        return pd.read_sql_query(sql, con, params=parametros)
