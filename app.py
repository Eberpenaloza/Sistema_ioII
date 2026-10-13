"""Sistema de apoyo a la toma de decisiones - Investigación Operativa II
Boulevard Import S.A.C. (caso simulado). Python + Streamlit + SQLite.
Ejecutar:  streamlit run app.py
"""
import json, math, sqlite3
import numpy as np, pandas as pd, streamlit as st
import matplotlib.pyplot as plt

DB = "boulevard.db"
st.set_page_config(page_title="Boulevard Import - IO II", layout="wide")

# ---------------------------------------------------------------- BASE DE DATOS
def run(sql, p=()):
    with sqlite3.connect(DB) as c:
        return c.execute(sql, p).lastrowid

def many(sql, rows):
    with sqlite3.connect(DB) as c:
        c.executemany(sql, rows)

def read(sql, p=()):
    with sqlite3.connect(DB) as c:
        return pd.read_sql_query(sql, c, params=p)

def init_db():
    run("""CREATE TABLE IF NOT EXISTS proyectos(id INTEGER PRIMARY KEY, nombre TEXT UNIQUE,
           modo TEXT DEFAULT 'CPM', plazo REAL DEFAULT 10)""")
    run("""CREATE TABLE IF NOT EXISTS actividades(id INTEGER PRIMARY KEY, proyecto_id INTEGER,
           codigo TEXT, nombre TEXT, predecesoras TEXT, duracion REAL, a REAL, m REAL, b REAL, real REAL,
           FOREIGN KEY(proyecto_id) REFERENCES proyectos(id))""")
    run("""CREATE TABLE IF NOT EXISTS productos(id INTEGER PRIMARY KEY, nombre TEXT, demanda REAL,
           costo REAL, pedido REAL, mantenimiento REAL, plazo REAL, desv_diaria REAL, stock REAL)""")
    run("CREATE TABLE IF NOT EXISTS config(clave TEXT PRIMARY KEY, valor REAL)")
    run("""CREATE TABLE IF NOT EXISTS decisiones(id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, tipo TEXT,
           alpha REAL, estados TEXT, matriz TEXT, probs TEXT)""")
    if read("SELECT COUNT(*) n FROM proyectos").n[0] == 0:  # datos de ejemplo (simulados)
        pid = run("INSERT INTO proyectos(nombre,modo,plazo) VALUES('Reorganización del almacén','CPM',13)")
        A = [("A","Diseñar la distribución","",3),("B","Despejar y preparar el área","A",2),
             ("C","Adquirir estanterías y señalización","A",4),("D","Instalar estanterías","B,C",3),
             ("E","Organizar y etiquetar productos","D",2),("F","Verificar seguridad y distribución","E",1)]
        many("INSERT INTO actividades(proyecto_id,codigo,nombre,predecesoras,duracion,a,m,b) VALUES(?,?,?,?,?,?,?,?)",
             [(pid,c,n,p,d,max(d-1,0),d,d+1) for c,n,p,d in A])
        many("INSERT INTO productos(nombre,demanda,costo,pedido,mantenimiento,plazo,desv_diaria,stock) VALUES(?,?,?,?,?,?,?,?)",
             [("Laptop de oficina",600,2200,80,220,5,2,30),("Impresora multifuncional",480,750,60,75,4,1.5,25),
              ("Teclado y mouse",1200,85,35,8.5,3,4,60)])
        many("INSERT INTO config VALUES(?,?)", [("dias",300),("z",1.65)])
        run("INSERT INTO decisiones(nombre,tipo,alpha,estados,matriz,probs) VALUES(?,?,?,?,?,?)",
            ("Selección de proveedor (ejemplo simulado)","Costos",0.5,"Demanda baja,Demanda media,Demanda alta",
             json.dumps({"Proveedor A":[100,120,150],"Proveedor B":[110,115,130],"Proveedor C":[105,125,140]}),
             json.dumps([0.3,0.5,0.2])))

nz = lambda x, d=0.0: d if x is None or (isinstance(x, float) and math.isnan(x)) else float(x)

