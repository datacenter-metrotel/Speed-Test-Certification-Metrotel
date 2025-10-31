# Monitor de Red (iPerf3 & Speedtest GUI)

Esta es una utilidad de escritorio para Python que provee una interfaz gráfica (GUI) para las herramientas de línea de comandos `iperf3` y `speedtest` (Ookla).

La aplicación permite ejecutar pruebas de velocidad, parsea los resultados JSON en vivo, y los muestra en medidores visuales (velocímetros) y en un panel de resultados detallados.

<img width="1861" height="1072" alt="image" src="https://github.com/user-attachments/assets/6bdc1316-0eb6-46e7-8d04-cd17bed08c63" />


## 📋 Características Principales

* **Medidores Visuales:** Tres relojes (medidores) para Descarga, Subida y Jitter.
* **Soporte iPerf3:** Permite configurar host, velocidad objetivo y modo de test:
    * Upload (Estándar)
    * Download (`-R`)
    * Upload y Download (`--bidir`)
* **Soporte Speedtest (Ookla):** Permite configurar un ID de servidor específico.
* **Chequeo de Conectividad:** Antes de iniciar, verifica con Ping y un chequeo de puerto (`5201`) que el servidor de iPerf3 esté accesible.
* **Resultados Detallados:** Muestra un resumen de los tests en un formato legible y seleccionable (para copiar y pegar).
* **Integración Web:** Abre automáticamente la URL del resultado de Speedtest en tu navegador.
* **Interfaz Moderna:** Construida con `ttkbootstrap` para un look moderno.

## ⚙️ Prerrequisitos

Antes de ejecutar, asegúrate de tener instaladas las siguientes herramientas en tu sistema (probado en Linux/Ubuntu/Debian):

* **Python 3** (incluyendo el módulo `venv`):
    ```bash
    sudo apt install python3 python3-venv
    ```
* **iPerf3**:
    ```bash
    sudo apt install iperf3
    ```
* **Speedtest CLI (Ookla):**
    (Se recomienda seguir las [instrucciones oficiales de instalación](https://www.speedtest.net/es/apps/cli), ya que la versión de `apt` puede ser antigua).
    ```bash
    # Ejemplo de instalación (puede variar según tu SO)
    curl -s [https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh](https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh) | sudo bash
    sudo apt install speedtest
    ```

La dependencia de Python (`ttkbootstrap`) será instalada automáticamente por el script lanzador.

## 🚀 Cómo Ejecutar

Este proyecto utiliza un entorno virtual de Python (`venv`) para manejar sus dependencias de forma aislada, gracias al script `run.sh`.

1.  **Clona el repositorio (o descarga los archivos `speedtest.py` y `run.sh`):**
    ```bash
    git clone https://github.com/datacenter-metrotel/Speed-Test-Certification-Metrotel.git
    cd Speed-Test-Certification-Metrotel
    ```

2.  **Dale permisos de ejecución al lanzador:**
    (Solo necesitas hacer esto una vez)
    ```bash
    chmod +x run.sh
    ```

3.  **Ejecuta la aplicación:**
    ¡Usa siempre `run.sh` para iniciar la app!
    ```bash
    ./run.sh
    ```

La primera vez que lo ejecutes, el script `run.sh` creará un entorno virtual en la carpeta `.venv`, lo activará, e instalará `ttkbootstrap` automáticamente antes de lanzar la aplicación.

## 🔧 Configuración

La aplicación está pre-configurada para los servidores de Metrotel. Si deseas cambiarlos, puedes editar los valores directamente en la parte superior del script `p.py` y `run.sh`.

* **iPerf3 Host:** `velocidad.metrotel.com.ar`
* **iPerf3 Puerto (Chequeo):** `5201`
* **Speedtest Host (Info):** `certificaciones.metrotel.com.ar`
* **Speedtest ID:** `72225`
