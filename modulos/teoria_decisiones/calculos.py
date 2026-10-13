"""Cálculos de teoría de decisiones: criterios bajo incertidumbre y bajo riesgo (valor esperado)."""
import numpy as np


def _funciones(es_costo):
    """Devuelve (mejor, peor) según se trate de una matriz de costos o de beneficios."""
    return (np.min, np.max) if es_costo else (np.max, np.min)


def _elegir(valores, alternativas, funcion):
    """Alternativas cuyo valor coincide con el óptimo (puede haber empates)."""
    return [alternativas[i] for i in np.flatnonzero(np.isclose(valores, funcion(valores)))]


def matriz_arrepentimiento(M, es_costo):
    mejor, _ = _funciones(es_costo)
    return np.abs(mejor(M, axis=0) - M)


def criterios_incertidumbre(M, alternativas, es_costo, alpha):
    """Evalúa Optimista, Pesimista (Wald), Laplace, Hurwicz y Savage.

    Devuelve una lista de filas: {"Criterio", <alternativa>: valor, ..., "Recomendada"}.
    """
    mejor, peor = _funciones(es_costo)
    criterios = {
        ("Optimista (mín. de mínimos)" if es_costo else "Maximax"): mejor(M, axis=1),
        ("Pesimista - Wald" if es_costo else "Maximin"): peor(M, axis=1),
        "Laplace": M.mean(axis=1),
        f"Hurwicz (α={alpha:g})": alpha * mejor(M, axis=1) + (1 - alpha) * peor(M, axis=1),
    }
    filas = [{"Criterio": nombre, **dict(zip(alternativas, np.round(v, 2))),
              "Recomendada": ", ".join(_elegir(v, alternativas, mejor))}
             for nombre, v in criterios.items()]
    savage = matriz_arrepentimiento(M, es_costo).max(axis=1)
    filas.append({"Criterio": "Savage (mín. arrepentimiento máx.)", **dict(zip(alternativas, np.round(savage, 2))),
                  "Recomendada": ", ".join(_elegir(savage, alternativas, np.min))})
    return filas


def valor_esperado(M, alternativas, p, es_costo):
    """Valor esperado por alternativa, alternativa(s) recomendada(s) y VEIP."""
    mejor, _ = _funciones(es_costo)
    ve = M @ p
    recomendadas = _elegir(ve, alternativas, mejor)
    con_informacion = mejor(M, axis=0) @ p
    veip = (ve.min() - con_informacion) if es_costo else (con_informacion - ve.max())
    return ve, recomendadas, veip