# ---------------------------------------------------------------- PERT / CPM
def calc_pert(df, modo):
    A, err = {}, []
    for _, r in df.iterrows():
        k = str(r["codigo"] or "").strip().upper()
        if k in ("", "NONE", "NAN"): continue
        if k in A: err.append(f"Código repetido: {k}")
        if modo == "PERT":
            a, m, b = nz(r["a"]), nz(r["m"]), nz(r["b"])
            if not a <= m <= b: err.append(f"{k}: debe cumplirse a ≤ m ≤ b")
            te, var = (a + 4 * m + b) / 6, ((b - a) / 6) ** 2
        else:
            te, var = nz(r["duracion"]), 0.0
        if te < 0: err.append(f"{k}: duración negativa")
        pr = [p.strip().upper() for p in str(r["predecesoras"] or "").split(",") if p.strip()]
        A[k] = dict(nombre=r["nombre"], te=te, var=var, pr=pr, su=[], real=r["real"])
    if not A: return None, ["Registre al menos una actividad."]
    for k, a in A.items():
        for p in a["pr"]:
            if p not in A: err.append(f"{k}: predecesora inexistente ({p})")
            else: A[p]["su"].append(k)
    if err: return None, err
    indeg = {k: len(a["pr"]) for k, a in A.items()}
    cola, orden = [k for k, v in indeg.items() if v == 0], []
    while cola:
        k = cola.pop(0); orden.append(k)
        for s in A[k]["su"]:
            indeg[s] -= 1
            if indeg[s] == 0: cola.append(s)
    if len(orden) < len(A): return None, ["Dependencia circular detectada en las precedencias."]
    for k in orden:
        a = A[k]
        a["IT"] = max([A[p]["FT"] for p in a["pr"]], default=0)
        a["FT"] = a["IT"] + a["te"]
    T = max(a["FT"] for a in A.values())
    for k in reversed(orden):
        a = A[k]
        a["FL"] = min([A[s]["IL"] for s in a["su"]], default=T)
        a["IL"] = a["FL"] - a["te"]
        a["H"] = round(a["IL"] - a["IT"], 9)
    crit = [k for k in orden if A[k]["H"] == 0]
    V = sum(A[k]["var"] for k in crit)
    return dict(A=A, orden=orden, T=T, crit=crit, V=V), []

