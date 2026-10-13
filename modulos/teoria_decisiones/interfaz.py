"""Pestaña de Teoría de decisiones: matriz de pagos, criterios, valor esperado y árbol de decisión."""
import json
import math
import sqlite3

import pandas as pd
import streamlit as st

from base_datos import ejecutar, consultar
from .calculos import criterios_incertidumbre, matriz_arrepentimiento, valor_esperado


def mostrar_teoria_decisiones():
    caso = _seleccionar_caso()
    tipo = st.radio("Tipo de matriz", ["Costos", "Beneficios"],
                    index=["Costos", "Beneficios"].index(caso.tipo), horizontal=True)
    alpha = st.slider("α de Hurwicz (optimismo)", 0.0, 1.0, float(caso.alpha))
    escenarios = [e.strip() for e in st.text_input("Escenarios (separados por coma)", caso.estados).split(",")
                  if e.strip()]
    matriz, probabilidades = _editar_matriz(caso, escenarios)
    if st.button("💾 Guardar caso"):
        _guardar_caso(int(caso.id), tipo, alpha, escenarios, matriz, probabilidades)

    matriz = matriz.dropna(subset=["Alternativa"])
    if matriz.empty or not escenarios:
        return
    M = matriz[escenarios].astype(float).values
    alternativas = list(matriz.Alternativa)
    p = probabilidades.iloc[0].astype(float).values
    es_costo = tipo == "Costos"

    _mostrar_criterios(M, alternativas, escenarios, es_costo, alpha)
    st.subheader("Valor esperado")
    if not math.isclose(p.sum(), 1, abs_tol=1e-6):
        st.error(f"Las probabilidades suman {p.sum():.3f}; deben sumar 1.")
        return
    ve = _mostrar_valor_esperado(M, alternativas, p, es_costo)
    _mostrar_arbol(M, alternativas, escenarios, p, ve, es_costo)


# ---------------------------------------------------------------- Datos del caso
def _seleccionar_caso():
    casos = consultar("SELECT * FROM decisiones")
    c1, c2 = st.columns([3, 2])
    nombre = c1.selectbox("Caso de decisión", casos.nombre)
    nuevo = c2.text_input("Nuevo caso", placeholder="Nombre y presione Enter")
    if nuevo:
        try:
            ejecutar("INSERT INTO decisiones(nombre,tipo,alpha,estados,matriz,probs) VALUES(?,?,?,?,?,?)",
                     (nuevo, "Costos", 0.5, "Demanda baja,Demanda media,Demanda alta",
                      json.dumps({"Proveedor A": [0, 0, 0]}), json.dumps([0.3, 0.4, 0.3])))
            st.rerun()
        except sqlite3.IntegrityError:
            c2.warning("Ya existe ese caso.")
    return casos[casos.nombre == nombre].iloc[0]


def _editar_matriz(caso, escenarios):
    n = len(escenarios)
    valores = json.loads(caso.matriz)
    df = pd.DataFrame([[alt] + (fila + [0] * n)[:n] for alt, fila in valores.items()],
                      columns=["Alternativa"] + escenarios)
    st.caption("Los valores iniciales son datos simulados de ejemplo; reemplácelos con las cotizaciones del caso.")
    matriz = st.data_editor(df, num_rows="dynamic", width="stretch", key=f"matriz_{caso.id}_{n}")
    probs = (json.loads(caso.probs) + [0] * n)[:n]
    probabilidades = st.data_editor(pd.DataFrame([probs], columns=escenarios), hide_index=True,
                                    width="stretch", key=f"probs_{caso.id}_{n}")
    return matriz, probabilidades


def _guardar_caso(caso_id, tipo, alpha, escenarios, matriz, probabilidades):
    valores = {str(alt): [float(x) for x in fila]
               for alt, fila in zip(matriz.Alternativa, matriz[escenarios].values.tolist())}
    ejecutar("UPDATE decisiones SET tipo=?,alpha=?,estados=?,matriz=?,probs=? WHERE id=?",
             (tipo, alpha, ",".join(escenarios), json.dumps(valores),
              json.dumps([float(x) for x in probabilidades.iloc[0]]), caso_id))
    st.success("Guardado en SQLite.")


# ---------------------------------------------------------------- Resultados
def _mostrar_criterios(M, alternativas, escenarios, es_costo, alpha):
    st.subheader("Criterios bajo incertidumbre")
    st.dataframe(pd.DataFrame(criterios_incertidumbre(M, alternativas, es_costo, alpha)),
                 width="stretch", hide_index=True)
    with st.expander("Matriz de arrepentimiento"):
        st.dataframe(pd.DataFrame(matriz_arrepentimiento(M, es_costo), index=alternativas, columns=escenarios))


def _mostrar_valor_esperado(M, alternativas, p, es_costo):
    ve, recomendadas, veip = valor_esperado(M, alternativas, p, es_costo)
    st.dataframe(pd.DataFrame({"Alternativa": alternativas,
                               "Costo esperado" if es_costo else "VME": ve.round(2)}), hide_index=True)
    st.success(f"Alternativa recomendada: {', '.join(recomendadas)}   |   VEIP = {veip:.2f}")
    st.bar_chart(pd.Series(ve, index=alternativas))
    return ve


def _mostrar_arbol(M, alternativas, escenarios, p, ve, es_costo):
    st.subheader("Árbol de decisión (evaluado de derecha a izquierda)")
    optimo = ve.min() if es_costo else ve.max()
    dot = f'digraph{{rankdir=LR;D[shape=box,label="Decisión\\n{"mín" if es_costo else "máx"} = {optimo:.2f}"];'
    for i, alt in enumerate(alternativas):
        dot += f'D->N{i}[label="{alt}"];N{i}[shape=circle,label="{ve[i]:.1f}"];'
        for j in range(len(escenarios)):
            dot += f'N{i}->R{i}_{j}[label="p={p[j]:g}"];R{i}_{j}[shape=plaintext,label="{M[i, j]:g}"];'
    st.graphviz_chart(dot + "}")
