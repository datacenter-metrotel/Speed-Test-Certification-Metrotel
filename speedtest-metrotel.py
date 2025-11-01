import sys
import subprocess
import importlib.util
import os
import platform
import threading
import queue
import json

# --- Dependencias (deben instalarse manualmente o por el lanzador) ---
import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import webbrowser
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class NetTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Red (Speedtest & iPerf3)")
        self.root.geometry("850x830") 
        self.root.resizable(True, True) 

        self.queue = queue.Queue()
        self.process = None
        self.current_test_type = "ping_check" 
        self.connectivity_ok = False 
        self.speedtest_max_speed = 10000 

        # 1. Medidores de Velocidad (Arriba)
        meter_frame = ttk.Labelframe(root, text="Velocidad Actual (Mbps)", padding=10)
        meter_frame.pack(side=TOP, fill=X, padx=10, pady=5)

        center_meter_frame = ttk.Frame(meter_frame)
        center_meter_frame.pack()

        dl_frame = ttk.Frame(center_meter_frame)
        ttk.Label(dl_frame, text="Download Media").pack(pady=(0,5))
        self.dl_meter = ttk.Meter(
            dl_frame, metersize=160, padding=5, amountused=0,
            metertype="semi", subtext="Mbps", interactive=False,
            bootstyle="success", textfont="-size 18", subtextfont="-size 9"
        )
        self.dl_meter.pack(pady=5, padx=10)
        dl_frame.pack(side=LEFT, padx=10)

        ul_frame = ttk.Frame(center_meter_frame)
        ttk.Label(ul_frame, text="Upload Media").pack(pady=(0,5))
        self.ul_meter = ttk.Meter(
            ul_frame, metersize=160, padding=5, amountused=0,
            metertype="semi", subtext="Mbps", interactive=False,
            bootstyle="info", textfont="-size 18", subtextfont="-size 9"
        )
        self.ul_meter.pack(pady=5, padx=10)
        ul_frame.pack(side=LEFT, padx=10)

        jitter_frame = ttk.Frame(center_meter_frame)
        ttk.Label(jitter_frame, text="Jitter").pack(pady=(0,5))
        self.jitter_meter = ttk.Meter(
            jitter_frame, metersize=160, padding=5, amountused=0,
            metertype="semi", subtext="ms", interactive=False,
            bootstyle="warning", textfont="-size 18", subtextfont="-size 9"
        )
        self.jitter_meter.pack(pady=5, padx=10)
        jitter_frame.pack(side=LEFT, padx=10)

        # 2. Sección de Resultados Finales
        result_frame = ttk.Labelframe(root, text="Resultados Finales (Seleccionable)", padding=10)
        result_frame.pack(side=TOP, fill=BOTH, expand=True, padx=10, pady=5)
        
        self.result_text = tk.Text( 
            result_frame, 
            height=6, 
            font=("Arial", 10, "bold"), 
            wrap=WORD, 
            borderwidth=0,
            background=root.cget("background") 
        )
        self.result_text.pack(fill=BOTH, expand=True, padx=5, pady=5)
        self.result_text.insert(tk.END, "N/A")
        self.result_text.config(state=DISABLED)

        # 3. Sección de Estado en Tiempo Real
        status_frame = ttk.Labelframe(root, text="Estado en Tiempo Real", padding=10)
        status_frame.pack(side=TOP, fill=X, padx=10, pady=5)

        status_frame.columnconfigure(0, weight=1) 

        self.status_label = ttk.Label(status_frame, text="Verificando conectividad con servidor de test...", font=("Arial", 12), foreground="orange")
        self.status_label.grid(row=0, column=0, sticky="w", padx=5)

        self.recheck_button = ttk.Button(status_frame, text="Re-chequear", command=self.start_connectivity_check, bootstyle=INFO)
        self.recheck_button.grid(row=0, column=1, sticky="e", padx=5)

        # 4. Botón de Parar
        self.stop_button = ttk.Button(root, text="Parar Test Actual", command=self.stop_test, state=DISABLED, bootstyle=DANGER)
        self.stop_button.pack(side=TOP, pady=5)

        # 5. Parámetros (Abajo)
        parameters_frame = ttk.Frame(root)
        parameters_frame.pack(side=TOP, fill=X, padx=5, pady=5)

        # --- Configuración de iPerf3 ---
        iperf_frame = ttk.Labelframe(parameters_frame, text="iPerf3", padding=10)
        iperf_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 5), pady=5)

        iperf_settings_frame = ttk.Frame(iperf_frame)
        iperf_settings_frame.pack(fill=X, expand=True, padx=5)

        ttk.Label(iperf_settings_frame, text="Host:").grid(row=0, column=0, sticky="w", pady=2)
        self.iperf_host_entry = ttk.Entry(iperf_settings_frame, width=30)
        self.iperf_host_entry.insert(0, "velocidad.metrotel.com.ar")
        self.iperf_host_entry.grid(row=0, column=1, columnspan=2, sticky="w", padx=5, pady=2)

        ttk.Label(iperf_settings_frame, text="Velocidad (Mbps):").grid(row=1, column=0, sticky="w", pady=2)
        self.iperf_speed_entry = ttk.Entry(iperf_settings_frame, width=10)
        self.iperf_speed_entry.insert(0, "10000") 
        self.iperf_speed_entry.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=2)

        ttk.Label(iperf_settings_frame, text="Parallel Streams (-P):").grid(row=2, column=0, sticky="w", pady=2)
        self.iperf_parallel_entry = ttk.Entry(iperf_settings_frame, width=10)
        self.iperf_parallel_entry.insert(0, "1") 
        self.iperf_parallel_entry.grid(row=2, column=1, columnspan=2, sticky="w", padx=5, pady=2)

        # --- ¡CAMBIO AQUÍ! (wraplength eliminado) ---
        ttk.Label(iperf_settings_frame, text="Test:").grid(row=3, column=0, sticky="w", pady=5)
        
        self.iperf_direction = tk.StringVar(value="upload") 
        
        ttk.Radiobutton(
            iperf_settings_frame, 
            text="Modo Estandar: Origen el Cliente", 
            variable=self.iperf_direction, 
            value="upload"
        ).grid(row=3, column=1, sticky="w", pady=2) 
        
        ttk.Radiobutton(
            iperf_settings_frame, 
            text='Modo Reverso: Origen Metrotel "-R"', 
            variable=self.iperf_direction, 
            value="download"
        ).grid(row=4, column=1, sticky="w", pady=2) 

        ttk.Radiobutton(
            iperf_settings_frame, 
            text='Modo Dual: Origen Simultaneo Ambos "--bidir"', 
            variable=self.iperf_direction, 
            value="bidir"
        ).grid(row=5, column=1, sticky="w", pady=2) 
        # -------------------------------------------------

        iperf_settings_frame.columnconfigure(1, weight=1)
        
        iperf_button_frame = ttk.Frame(iperf_frame)
        iperf_button_frame.pack(fill=X, pady=5, padx=5)
        
        self.iperf_debug_button = ttk.Button(iperf_button_frame, text="Depuración en Vivo", command=self.start_iperf_debug, state=DISABLED, bootstyle=(OUTLINE, INFO))
        self.iperf_debug_button.pack(side=LEFT, anchor=W)

        self.iperf_button = ttk.Button(iperf_button_frame, text="Certificar Test iPerf3", command=self.start_iperf_test, state=DISABLED, bootstyle=PRIMARY)
        self.iperf_button.pack(side=RIGHT, anchor=E)

        # --- Configuración de Speedtest ---
        speedtest_frame = ttk.Labelframe(parameters_frame, text="Speedtest (Ookla)", padding=10)
        speedtest_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 5), pady=5)

        settings_frame = ttk.Frame(speedtest_frame)
        settings_frame.pack(fill=X, expand=True, padx=5)

        self.server_map = {
            "Metrotel (72225)": "72225",
            "Telecom Personal (54503)": "54503",
            "Telecentro (900)": "900",
            "Claro Argentina (5181)": "5181",
            "Cabase (4336)": "4336",
            "Iplan (13964)": "13964"
        }
        
        ttk.Label(settings_frame, text="Servidor:").grid(row=0, column=0, sticky="w", pady=5)
        self.speedtest_server_combo = ttk.Combobox(
            settings_frame,
            width=28, 
            state="readonly",
            values=list(self.server_map.keys())
        )
        self.speedtest_server_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.speedtest_server_combo.current(0) 
        
        settings_frame.columnconfigure(1, weight=1)

        speedtest_button_frame = ttk.Frame(speedtest_frame)
        speedtest_button_frame.pack(fill=X, pady=5, padx=5, side=BOTTOM)

        self.speedtest_debug_button = ttk.Button(speedtest_button_frame, text="Depuración en Vivo", command=self.start_speedtest_debug, state=DISABLED, bootstyle=(OUTLINE, INFO))
        self.speedtest_debug_button.pack(side=LEFT, anchor=W)

        self.speedtest_button = ttk.Button(speedtest_button_frame, text="Certificar Test Ookla", command=self.start_speedtest, state=DISABLED, bootstyle=PRIMARY)
        self.speedtest_button.pack(side=RIGHT, anchor=E)
        
        # --- Fin del Layout ---

        self.start_connectivity_check()
        self.root.after(100, self.process_queue) 

    def start_connectivity_check(self):
        """Inicia el chequeo de ping y puerto en un hilo separado."""
        self.status_label.config(text="Verificando conectividad con servidor de test...", font=("Arial", 12), foreground="orange")
        self.current_test_type = "ping_check" 
        self.connectivity_ok = False 
        
        self.iperf_button.config(state=DISABLED)
        self.speedtest_button.config(state=DISABLED)
        self.iperf_debug_button.config(state=DISABLED)
        self.speedtest_debug_button.config(state=DISABLED)
        self.stop_button.config(state=DISABLED)
        
        if hasattr(self, 'recheck_button'): 
            self.recheck_button.config(state=DISABLED)
        
        self.dl_meter.configure(amountused=0, amounttotal=100)
        self.ul_meter.configure(amountused=0, amounttotal=100)
        self.jitter_meter.configure(amountused=0, amounttotal=20) 

        threading.Thread(target=self.execute_pre_checks, args=(self.queue,), daemon=True).start()

    def execute_pre_checks(self, q):
        """Chequea Ping Y Puerto 5201. Se ejecuta en un HILO SECUNDARIO."""
        target_host = "velocidad.metrotel.com.ar"
        target_port = 5201 
        
        try:
            if platform.system() == "Windows":
                cmd = ['ping', '-n', '2', target_host] 
                popen_flags = 0x08000000 
            else:
                cmd = ['ping', '-c', '2', target_host] 
                popen_flags = 0

            result = subprocess.run(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                creationflags=popen_flags
            )
            
            if result.returncode != 0:
                q.put("CHECK_FAIL_PING")
                return 

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(3) 
                    s.connect((target_host, target_port))
                q.put("CHECK_SUCCESS")
            except (socket.timeout, ConnectionRefusedError):
                q.put("CHECK_FAIL_PORT")
            
        except Exception:
            q.put("CHECK_FAIL_GENERIC")

    def set_ui_state(self, testing):
        """Activa o desactiva los botones según el estado del test."""
        ping_success = self.connectivity_ok 
        start_state = NORMAL if (not testing and ping_success) else DISABLED
        
        self.iperf_button.config(state=start_state)
        self.speedtest_button.config(state=start_state)
        self.iperf_debug_button.config(state=start_state)
        self.speedtest_debug_button.config(state=start_state)
        
        self.stop_button.config(state=NORMAL if testing else DISABLED)

        if hasattr(self, 'recheck_button'):
            self.recheck_button.config(state=NORMAL if not testing else DISABLED)

    def set_result_text(self, text):
        """Helper para actualizar el widget de Texto de resultados."""
        self.result_text.config(state=NORMAL)
        self.result_text.delete(1.0, END)
        self.result_text.insert(END, text)
        self.result_text.see(END) # Auto-scroll
        self.result_text.config(state=DISABLED)

    # --- Lógica de "Certificar" (JSON) ---

    def start_iperf_test(self):
        host = self.iperf_host_entry.get().strip()
        speed = self.iperf_speed_entry.get().strip()
        direction = self.iperf_direction.get()
        parallel = self.iperf_parallel_entry.get().strip()
        
        if not host:
            messagebox.showerror("Error", "El host de iPerf3 no puede estar vacío.")
            return
        if not speed.isdigit() or int(speed) <= 0:
            messagebox.showerror("Error", "La Velocidad (Mbps) de iPerf3 debe ser un número positivo.")
            return
        if not parallel.isdigit() or int(parallel) <= 0:
            messagebox.showerror("Error", "Parallel Streams (-P) debe ser un número positivo.")
            return
        
        max_speed = int(speed) * 1.5 
        
        if direction == "download":
            self.dl_meter.configure(amounttotal=max_speed, amountused=0)
        elif direction == "upload":
            self.ul_meter.configure(amounttotal=max_speed, amountused=0)
        else: # bidir
            self.dl_meter.configure(amounttotal=max_speed, amountused=0)
            self.ul_meter.configure(amounttotal=max_speed, amountused=0)
        
        self.jitter_meter.configure(amountused=0, amounttotal=20, subtext="ms (iPerf3)")

        cmd = ['iperf3', '-c', host, '-J', '-i', '1']
        cmd.extend(['-b', f"{speed}M"])
        cmd.extend(['-P', parallel])
        
        if direction == "download":
            cmd.append('-R') 
        elif direction == "bidir":
            cmd.append('--bidir')
            
        self.run_test_thread(cmd, "iperf3")

    def start_speedtest(self):
        selected_name = self.speedtest_server_combo.get()
        if not selected_name:
            messagebox.showerror("Error", "Por favor, selecciona un servidor de Speedtest.")
            return
        server_id = self.server_map.get(selected_name)
        
        self.speedtest_max_speed = 10000 
        
        self.dl_meter.configure(amounttotal=self.speedtest_max_speed, amountused=0)
        self.ul_meter.configure(amounttotal=self.speedtest_max_speed, amountused=0)
        self.jitter_meter.configure(amounttotal=20, amountused=0, subtext="ms (Speedtest)")

        cmd = ['speedtest', '-s', server_id, '-f', 'json', '--accept-license']
        self.run_test_thread(cmd, "speedtest")

    def run_test_thread(self, cmd, test_type):
        """Inicia el test JSON en un hilo separado."""
        self.current_test_type = test_type 
        self.set_ui_state(testing=True)
        self.status_label.config(text=f"Iniciando {test_type}...")
        self.set_result_text("N/A")

        threading.Thread(target=self.execute_command_json, args=(cmd, self.queue, test_type), daemon=True).start()
        
    def execute_command_json(self, cmd, q, test_type):
        """Ejecuta el comando para JSON (Speedtest en vivo, iPerf3 al final)."""
        popen_flags = 0
        if platform.system() == "Windows":
            popen_flags = 0x08000000
            
        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', bufsize=1, creationflags=popen_flags
            )
            
            if test_type == "speedtest":
                if self.process.stdout:
                    for line in iter(self.process.stdout.readline, ''):
                        if line: q.put(line)
                        else: break
            
            elif test_type == "iperf3":
                output_accumulator = []
                if self.process.stdout:
                    for line in iter(self.process.stdout.readline, ''):
                        if line: output_accumulator.append(line)
                        else: break
                q.put("".join(output_accumulator)) 

            self.process.wait()

        except FileNotFoundError:
            q.put(f"ERROR: Comando '{cmd[0]}' no encontrado.\n")
        except Exception as e:
            q.put(f"ERROR: {str(e)}\n")
        finally:
            q.put(None) 
            self.process = None

    # --- Lógica de "Depuración" (Modo Humano) ---

    def start_iperf_debug(self):
        host = self.iperf_host_entry.get().strip()
        speed = self.iperf_speed_entry.get().strip()
        direction = self.iperf_direction.get()
        parallel = self.iperf_parallel_entry.get().strip()
        
        if not host:
            messagebox.showerror("Error", "El host de iPerf3 no puede estar vacío.")
            return
        if not speed.isdigit() or int(speed) <= 0:
            messagebox.showerror("Error", "La Velocidad (Mbps) de iPerf3 debe ser un número positivo.")
            return
        if not parallel.isdigit() or int(parallel) <= 0:
            messagebox.showerror("Error", "Parallel Streams (-P) debe ser un número positivo.")
            return

        # Comando SIN JSON
        cmd = ['iperf3', '-c', host, '-i', '1'] 
        cmd.extend(['-b', f"{speed}M"])
        cmd.extend(['-P', parallel])
        
        if direction == "download":
            cmd.append('-R') 
        elif direction == "bidir":
            cmd.append('--bidir')
            
        self.run_test_thread_debug(cmd)

    def start_speedtest_debug(self):
        selected_name = self.speedtest_server_combo.get()
        if not selected_name:
            messagebox.showerror("Error", "Por favor, selecciona un servidor de Speedtest.")
            return
        server_id = self.server_map.get(selected_name)
        
        # Comando SIN JSON
        cmd = ['speedtest', '-s', server_id, '--accept-license'] 
        self.run_test_thread_debug(cmd)

    def run_test_thread_debug(self, cmd):
        """Inicia el test de depuración (modo humano) en un hilo."""
        self.current_test_type = "debug" 
        self.set_ui_state(testing=True)
        self.status_label.config(text=f"Iniciando depuración en vivo...")
        
        self.result_text.config(state=NORMAL)
        self.result_text.delete(1.0, END)
        self.result_text.config(state=DISABLED)
        
        self.dl_meter.configure(amountused=0)
        self.ul_meter.configure(amountused=0)
        self.jitter_meter.configure(amountused=0)

        threading.Thread(target=self.execute_command_debug, args=(cmd, self.queue), daemon=True).start()

    def execute_command_debug(self, cmd, q):
        """Ejecuta el comando y pone CADA LÍNEA (humana) en la cola."""
        popen_flags = 0
        if platform.system() == "Windows":
            popen_flags = 0x08000000
            
        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', bufsize=1, creationflags=popen_flags
            )
            
            if self.process.stdout:
                for line in iter(self.process.stdout.readline, ''):
                    if line: 
                        q.put(f"DEBUG_LINE: {line}") # Prefijo para distinguirlo
                    else: 
                        break
            self.process.wait()

        except FileNotFoundError:
            q.put(f"ERROR: Comando '{cmd[0]}' no encontrado.\n")
        except Exception as e:
            q.put(f"ERROR: {str(e)}\n")
        finally:
            q.put(None) 
            self.process = None

    # --- Lógica de la Cola (Maneja ambos tipos de test) ---

    def process_queue(self):
        """Procesa mensajes de la cola en el HILO PRINCIPAL (Loop perpetuo)."""
        test_type = self.current_test_type
        
        try:
            line = self.queue.get_nowait()

            if line == "CHECK_SUCCESS":
                self.status_label.config(text="Conectado. Listo para probar.", foreground="green")
                self.connectivity_ok = True 
                self.set_ui_state(testing=False) 
                self.current_test_type = "idle" 
            
            elif line in ["CHECK_FAIL_PING", "CHECK_FAIL_PORT", "CHECK_FAIL_GENERIC"]:
                if line == "CHECK_FAIL_PING":
                    self.status_label.config(text="Error: No se pudo encontrar el host del servidor.", foreground="red")
                elif line == "CHECK_FAIL_PORT":
                    self.status_label.config(text="Error: El servidor iPerf3 está offline (puerto 5201).", foreground="red")
                else: 
                    self.status_label.config(text="Error: Falló el chequeo de conectividad.", foreground="red")
                
                self.connectivity_ok = False 
                self.set_ui_state(testing=False) 
                self.current_test_type = "idle"

            elif line is None: 
                self.set_ui_state(testing=False)
                if "ERROR" not in self.status_label.cget("text"):
                        self.status_label.config(text="Test completado.")
                self.current_test_type = "idle"

            elif line.startswith("ERROR:"):
                self.set_result_text(line)
                self.status_label.config(text="Error.", foreground="red")
                self.dl_meter.configure(amountused=0)
                self.ul_meter.configure(amountused=0)
                self.jitter_meter.configure(amountused=0)

            elif line.startswith("DEBUG_LINE: "):
                debug_output = line.replace("DEBUG_LINE: ", "")
                self.result_text.config(state=NORMAL)
                self.result_text.insert(END, debug_output)
                self.result_text.see(END)
                self.result_text.config(state=DISABLED)

            elif test_type not in ["ping_check", "idle", "debug"]:
                self.parse_json_update(line, test_type)

        except queue.Empty:
            pass 
        except Exception as e:
            self.status_label.config(text=f"Error de UI: {e}", fg="red")

        self.root.after(100, self.process_queue)

    def parse_json_update(self, line, test_type):
        """Intenta decodificar el JSON y actualizar el estado."""
        data = None
        try:
            if test_type == "speedtest":
                data = json.loads(line) 
            
            elif test_type == "iperf3":
                json_start_index = line.find('{')
                if json_start_index != -1:
                    json_str = line[json_start_index:]
                    data = json.loads(json_str)
                else:
                    self.set_result_text(f"Error de iPerf3:\n{line}")
                    return
                    
        except json.JSONDecodeError:
            if test_type == "speedtest":
                pass 
            else:
                self.set_result_text(f"Error de iPerf3:\n{line}")
            return 

        if data is None:
            return 

        if test_type == "speedtest":
            test_name = data.get("type", "")
            if test_name in ["download", "upload"]:
                speed_mbps = data[test_name].get("bandwidth", 0) * 8 / 1_000_000
                progress = data[test_name].get("progress", 0) * 100
                self.status_label.config(text=f"Probando {test_name.capitalize()}: {speed_mbps:.2f} Mbps ({progress:.0f}%)", foreground="blue")
                
                if test_name == "download":
                    self.dl_meter.configure(amounttotal=self.speedtest_max_speed, amountused=int(speed_mbps))
                elif test_name == "upload":
                    self.ul_meter.configure(amounttotal=self.speedtest_max_speed, amountused=int(speed_mbps))
            
            elif test_name == "result":
                dl = data.get("download", {}).get("bandwidth", 0) * 8 / 1_000_000
                ul = data.get("upload", {}).get("bandwidth", 0) * 8 / 1_000_000
                ping = data.get("ping", {}).get("latency", 0)
                jitter = data.get("ping", {}).get("jitter", 0)
                
                url = data.get('result', {}).get('url', 'N/A')
                
                result_str = (
                    f"Descarga: {dl:.2f} Mbps\n"
                    f"Subida: {ul:.2f} Mbps\n"
                    f"Ping: {ping:.2f} ms (Jitter: {jitter:.2f} ms)\n"
                    f"ISP: {data.get('isp', 'N/A')}\n"
                    f"IP Externa: {data.get('interface', {}).get('externalIp', 'N/A')}\n"
                    f"URL: {url}"
                )
                self.set_result_text(result_str)
                
                self.dl_meter.configure(amountused=int(dl))
                self.ul_meter.configure(amountused=int(ul))
                self.jitter_meter.configure(amountused=round(jitter, 2)) 

                if url != 'N/A' and url.startswith('http'):
                    try:
                        webbrowser.open(url)
                    except Exception as e:
                        print(f"No se pudo abrir el navegador: {e}")

        elif test_type == "iperf3":
            if data.get("error"):
                self.set_result_text(f"Error de iPerf3: {data.get('error')}")
                self.status_label.config(text="Error de iPerf3.", foreground="red")
                return 

            # iPerf3 no actualiza en vivo (solo al final)
            
            if "end" in data: 
                try:
                    target_speed = self.iperf_speed_entry.get()
                    direction = self.iperf_direction.get()
                    result_str = ""
                    
                    if direction == "bidir":
                        upload_speed = data["end"]["sum_sent"]["bits_per_second"] / 1_000_000
                        download_speed = data["end"]["sum_received"]["bits_per_second"] / 1_000_000
                        upload_jitter = data["end"]["sum_sent"].get("jitter_ms", 0)
                        download_jitter = data["end"]["sum_received"].get("jitter_ms", 0)
                        
                        result_str = (
                            f"Resultado Bi-direccional:\n"
                            f"Upload Media: {upload_speed:.2f} Mbps (Jitter: {upload_jitter:.2f} ms)\n"
                            f"Download Media: {download_speed:.2f} Mbps (Jitter: {download_jitter:.2f} ms)\n"
                            f"Velocidad Objetivo: {target_speed} Mbps"
                        )
                        self.ul_meter.configure(amountused=int(upload_speed))
                        self.dl_meter.configure(amountused=int(download_speed))
                        self.jitter_meter.configure(amountused=round(download_jitter, 2)) 
                    
                    elif direction == "upload":
                        summary = data["end"]["sum_sent"] 
                        speed_mbps = summary["bits_per_second"] / 1_000_000
                        jitter_ms = summary.get("jitter_ms", 0)
                        result_str = (
                            f"Resultado Upload (Estándar):\n"
                            f"Velocidad Media: {speed_mbps:.2f} Mbps (Jitter: {jitter_ms:.2f} ms)\n"
                            f"Velocidad Objetivo: {target_speed} Mbps"
                        )
                        self.ul_meter.configure(amountused=int(speed_mbps))
                        self.jitter_meter.configure(amountused=round(jitter_ms, 2))

                    elif direction == "download":
                        summary = data["end"]["sum_received"]
                        speed_mbps = summary["bits_per_second"] / 1_000_000
                        jitter_ms = summary.get("jitter_ms", 0)
                        result_str = (
                            f"Resultado Download (-R):\n"
                            f"Velocidad Media: {speed_mbps:.2f} Mbps (Jitter: {jitter_ms:.2f} ms)\n"
                            f"Velocidad Objetivo: {target_speed} Mbps"
                        )
                        self.dl_meter.configure(amountused=int(speed_mbps))
                        self.jitter_meter.configure(amountused=round(jitter_ms, 2))
                    
                    self.set_result_text(result_str)
                
                except KeyError as e:
                    err_msg = f"Error iPerf3: No se encontró la llave '{e}' en el JSON final.\nEl test pudo haber fallado."
                    self.set_result_text(err_msg)
                except Exception as e:
                    err_msg = f"Error iPerf3 inesperado: {str(e)}"
                    self.set_result_text(err_msg)

    def stop_test(self):
        """Intenta terminar el subproceso actual."""
        if self.process:
            try:
                self.process.terminate()
                self.status_label.config(text="Test detenido por el usuario.", foreground="orange")
                self.set_ui_state(testing=False)
                self.current_test_type = "idle"
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo detener el proceso: {e}")

if __name__ == "__main__":
    main_root = ttk.Window(themename="superhero") 
    app = NetTestApp(main_root)
    main_root.mainloop()