def tab_pert():
    proyectos = read("SELECT * FROM proyectos")
    c1, c2 = st.columns([3, 2])
    nombre = c1.selectbox("Proyecto", proyectos.nombre)
    p = proyectos[proyectos.nombre == nombre].iloc[0]
    nuevo = c2.text_input("Nuevo proyecto", placeholder="Nombre y presione Enter")
    if nuevo:
        try: run("INSERT INTO proyectos(nombre) VALUES(?)", (nuevo,)); st.rerun()
        except sqlite3.IntegrityError: c2.warning("Ya existe un proyecto con ese nombre.")
    modo = st.radio("Método", ["CPM", "PERT"], index=["CPM", "PERT"].index(p.modo), horizontal=True)
    acts = read("SELECT codigo,nombre,predecesoras,duracion,a,m,b,real FROM actividades WHERE proyecto_id=?", (int(p.id),))
    st.caption("Predecesoras separadas por coma (ej. B,C). CPM usa 'duracion'; PERT usa a, m, b. 'real' = duración real (seguimiento).")
    cols = ["codigo", "nombre", "predecesoras"] + (["a", "m", "b"] if modo == "PERT" else ["duracion"]) + ["real"]
    ed = st.data_editor(acts, num_rows="dynamic", use_container_width=True, key=f"act{p.id}", column_order=cols)
    plazo = st.number_input("Plazo objetivo T (para PERT)", value=float(p.plazo))
    if st.button("💾 Guardar proyecto", key="gp"):
        run("UPDATE proyectos SET modo=?, plazo=? WHERE id=?", (modo, plazo, int(p.id)))
        run("DELETE FROM actividades WHERE proyecto_id=?", (int(p.id),))
        many("INSERT INTO actividades(proyecto_id,codigo,nombre,predecesoras,duracion,a,m,b,real) VALUES(?,?,?,?,?,?,?,?,?)",
             [(int(p.id), *[None if pd.isna(v) else v for v in r]) for r in ed.itertuples(index=False)])
        st.success("Guardado en SQLite.")
    R, err = calc_pert(ed, modo)
    for e in err: st.error(e)
    if not R: return
    A = R["A"]
    st.subheader("Resultados")
    k1, k2, k3 = st.columns(3)
    k1.metric("Duración total", f"{R['T']:.2f}")
    k2.metric("Ruta crítica", " → ".join(R["crit"]))
    if modo == "PERT":
        k3.metric("Varianza ruta crítica", f"{R['V']:.3f}")
        z = (plazo - R["T"]) / math.sqrt(R["V"]) if R["V"] > 0 else (9 if plazo >= R["T"] else -9)
        st.info(f"Z = {z:.3f}  →  P(T* ≤ {plazo:g}) ≈ {0.5 * math.erfc(-z / math.sqrt(2)) * 100:.1f} %  (aproximación normal)")
    st.dataframe(pd.DataFrame([{"Act.": k, "Actividad": A[k]["nombre"], "Duración": round(A[k]["te"], 3),
        "IT": A[k]["IT"], "FT": A[k]["FT"], "IL": A[k]["IL"], "FL": A[k]["FL"], "Holgura": A[k]["H"],
        "Estado": "CRÍTICA" if k in R["crit"] else "con holgura"} for k in R["orden"]]), use_container_width=True, hide_index=True)
    dot = "digraph{rankdir=LR;node[shape=box,style=rounded];"
    for k in R["orden"]:
        col = "red" if k in R["crit"] else "gray40"
        dot += f'{k}[label="{k} ({A[k]["te"]:.1f})\\n{A[k]["IT"]:.1f} | {A[k]["FT"]:.1f}",color={col}];'
        for s in A[k]["su"]:
            dot += f'{k}->{s}[color={"red" if k in R["crit"] and s in R["crit"] else "gray"}];'
    st.subheader("Diagrama de red (rojo = ruta crítica)")
    st.graphviz_chart(dot + "}")
    st.subheader("Cronograma Gantt")
    fig, ax = plt.subplots(figsize=(9, 0.5 * len(A) + 1))
    for i, k in enumerate(sorted(A, key=lambda x: A[x]["IT"])):
        ax.barh(i, A[k]["te"], left=A[k]["IT"], color="tab:red" if k in R["crit"] else "tab:blue")
        if not pd.isna(A[k]["real"]): ax.barh(i + 0.35, nz(A[k]["real"]), left=A[k]["IT"], height=0.15, color="gray")
    ax.set_yticks(range(len(A))); ax.set_yticklabels(sorted(A, key=lambda x: A[x]["IT"])); ax.invert_yaxis()
    ax.set_xlabel("Tiempo"); st.pyplot(fig)
    hechas = [k for k in A if not pd.isna(A[k]["real"])]
    st.write(f"**Avance:** {len(hechas)}/{len(A)} actividades con duración real.")
    atras = [k for k in hechas if nz(A[k]["real"]) > A[k]["te"] + 1e-9]
    for k in atras:
        st.warning(f"Actividad {k} retrasada: real {nz(A[k]['real']):g} vs plan {A[k]['te']:g}"
                   + (" (es crítica: retrasa el proyecto)" if k in R["crit"] else ""))
    if not atras: st.success("Sin actividades retrasadas.")

