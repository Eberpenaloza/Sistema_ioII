"""Creación de tablas y carga de datos de ejemplo (simulados)."""
import json

from .conexion import ejecutar, ejecutar_varios, consultar

TABLAS = [
    """CREATE TABLE IF NOT EXISTS proyectos(
           id INTEGER PRIMARY KEY, nombre TEXT UNIQUE,
           modo TEXT DEFAULT 'CPM', plazo REAL DEFAULT 10)""",
    """CREATE TABLE IF NOT EXISTS actividades(
           id INTEGER PRIMARY KEY, proyecto_id INTEGER,
           codigo TEXT, nombre TEXT, predecesoras TEXT,
           duracion REAL, a REAL, m REAL, b REAL, real REAL,
           FOREIGN KEY(proyecto_id) REFERENCES proyectos(id))""",
    """CREATE TABLE IF NOT EXISTS productos(
           id INTEGER PRIMARY KEY, nombre TEXT, demanda REAL, costo REAL, pedido REAL,
           mantenimiento REAL, plazo REAL, desv_diaria REAL, stock REAL)""",
    """CREATE TABLE IF NOT EXISTS config(
           clave TEXT PRIMARY KEY, valor REAL)""",
    """CREATE TABLE IF NOT EXISTS decisiones(
           id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, tipo TEXT,
           alpha REAL, estados TEXT, matriz TEXT, probs TEXT)""",
]

ACTIVIDADES_EJEMPLO = [
    ("A", "Diseñar la distribución", "", 3),
    ("B", "Despejar y preparar el área", "A", 2),
    ("C", "Adquirir estanterías y señalización", "A", 4),
    ("D", "Instalar estanterías", "B,C", 3),
    ("E", "Organizar y etiquetar productos", "D", 2),
    ("F", "Verificar seguridad y distribución", "E", 1),
]

PRODUCTOS_EJEMPLO = [
    ("Laptop de oficina", 600, 2200, 80, 220, 5, 2, 30),
    ("Impresora multifuncional", 480, 750, 60, 75, 4, 1.5, 25),
    ("Teclado y mouse", 1200, 85, 35, 8.5, 3, 4, 60),
]


def inicializar_base_datos():
    """Crea las tablas y, si la base está vacía, carga los datos de ejemplo."""
    for sql in TABLAS:
        ejecutar(sql)
    if consultar("SELECT COUNT(*) n FROM proyectos").n[0] == 0:
        _cargar_datos_ejemplo()


def _cargar_datos_ejemplo():
    pid = ejecutar("INSERT INTO proyectos(nombre,modo,plazo) VALUES('Reorganización del almacén','CPM',13)")
    ejecutar_varios(
        "INSERT INTO actividades(proyecto_id,codigo,nombre,predecesoras,duracion,a,m,b) VALUES(?,?,?,?,?,?,?,?)",
        [(pid, c, n, p, d, max(d - 1, 0), d, d + 1) for c, n, p, d in ACTIVIDADES_EJEMPLO])
    ejecutar_varios(
        "INSERT INTO productos(nombre,demanda,costo,pedido,mantenimiento,plazo,desv_diaria,stock) VALUES(?,?,?,?,?,?,?,?)",
        PRODUCTOS_EJEMPLO)
    ejecutar_varios("INSERT INTO config VALUES(?,?)", [("dias", 300), ("z", 1.65)])
    ejecutar(
        "INSERT INTO decisiones(nombre,tipo,alpha,estados,matriz,probs) VALUES(?,?,?,?,?,?)",
        ("Selección de proveedor (ejemplo simulado)", "Costos", 0.5,
         "Demanda baja,Demanda media,Demanda alta",
         json.dumps({"Proveedor A": [100, 120, 150], "Proveedor B": [110, 115, 130], "Proveedor C": [105, 125, 140]}),
         json.dumps([0.3, 0.5, 0.2])))
