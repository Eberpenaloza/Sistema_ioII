"""Sistema de apoyo a la toma de decisiones - Investigación Operativa II
Boulevard Import S.A.C. (caso simulado). Python + Streamlit + SQLite.

Ejecutar:  streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="Boulevard Import - IO II", layout="wide")

from base_datos import inicializar_base_datos
from modulos.pert_cpm import mostrar_pert_cpm
from modulos.inventarios import mostrar_inventarios
from modulos.teoria_decisiones import mostrar_teoria_decisiones

inicializar_base_datos()

st.title("Sistema de apoyo a la toma de decisiones - Boulevard Import S.A.C.")
st.caption("Investigación Operativa II · Caso simulado con fines académicos · Base de datos: SQLite (boulevard.db)")

pestana_pert, pestana_inventarios, pestana_decisiones = st.tabs(["PERT/CPM", "Inventarios", "Teoría de decisiones"])
with pestana_pert:
    mostrar_pert_cpm()
with pestana_inventarios:
    mostrar_inventarios()
with pestana_decisiones:
    mostrar_teoria_decisiones()