# ---------------------------------------------------------------- INVENTARIOS
def tab_inv():
    cfg = dict(read("SELECT clave,valor FROM config").values)
    c1, c2 = st.columns(2)
    dias = c1.number_input("Días laborables por año", value=float(cfg.get("dias", 300)))
    z = c2.number_input("z (nivel de servicio; 1.65 ≈ 95 %)", value=float(cfg.get("z", 1.65)))
    prod = read("SELECT nombre,demanda,costo,pedido,mantenimiento,plazo,desv_diaria,stock FROM productos")
    st.caption("H = costo anual de mantener una unidad (S/ por unidad al año); no se multiplica de nuevo por el costo unitario.")
    ed = st.data_editor(prod, num_rows="dynamic", use_container_width=True, key="prod")
    if st.button("💾 Guardar inventario"):
        run("DELETE FROM productos")
        many("INSERT INTO productos(nombre,demanda,costo,pedido,mantenimiento,plazo,desv_diaria,stock) VALUES(?,?,?,?,?,?,?,?)",
             [tuple(None if pd.isna(v) else v for v in r) for r in ed.itertuples(index=False)])
        many("INSERT OR REPLACE INTO config VALUES(?,?)", [("dias", dias), ("z", z)])
        st.success("Guardado en SQLite.")
    d = ed.dropna(subset=["nombre", "demanda", "pedido", "mantenimiento"]).copy()
    d = d[(d.demanda > 0) & (d.pedido > 0) & (d.mantenimiento > 0)]
    if d.empty: return st.error("Ingrese productos con demanda, costo por pedido y mantenimiento positivos.")
    d["V"] = d.demanda * d.costo
    d = d.sort_values("V", ascending=False)
    prev = d.V.cumsum().shift(fill_value=0) / d.V.sum() * 100
    d["% acum."] = d.V.cumsum() / d.V.sum() * 100
    d["Clase"] = np.where((d["% acum."] <= 80) | (np.arange(len(d)) == 0), "A",
                          np.where(d["% acum."] <= 95, "B", "C"))
    st.subheader("Clasificación ABC (A hasta 80 %, B hasta 95 %, C resto)")
    st.dataframe(d[["nombre", "V", "% acum.", "Clase"]].round(1), use_container_width=True, hide_index=True)
    d["Q*"] = np.sqrt(2 * d.demanda * d.pedido / d.mantenimiento)
    d["Pedidos/año"] = d.demanda / d["Q*"]
    d["Días entre pedidos"] = d["Q*"] / d.demanda * dias
    d["Costo pedido"] = d["Pedidos/año"] * d.pedido
    d["Costo mantenimiento"] = d["Q*"] / 2 * d.mantenimiento
    d["CT relevante"] = d["Costo pedido"] + d["Costo mantenimiento"]
    d["Stock seguridad"] = z * d.desv_diaria.fillna(0) * np.sqrt(d.plazo)
    d["ROP"] = d.demanda / dias * d.plazo + d["Stock seguridad"]
    d["Estado"] = np.where(d.stock.fillna(0) <= d.ROP, "REPONER", "OK")
    st.subheader("EOQ, punto de pedido y costos")
    st.dataframe(d[["nombre", "Q*", "Pedidos/año", "Días entre pedidos", "Costo pedido", "Costo mantenimiento",
                    "CT relevante", "Stock seguridad", "ROP", "stock", "Estado"]].round(2), use_container_width=True, hide_index=True)
    for _, r in d[d.Estado == "REPONER"].iterrows():
        st.warning(f"{r.nombre}: stock ({r.stock:g}) ≤ punto de pedido ({r.ROP:.1f}). Riesgo de desabastecimiento; pedir {r['Q*']:.0f} unid.")
    st.bar_chart(d.set_index("nombre")[["Costo pedido", "Costo mantenimiento"]])

