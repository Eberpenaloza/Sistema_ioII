"""Cálculos de inventarios: clasificación ABC, lote económico (EOQ), stock de seguridad y ROP."""
import numpy as np


def productos_validos(df):
    """Filtra los productos con demanda, costo por pedido y mantenimiento positivos."""
    d = df.dropna(subset=["nombre", "demanda", "pedido", "mantenimiento"]).copy()
    return d[(d.demanda > 0) & (d.pedido > 0) & (d.mantenimiento > 0)]


def clasificar_abc(d):
    """Clasificación ABC por valor anual: A hasta 80 %, B hasta 95 %, C el resto."""
    d = d.copy()
    d["V"] = d.demanda * d.costo
    d = d.sort_values("V", ascending=False)
    d["% acum."] = d.V.cumsum() / d.V.sum() * 100
    d["Clase"] = np.where((d["% acum."] <= 80) | (np.arange(len(d)) == 0), "A",
                          np.where(d["% acum."] <= 95, "B", "C"))
    return d


def calcular_eoq(d, dias, z):
    """Lote económico, costos, stock de seguridad, punto de pedido (ROP) y estado del stock."""
    d = d.copy()
    d["Q*"] = np.sqrt(2 * d.demanda * d.pedido / d.mantenimiento)
    d["Pedidos/año"] = d.demanda / d["Q*"]
    d["Días entre pedidos"] = d["Q*"] / d.demanda * dias
    d["Costo pedido"] = d["Pedidos/año"] * d.pedido
    d["Costo mantenimiento"] = d["Q*"] / 2 * d.mantenimiento
    d["CT relevante"] = d["Costo pedido"] + d["Costo mantenimiento"]
    d["Stock seguridad"] = z * d.desv_diaria.fillna(0) * np.sqrt(d.plazo)
    d["ROP"] = d.demanda / dias * d.plazo + d["Stock seguridad"]
    d["Estado"] = np.where(d.stock.fillna(0) <= d.ROP, "REPONER", "OK")
    return d
