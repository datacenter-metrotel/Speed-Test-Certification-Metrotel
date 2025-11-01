#!/bin/bash

# --- Este script automatiza la configuración del entorno virtual ---

# Encontrar el directorio donde reside este script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
VENV_DIR="$DIR/.venv"
# --- ¡CAMBIO AQUÍ! ---
PYTHON_SCRIPT="$DIR/speedtest-metrotel.py" # Nombre actualizado

# 1. Crear el entorno virtual si no existe
if [ ! -d "$VENV_DIR" ]; then
    echo "Creando entorno virtual en $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "Error: No se pudo crear el entorno virtual."
        exit 1
    fi
fi

# 2. Activar el entorno virtual
source "$VENV_DIR/bin/activate"

# 3. Instalar dependencias si no están
pip show ttkbootstrap &> /dev/null
if [ $? -ne 0 ]; then
    echo "Instalando ttkbootstrap en el entorno virtual..."
    pip install ttkbootstrap
    if [ $? -ne 0 ]; then
        echo "Error: No se pudo instalar ttkbootstrap."
        exit 1
    fi
fi

# 4. Ejecutar el script de Python
echo "Iniciando la aplicación..."
python3 "$PYTHON_SCRIPT"
