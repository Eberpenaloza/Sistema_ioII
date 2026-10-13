"""Pestaña de Inventarios: edición de productos, clasificación ABC, EOQ y alertas de reposición."""
import streamlit as st

from base_datos import ejecutar, ejecutar_varios, consultar
from utilidades import filas_para_bd
from .calculos import productos_validos, clasificar_abc, calcular_eoq

COLUMNAS_EOQ = ["nombre", "Q*", "Pedidos/año", "Días entre pedidos", "Costo pedido", "Costo mantenimiento",
                "CT relevante", "Stock seguridad", "ROP", "stock", "Estado"]


def mostrar_inventarios():
    dias, z = _editar_parametros()
    productos = _editar_productos()
    if st.button("💾 Guardar inventario"):
        _guardar_inventario(productos, dias, z)

    d = productos_validos(productos)
    if d.empty:
        st.error("Ingrese productos con demanda, costo por pedido y mantenimiento positivos.")
        return
    d = calcular_eoq(clasificar_abc(d), dias, z)
    _mostrar_abc(d)
    _mostrar_eoq(d)


# ---------------------------------------------------------------- Datos
def _editar_parametros():
    config = dict(consultar("SELECT clave,valor FROM config").values)
    c1, c2 = st.columns(2)
    dias = c1.number_input("Días laborables por año", value=float(config.get("dias", 300)))
    z = c2.number_input("z (nivel de servicio; 1.65 ≈ 95 %)", value=float(config.get("z", 1.65)))
    return dias, z


def _editar_productos():
    productos = consultar("SELECT nombre,demanda,costo,pedido,mantenimiento,plazo,desv_diaria,stock FROM productos")
    st.caption("H = costo anual de mantener una unidad (S/ por unidad al año); "
               "no se multiplica de nuevo por el costo unitario.")
    return st.data_editor(productos, num_rows="dynamic", width="stretch", key="productos")


def _guardar_inventario(productos, dias, z):
    ejecutar("DELETE FROM productos")
    ejecutar_varios(
        "INSERT INTO productos(nombre,demanda,costo,pedido,mantenimiento,plazo,desv_diaria,stock) VALUES(?,?,?,?,?,?,?,?)",
        filas_para_bd(productos))
    ejecutar_varios("INSERT OR REPLACE INTO config VALUES(?,?)", [("dias", dias), ("z", z)])
    st.success("Guardado en SQLite.")


# ---------------------------------------------------------------- Resultados
def _mostrar_abc(d):
    st.subheader("Clasificación ABC (A hasta 80 %, B hasta 95 %, C resto)")
    st.dataframe(d[["nombre", "V", "% acum.", "Clase"]].round(1), width="stretch", hide_index=True)


def _mostrar_eoq(d):
    st.subheader("EOQ, punto de pedido y costos")
    st.dataframe(d[COLUMNAS_EOQ].round(2), width="stretch", hide_index=True)
    for _, r in d[d.Estado == "REPONER"].iterrows():
        st.warning(f"{r.nombre}: stock ({r.stock:g}) ≤ punto de pedido ({r.ROP:.1f}). "
                   f"Riesgo de desabastecimiento; pedir {r['Q*']:.0f} unid.")
    st.bar_chart(d.set_index("nombre")[["Costo pedido", "Costo mantenimiento"]])
