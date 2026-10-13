"""Pestaña PERT/CPM: edición de actividades, resultados, diagrama de red, Gantt y seguimiento."""
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from base_datos import ejecutar, ejecutar_varios, consultar
from utilidades import a_numero, filas_para_bd
from .calculos import calcular_red, probabilidad_plazo


def mostrar_pert_cpm():
    proyecto = _seleccionar_proyecto()
    modo = st.radio("Método", ["CPM", "PERT"], index=["CPM", "PERT"].index(proyecto.modo), horizontal=True)
    actividades = _editar_actividades(proyecto, modo)
    plazo = st.number_input("Plazo objetivo T (para PERT)", value=float(proyecto.plazo))
    if st.button("💾 Guardar proyecto"):
        _guardar_proyecto(int(proyecto.id), modo, plazo, actividades)

    R, errores = calcular_red(actividades, modo)
    for e in errores:
        st.error(e)
    if not R:
        return
    _mostrar_resultados(R, modo, plazo)
    _mostrar_diagrama_red(R)
    _mostrar_gantt(R)
    _mostrar_seguimiento(R)


# ---------------------------------------------------------------- Datos del proyecto
def _seleccionar_proyecto():
    proyectos = consultar("SELECT * FROM proyectos")
    c1, c2 = st.columns([3, 2])
    nombre = c1.selectbox("Proyecto", proyectos.nombre)
    nuevo = c2.text_input("Nuevo proyecto", placeholder="Nombre y presione Enter")
    if nuevo:
        try:
            ejecutar("INSERT INTO proyectos(nombre) VALUES(?)", (nuevo,))
            st.rerun()
        except sqlite3.IntegrityError:
            c2.warning("Ya existe un proyecto con ese nombre.")
    return proyectos[proyectos.nombre == nombre].iloc[0]


def _editar_actividades(proyecto, modo):
    actividades = consultar(
        "SELECT codigo,nombre,predecesoras,duracion,a,m,b,real FROM actividades WHERE proyecto_id=?",
        (int(proyecto.id),))
    st.caption("Predecesoras separadas por coma (ej. B,C). CPM usa 'duracion'; PERT usa a, m, b. "
               "'real' = duración real (seguimiento).")
    columnas = ["codigo", "nombre", "predecesoras"] + (["a", "m", "b"] if modo == "PERT" else ["duracion"]) + ["real"]
    return st.data_editor(actividades, num_rows="dynamic", width="stretch",
                          key=f"actividades_{proyecto.id}", column_order=columnas)


def _guardar_proyecto(proyecto_id, modo, plazo, actividades):
    ejecutar("UPDATE proyectos SET modo=?, plazo=? WHERE id=?", (modo, plazo, proyecto_id))
    ejecutar("DELETE FROM actividades WHERE proyecto_id=?", (proyecto_id,))
    ejecutar_varios(
        "INSERT INTO actividades(proyecto_id,codigo,nombre,predecesoras,duracion,a,m,b,real) VALUES(?,?,?,?,?,?,?,?,?)",
        [(proyecto_id, *fila) for fila in filas_para_bd(actividades)])
    st.success("Guardado en SQLite.")


# ---------------------------------------------------------------- Resultados
def _mostrar_resultados(R, modo, plazo):
    A = R["A"]
    st.subheader("Resultados")
    k1, k2, k3 = st.columns(3)
    k1.metric("Duración total", f"{R['T']:.2f}")
    k2.metric("Ruta crítica", " → ".join(R["crit"]))
    if modo == "PERT":
        k3.metric("Varianza ruta crítica", f"{R['V']:.3f}")
        z, prob = probabilidad_plazo(R["T"], R["V"], plazo)
        st.info(f"Z = {z:.3f}  →  P(T* ≤ {plazo:g}) ≈ {prob * 100:.1f} %  (aproximación normal)")
    tabla = pd.DataFrame([{
        "Act.": k, "Actividad": A[k]["nombre"], "Duración": round(A[k]["te"], 3),
        "IT": A[k]["IT"], "FT": A[k]["FT"], "IL": A[k]["IL"], "FL": A[k]["FL"], "Holgura": A[k]["H"],
        "Estado": "CRÍTICA" if k in R["crit"] else "con holgura",
    } for k in R["orden"]])
    st.dataframe(tabla, width="stretch", hide_index=True)


def _mostrar_diagrama_red(R):
    A, crit = R["A"], R["crit"]
    dot = "digraph{rankdir=LR;node[shape=box,style=rounded];"
    for k in R["orden"]:
        color = "red" if k in crit else "gray40"
        dot += f'{k}[label="{k} ({A[k]["te"]:.1f})\\n{A[k]["IT"]:.1f} | {A[k]["FT"]:.1f}",color={color}];'
        for s in A[k]["su"]:
            dot += f'{k}->{s}[color={"red" if k in crit and s in crit else "gray"}];'
    st.subheader("Diagrama de red (rojo = ruta crítica)")
    st.graphviz_chart(dot + "}")


def _mostrar_gantt(R):
    A = R["A"]
    st.subheader("Cronograma Gantt")
    orden = sorted(A, key=lambda k: A[k]["IT"])
    fig, ax = plt.subplots(figsize=(9, 0.5 * len(A) + 1))
    for i, k in enumerate(orden):
        ax.barh(i, A[k]["te"], left=A[k]["IT"], color="tab:red" if k in R["crit"] else "tab:blue")
        if not pd.isna(A[k]["real"]):
            ax.barh(i + 0.35, a_numero(A[k]["real"]), left=A[k]["IT"], height=0.15, color="gray")
    ax.set_yticks(range(len(A)))
    ax.set_yticklabels(orden)
    ax.invert_yaxis()
    ax.set_xlabel("Tiempo")
    st.pyplot(fig)


def _mostrar_seguimiento(R):
    A = R["A"]
    hechas = [k for k in A if not pd.isna(A[k]["real"])]
    st.write(f"**Avance:** {len(hechas)}/{len(A)} actividades con duración real.")
    atrasadas = [k for k in hechas if a_numero(A[k]["real"]) > A[k]["te"] + 1e-9]
    for k in atrasadas:
        st.warning(f"Actividad {k} retrasada: real {a_numero(A[k]['real']):g} vs plan {A[k]['te']:g}"
                   + (" (es crítica: retrasa el proyecto)" if k in R["crit"] else ""))
    if not atrasadas:
        st.success("Sin actividades retrasadas.")
