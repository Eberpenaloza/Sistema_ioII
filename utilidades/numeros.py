"""Conversión de valores vacíos (None / NaN) provenientes de tablas editables."""
import pandas as pd


def a_numero(valor, por_defecto=0.0):
    """Convierte a float; si el valor está vacío devuelve `por_defecto`."""
    return por_defecto if valor is None or pd.isna(valor) else float(valor)


def filas_para_bd(df):
    """Convierte las filas de un DataFrame en tuplas, reemplazando NaN por None."""
    return [tuple(None if pd.isna(v) else v for v in fila) for fila in df.itertuples(index=False)]
