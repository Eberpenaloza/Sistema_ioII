"""Cálculos PERT/CPM: tiempos más tempranos y más tardíos, holguras y ruta crítica."""
import math

from utilidades import a_numero


def calcular_red(df, modo):
    """Calcula la red del proyecto.

    Devuelve (resultado, errores). `resultado` es None si hay errores; si no, un dict con:
    A (datos por actividad), orden (topológico), T (duración), crit (ruta crítica), V (varianza).
    """
    A, errores = _leer_actividades(df, modo)
    if not A:
        return None, errores or ["Registre al menos una actividad."]
    for k, act in A.items():
        for p in act["pr"]:
            if p not in A:
                errores.append(f"{k}: predecesora inexistente ({p})")
            else:
                A[p]["su"].append(k)
    if errores:
        return None, errores

    orden = _orden_topologico(A)
    if len(orden) < len(A):
        return None, ["Dependencia circular detectada en las precedencias."]

    # Pasada hacia adelante: inicio (IT) y fin (FT) más tempranos
    for k in orden:
        act = A[k]
        act["IT"] = max([A[p]["FT"] for p in act["pr"]], default=0)
        act["FT"] = act["IT"] + act["te"]
    T = max(act["FT"] for act in A.values())

    # Pasada hacia atrás: inicio (IL) y fin (FL) más tardíos y holgura (H)
    for k in reversed(orden):
        act = A[k]
        act["FL"] = min([A[s]["IL"] for s in act["su"]], default=T)
        act["IL"] = act["FL"] - act["te"]
        act["H"] = round(act["IL"] - act["IT"], 9)

    crit = [k for k in orden if A[k]["H"] == 0]
    V = sum(A[k]["var"] for k in crit)
    return dict(A=A, orden=orden, T=T, crit=crit, V=V), []


def probabilidad_plazo(T, V, plazo):
    """Probabilidad (aproximación normal) de terminar dentro del plazo. Devuelve (z, probabilidad)."""
    z = (plazo - T) / math.sqrt(V) if V > 0 else (9 if plazo >= T else -9)
    return z, 0.5 * math.erfc(-z / math.sqrt(2))


def _leer_actividades(df, modo):
    A, errores = {}, []
    for _, fila in df.iterrows():
        k = str(fila["codigo"] or "").strip().upper()
        if k in ("", "NONE", "NAN"):
            continue
        if k in A:
            errores.append(f"Código repetido: {k}")
        if modo == "PERT":
            a, m, b = a_numero(fila["a"]), a_numero(fila["m"]), a_numero(fila["b"])
            if not a <= m <= b:
                errores.append(f"{k}: debe cumplirse a ≤ m ≤ b")
            te, var = (a + 4 * m + b) / 6, ((b - a) / 6) ** 2
        else:
            te, var = a_numero(fila["duracion"]), 0.0
        if te < 0:
            errores.append(f"{k}: duración negativa")
        pr = [p.strip().upper() for p in str(fila["predecesoras"] or "").split(",") if p.strip()]
        A[k] = dict(nombre=fila["nombre"], te=te, var=var, pr=pr, su=[], real=fila["real"])
    return A, errores


def _orden_topologico(A):
    grado = {k: len(act["pr"]) for k, act in A.items()}
    cola, orden = [k for k, g in grado.items() if g == 0], []
    while cola:
        k = cola.pop(0)
        orden.append(k)
        for s in A[k]["su"]:
            grado[s] -= 1
            if grado[s] == 0:
                cola.append(s)
    return orden
