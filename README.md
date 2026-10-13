# Sistema IO2

Sistema de apoyo a la toma de decisiones para **Boulevard Import S.A.C.** (caso simulado con fines académicos), desarrollado para el curso de Investigación Operativa II con Python, Streamlit y SQLite.

El sistema tiene tres módulos:

- **PERT/CPM:** planificación de proyectos, ruta crítica, diagrama de red, cronograma Gantt y seguimiento.
- **Inventarios:** clasificación ABC, lote económico (EOQ), stock de seguridad y punto de pedido.
- **Teoría de decisiones:** criterios bajo incertidumbre, valor esperado, VEIP y árbol de decisión.

## Requisitos previos

- Python instalado en Windows.
- La carpeta completa del proyecto (todas las carpetas y archivos que se muestran abajo).
- Conexión a Internet para instalar las dependencias.

## Estructura del proyecto

```text
sistema_io2/
├── app.py                     ← Punto de entrada del sistema
├── requirements.txt           ← Bibliotecas necesarias
├── boulevard.db               ← Base de datos SQLite
├── README.md
├── base_datos/                ← Conexión y creación de tablas
├── utilidades/                ← Funciones auxiliares
└── modulos/
    ├── pert_cpm/              ← Módulo PERT/CPM
    ├── inventarios/           ← Módulo de Inventarios
    └── teoria_decisiones/     ← Módulo de Teoría de decisiones
```

Cada módulo contiene `calculos.py` (fórmulas) e `interfaz.py` (pantalla en Streamlit).

## Instalación y ejecución

### 1. Instalar Python

Si todavía no tienes Python instalado, descárgalo desde la página oficial:

https://www.python.org/downloads/

Durante la instalación en Windows, marca la casilla **Add Python to PATH**.

Para comprobar que está instalado correctamente, abre una terminal y ejecuta:

```bash
python --version
```

### 2. Preparar la carpeta del proyecto

Copia la carpeta completa del proyecto, por ejemplo en el Escritorio con el nombre `sistema_io2`. No copies solo `app.py`: el sistema también necesita las carpetas `base_datos`, `utilidades` y `modulos`.

Si no existe el archivo `boulevard.db`, el sistema lo crea automáticamente con datos de ejemplo la primera vez que se ejecuta.

### 3. Abrir una terminal en la carpeta

En Windows, sigue estos pasos:

1. Abre la carpeta `sistema_io2`.
2. Haz clic en la barra de direcciones del Explorador de archivos.
3. Escribe `cmd` y presiona Enter.

También puedes abrir PowerShell y ejecutar:

```powershell
cd "$HOME\Desktop\sistema_io2"
```

### 4. Instalar las dependencias

Ejecuta el siguiente comando para instalar las bibliotecas necesarias:

```bash
python -m pip install -r requirements.txt
```

Este paso se realiza normalmente una sola vez, siempre que las dependencias no cambien.

### 5. Ejecutar el sistema

Inicia la aplicación con el siguiente comando:

```bash
python -m streamlit run app.py
```

Streamlit abrirá el sistema en tu navegador web. Si no se abre automáticamente, visita la dirección local que aparece en la terminal, normalmente:

http://localhost:8501