# ---------------------------------------------------------------- TEORÍA DE DECISIONES
def tab_dec():
    casos = read("SELECT * FROM decisiones")
    c1, c2 = st.columns([3, 2])
    nombre = c1.selectbox("Caso de decisión", casos.nombre)
    nuevo = c2.text_input("Nuevo caso", placeholder="Nombre y presione Enter")
    if nuevo:
        try:
            run("INSERT INTO decisiones(nombre,tipo,alpha,estados,matriz,probs) VALUES(?,?,?,?,?,?)",
                (nuevo, "Costos", 0.5, "Demanda baja,Demanda media,Demanda alta",
                 json.dumps({"Proveedor A": [0, 0, 0]}), json.dumps([0.3, 0.4, 0.3]))); st.rerun()
        except sqlite3.IntegrityError: c2.warning("Ya existe ese caso.")
    r = casos[casos.nombre == nombre].iloc[0]
    tipo = st.radio("Tipo de matriz", ["Costos", "Beneficios"], index=["Costos", "Beneficios"].index(r.tipo), horizontal=True)
    alpha = st.slider("α de Hurwicz (optimismo)", 0.0, 1.0, float(r.alpha))
    est = [e.strip() for e in st.text_input("Escenarios (separados por coma)", r.estados).split(",") if e.strip()]
    mat = json.loads(r.matriz)
    dfm = pd.DataFrame([[a] + (v + [0] * len(est))[:len(est)] for a, v in mat.items()], columns=["Alternativa"] + est)
    st.caption("Los valores iniciales son datos simulados de ejemplo; reemplácelos con las cotizaciones del caso.")
    ed = st.data_editor(dfm, num_rows="dynamic", use_container_width=True, key=f"m{r.id}{len(est)}")
    pr = (json.loads(r.probs) + [0] * len(est))[:len(est)]
    pe = st.data_editor(pd.DataFrame([pr], columns=est), hide_index=True, use_container_width=True, key=f"p{r.id}{len(est)}")
    if st.button("💾 Guardar caso"):
        run("UPDATE decisiones SET tipo=?,alpha=?,estados=?,matriz=?,probs=? WHERE id=?",
            (tipo, alpha, ",".join(est), json.dumps({str(a): [float(x) for x in v] for a, v in zip(ed.Alternativa, ed[est].values.tolist())}),
             json.dumps([float(x) for x in pe.iloc[0]]), int(r.id)))
        st.success("Guardado en SQLite.")
    ed = ed.dropna(subset=["Alternativa"])
    if ed.empty or not est: return
    M, alts, p = ed[est].astype(float).values, list(ed.Alternativa), pe.iloc[0].astype(float).values
    cost = tipo == "Costos"
    best, worst = (np.min, np.max) if cost else (np.max, np.min)
    pick = lambda v, f=best: [alts[i] for i in np.flatnonzero(np.isclose(v, f(v)))]
    reg = np.abs(best(M, axis=0) - M)
    crit = {("Optimista (mín. de mínimos)" if cost else "Maximax"): best(M, axis=1),
            ("Pesimista - Wald" if cost else "Maximin"): worst(M, axis=1),
            "Laplace": M.mean(axis=1), f"Hurwicz (α={alpha:g})": alpha * best(M, axis=1) + (1 - alpha) * worst(M, axis=1)}
    st.subheader("Criterios bajo incertidumbre")
    filas = [{"Criterio": k, **dict(zip(alts, np.round(v, 2))), "Recomendada": ", ".join(pick(v, np.min if cost else np.max))} for k, v in crit.items()]
    sv = reg.max(axis=1)
    filas.append({"Criterio": "Savage (mín. arrepentimiento máx.)", **dict(zip(alts, np.round(sv, 2))), "Recomendada": ", ".join(pick(sv, np.min))})
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
    with st.expander("Matriz de arrepentimiento"):
        st.dataframe(pd.DataFrame(reg, index=alts, columns=est))
    st.subheader("Valor esperado")
    if not math.isclose(p.sum(), 1, abs_tol=1e-6):
        return st.error(f"Las probabilidades suman {p.sum():.3f}; deben sumar 1.")
    ev = M @ p
    ganador = pick(ev, np.min if cost else np.max)
    evpi = (ev.min() - (best(M, axis=0) @ p)) if cost else ((best(M, axis=0) @ p) - ev.max())
    st.dataframe(pd.DataFrame({"Alternativa": alts, "Costo esperado" if cost else "VME": ev.round(2)}), hide_index=True)
    st.success(f"Alternativa recomendada: {', '.join(ganador)}   |   VEIP = {evpi:.2f}")
    st.bar_chart(pd.Series(ev, index=alts))
    st.subheader("Árbol de decisión (evaluado de derecha a izquierda)")
    dot = f'digraph{{rankdir=LR;D[shape=box,label="Decisión\\n{"mín" if cost else "máx"} = {ev.min() if cost else ev.max():.2f}"];'
    for i, a in enumerate(alts):
        dot += f'D->N{i}[label="{a}"];N{i}[shape=circle,label="{ev[i]:.1f}"];'
        for j, e in enumerate(est): dot += f'N{i}->R{i}_{j}[label="p={p[j]:g}"];R{i}_{j}[shape=plaintext,label="{M[i, j]:g}"];'
    st.graphviz_chart(dot + "}")

# ---------------------------------------------------------------- MAIN
init_db()
st.title("Sistema de apoyo a la toma de decisiones - Boulevard Import S.A.C.")
st.caption("Investigación Operativa II · Caso simulado con fines académicos · Base de datos: SQLite (boulevard.db)")
t1, t2, t3 = st.tabs(["PERT/CPM", "Inventarios", "Teoría de decisiones"])
with t1: tab_pert()
with t2: tab_inv()
with t3: tab_dec()
