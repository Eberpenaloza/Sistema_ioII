# Sistema IO2

Aplicación desarrollada en Python utilizando Streamlit.

## Requisitos previos

- Python instalado en Windows.
- Los archivos `app.py` y `requirements.txt` del proyecto.
- Conexión a Internet para instalar las dependencias.

## Instalación y ejecución

### 1. Instalar Python

Si todavía no tienes Python instalado, descárgalo desde la página oficial:

https://www.python.org/downloads/

Durante la instalación en Windows, marca la casilla **Add Python to PATH**.

Para comprobar que está instalado correctamente, abre una terminal y ejecuta:

```bash
python --version
```

### 1. Abrir una terminal 

En Windows, sigue estos pasos:

1. Abre la carpeta `sistema_io2`.
2. Haz clic en la barra de direcciones del Explorador de archivos.
3. Escribe `cmd` y presiona Enter.

También puedes abrir una terminal y ejecutar:

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
