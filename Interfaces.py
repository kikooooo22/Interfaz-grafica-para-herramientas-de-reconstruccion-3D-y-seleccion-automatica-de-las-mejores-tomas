import os
import subprocess
import cv2
import time
import shutil
import threading
import tkinter as tk
from tkinter import ttk, Frame, Button, Label, Entry, BooleanVar, Checkbutton, filedialog, messagebox
from PIL import Image

from Evaluators import Evaluators
from ManagePreferences import Preferences

class MainApp:
    def __init__(self, root):
        self.root = root
        self.preferences = Preferences() 
        self.preferences.load()       
        self.ruta_imagenes = None
        self.root.title("Visualizador de Imágenes")
        self.root.geometry("1000x700")
        self.root.configure(bg="#1E1E1E")

        # Configurar estilos ttk
        self.setup_styles()
        
        # Variables de estado
        self.gs_visible = False
        self.animation_speed = 5
        self.panel_width = 1
        
        # Frame principal
        self.main_frame = tk.Frame(root, bg="#1E1E1E")
        self.main_frame.pack(fill="both", expand=True)
        
        # Frame COLMAP
        self.colmap_frame = tk.Frame(self.main_frame, bg="#1E1E1E")
        self.colmap_frame.pack(fill="both", expand=True)
        
        # Frame Gaussian Splatting (inicialmente oculto)
        self.gs_frame = tk.Frame(self.main_frame, bg="#1E1E1E")
        
        # Botón de alternancia derecho (para COLMAP)
        self.toggle_btn_right = tk.Button(self.main_frame, 
                                        text="Gaussian\nSplatting >", 
                                        font=("Arial", 10, "bold"), 
                                        fg="white", bg="#007ACC",
                                        relief="flat", 
                                        borderwidth=0,
                                        command=self.toggle_gs_panel)
        self.toggle_btn_right.place(relx=1, rely=0, anchor="ne", width=80, relheight=1)
        
        # Botón de alternancia izquierdo (para GS, inicialmente oculto)
        self.toggle_btn_left = tk.Button(self.gs_frame,
                                    text="< COLMAP\nTools",
                                    font=("Arial", 10, "bold"),
                                    fg="white", bg="#007ACC",
                                    relief="flat",
                                    borderwidth=0,
                                    command=self.toggle_gs_panel)
        
        # Configurar interfaces
        self.setup_colmap_interface()
        self.setup_gs_interface()
     
    def setup_ui(self):
        self.root.title("Visualizador de Imágenes")
        self.root.geometry("900x600")
        self.root.configure(bg="#1E1E1E")
        
        # Configuración de los frames principales
        self.main_frame = Frame(self.root, bg="#1E1E1E")
        self.main_frame.pack(fill="both", expand=True)
        
        # Frame COLMAP
        self.colmap_frame = Frame(self.main_frame, bg="#1E1E1E")
        self.colmap_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Frame Gaussian Splatting (inicialmente oculto)
        self.gs_frame = Frame(self.main_frame, bg="#1E1E1E")
        
        # Botón de alternancia
        self.toggle_btn = Button(self.main_frame, text="> Gaussian Splatting", 
                            font=("Arial", 10, "bold"), fg="white", bg="#007ACC",
                            relief="flat", command=self.toggle_gs_panel)
        self.toggle_btn.place(relx=0, rely=0.5, anchor="w", width=80, height=40)
        
        self.setup_colmap_interface()
        self.setup_gs_interface()

    def setup_styles(self):
        style = ttk.Style()
        
        # Configurar tema general
        style.theme_use('clam')
        
        # Colores base
        style.configure('.', background='#1E1E1E', foreground='white')
        style.configure('TFrame', background='#1E1E1E')
        style.configure('TLabel', background='#1E1E1E', foreground='white', font=('Arial', 16))
        style.configure('TButton', background='#3A3A3A', foreground='white', 
                       font=('Arial', 14, 'bold'), borderwidth=0, focusthickness=3, 
                       focuscolor='none', padding=5)
        style.map('TButton', 
                 background=[('active', '#505050'), ('disabled', '#2A2A2A')],
                 foreground=[('disabled', '#7A7A7A')])
        
        style.configure('Toggle.TButton', background='#007ACC', font=('Arial', 14, 'bold'))
        
        style.configure('Warning.TLabel', foreground='red')
        style.configure('Success.TLabel', foreground='green')
        style.configure('Title.TLabel', font=('Arial', 18, 'bold'))
        style.configure('Highlight.TButton', background='#007ACC', font=('Arial', 16, 'bold'))
        style.configure('Icon.TButton', font=('Arial', 20))
        
        # Entradas
        style.configure('TEntry', fieldbackground='#3A3A3A', foreground='white', 
                        insertcolor='white', bordercolor='#505050', lightcolor='#505050')
        
        # Barra de progreso
        style.configure('Horizontal.TProgressbar', background='#007ACC', troughcolor='#3A3A3A')
        
        # Checkbutton
        style.configure('TCheckbutton', background='#1E1E1E', foreground='white', 
                       font=('Arial', 16))
        style.map('TCheckbutton', 
                 background=[('active', '#1E1E1E')],
                 indicatorcolor=[('selected', '#007ACC'), ('!selected', '#3A3A3A')])
        
         # Estilo para Combobox
        style.configure('TCombobox', 
                    fieldbackground='#3A3A3A',
                    background='#1E1E1E',
                    foreground='white',
                    font=('Arial', 14),
                    padding=5)
        
        style.map('TCombobox',
                fieldbackground=[('readonly', '#3A3A3A')],
                selectbackground=[('readonly', '#505050')],
                selectforeground=[('readonly', 'white')])

    def toggle_gs_panel(self):
        if self.gs_visible:
            self.animate_panel_hide()
        else:
            self.animate_panel_show()

    def animate_panel_hide(self):
        self.gs_visible = False
        self.toggle_btn_right.place(relx=1, rely=0, anchor="ne", width=80, relheight=1)
        
        # Animación de deslizamiento
        for i in range(self.animation_speed + 1):
            relx = (1 - self.panel_width) + (self.panel_width * i/self.animation_speed)
            self.gs_frame.place_configure(relx=relx)
            self.root.update()
            time.sleep(0.02)
        
        self.gs_frame.place_forget()
        self.toggle_btn_left.place_forget()
        self.colmap_frame.pack(fill="both", expand=True)

    def animate_panel_show(self):
        self.gs_visible = True
        self.toggle_btn_right.place_forget()
        self.toggle_btn_left.place(relx=0, rely=0, anchor="nw", width=80, relheight=1)
        
        # Posicionar el frame GS fuera de vista a la derecha
        self.gs_frame.place(relx=1, rely=0, 
                        relwidth=self.panel_width, relheight=1)
        self.colmap_frame.pack_forget()
        
        # Animación de deslizamiento
        for i in range(self.animation_speed + 1):
            relx = 1 - (self.panel_width * i/self.animation_speed)
            self.gs_frame.place_configure(relx=relx)
            self.root.update()
            time.sleep(0.02)

    def save_preferences(self):
        prefs = {
            # COLMAP
            "path_tool": self.entry_ruta_herramienta.get(),
            "environment_name": self.entry_entorno.get(),

            # GS 
            "s": self.entry_s.get(),
            "m": self.entry_m.get(),
            "resolution": int(self.combo_resolution.get() or 1),
            "iterations": int(self.entry_iterations.get() or 30000),
            "save_iterations": self.entry_save_iterations.get(),
            "optimizer_type": self.entry_optimizer.get(),
            "antialiasing": self.antialiasing_var.get() or 0,
            "train_test_exp": self.train_test_exp.get(),
            "exposure_lr_init": float(self.entry_exp_lr_init.get()),
            "exposure_lr_final": float(self.entry_exp_lr_final.get()),
            "exposure_lr_delay_steps": int(self.entry_exp_lr_delay_steps.get()),
            "exposure_lr_delay_mult": float(self.entry_exp_lr_delay_mult.get()),
        }
        
        self.preferences.update(**prefs)
        self.preferences.save()
    
    def setup_colmap_interface(self):
        frame_botones = ttk.Frame(self.colmap_frame)
        frame_botones.place(relx=0.5, rely=0.5, anchor="center")

        # Label de advertencia
        self.label_advertencia = ttk.Label(frame_botones, 
                                    text="Antes de continuar asegúrate que desde la carpeta\nseleccionada puedas ver la carpeta 'input'", 
                                    style='Warning.TLabel')

        # Label carpeta actual
        self.label_carpeta_actual = ttk.Label(frame_botones, text="Carpeta actual: Ninguna")
        self.label_carpeta_actual.pack(pady=5)

        # Barra de progreso
        self.progressbar = ttk.Progressbar(frame_botones, orient="horizontal", 
                                        length=300, mode="determinate",
                                        style='Horizontal.TProgressbar')
        self.progressbar.pack(pady=10)

        # Contador de imágenes
        self.label_contador = ttk.Label(frame_botones, text="Imágenes cargadas: 0")
        self.label_contador.pack(pady=5)

        # Frame botones de carga
        frame_carga = ttk.Frame(frame_botones)
        frame_carga.pack(pady=10)

        # Botón cargar carpeta
        self.btn_carpeta = ttk.Button(frame_carga, text="📁 Cargar Carpeta",
                                    command=self.seleccionar_carpeta)
        self.btn_carpeta.pack(side="left", padx=10)

        # Botón cargar video
        self.btn_video = ttk.Button(frame_carga, text="🎥 Cargar Video",
                                  command=self.cargar_video)
        self.btn_video.pack(side="left", padx=10)

        # Frame opciones
        frame_opciones = ttk.Frame(frame_botones)
        frame_opciones.pack(pady=10)

        # Campos para mejores tomas
        ttk.Label(frame_opciones, text="Elegir las mejores").pack(side="left", padx=5)
        
        self.entry_n = ttk.Entry(frame_opciones, width=5, font=('Arial', 14))
        self.entry_n.pack(side="left", padx=5)
        self.entry_n.insert(0, "5")

        ttk.Label(frame_opciones, text="tomas cada").pack(side="left", padx=5)
        
        self.entry_framerate = ttk.Entry(frame_opciones, width=5, font=('Arial', 14))
        self.entry_framerate.pack(side="left", padx=5)
        self.entry_framerate.insert(0, "30")

        ttk.Label(frame_opciones, text="imágenes").pack(side="left", padx=5)

        # Botón extraer mejores tomas
        self.btn_extraer = ttk.Button(frame_botones, text="⭐ Extraer Mejores Tomas ⭐", 
                                    style='Highlight.TButton',
                                    command=self.extraer_mejores_tomas)
        self.btn_extraer.pack(pady=20)

        # Frame prueba entorno
        frame_prueba = ttk.Frame(frame_botones)
        frame_prueba.pack(pady=10)

        # Configuración entorno conda
        ttk.Label(frame_prueba, text="Nombre del entorno (conda):").pack(side="left", padx=5)
        
        self.entry_entorno = ttk.Entry(frame_prueba, width=20, font=('Arial', 14))
        self.entry_entorno.pack(side="left", padx=5)
        self.entry_entorno.insert(0, self.preferences.preferences["environment_name"])

        # Botón probar entorno
        self.btn_probar = ttk.Button(frame_prueba, text="Probar Entorno",
                                   command=self.probar_entorno_conda)
        self.btn_probar.pack(side="left", padx=5)

        # Frame ruta herramienta
        frame_ruta_herramienta = ttk.Frame(frame_botones)
        frame_ruta_herramienta.pack(pady=10)

        # Configuración ruta herramienta
        ttk.Label(frame_ruta_herramienta, text="Ruta de la herramienta:").pack(side="left", padx=5)
        
        self.entry_ruta_herramienta = ttk.Entry(frame_ruta_herramienta, width=30, font=('Arial', 14))
        self.entry_ruta_herramienta.pack(side="left", padx=5)
        self.entry_ruta_herramienta.insert(0, self.preferences.preferences["path_tool"])

        # Botón seleccionar carpeta
        self.btn_seleccionar_carpeta = ttk.Button(frame_ruta_herramienta, text="📁", 
                                                style='Icon.TButton',
                                                command=self.seleccionar_carpeta_herramienta)
        self.btn_seleccionar_carpeta.pack(side="left", padx=5)

        # Label advertencia
        self.label_advertencia.pack(pady=10)

        # Frame COLMAP
        frame_colmap = ttk.Frame(frame_botones)
        frame_colmap.pack(pady=10)

        # Checkbutton reescalar
        self.chkbtn_resize = BooleanVar(value=False)
        self.check_reescalar = ttk.Checkbutton(frame_colmap, 
                                        text="Reescalar (1/2, 1/4 y 1/8)", 
                                        variable=self.chkbtn_resize)
        self.check_reescalar.pack(side="left", padx=5)

        # Lista de botones para deshabilitar
        self.botones_colmap = [self.btn_carpeta, self.btn_video, self.btn_extraer, 
                            self.btn_probar, self.btn_seleccionar_carpeta]

        # Botón ejecutar COLMAP
        self.btn_colmap = ttk.Button(frame_colmap, text="📐COLMAP (convert)", 
                                   style='Highlight.TButton',
                                   command=self.ejecutar_colmap)
        self.btn_colmap.pack(side="left", padx=5)
    
    def setup_gs_interface(self):
        # Frame principal para los componentes
        main_frame = ttk.Frame(self.gs_frame)
        main_frame.pack(fill="both", expand=True, padx=(100,20), pady=20)

        # Botón para crear reconstrucción (centrado arriba)
        self.btn_create_3dgs = ttk.Button(
            main_frame,
            text="✨ Crear reconstrucción 3DGS ✨",
            style='Highlight.TButton',
            command=self.execute_3dgs_reconstruction
        )
        self.btn_create_3dgs.pack(pady=(0, 20), fill='x')
        
        # Frame para organizar en 2 columnas
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill="x", padx=10, pady=10)
        
        # Configuración de grid
        form_frame.columnconfigure(0, weight=1)
        form_frame.columnconfigure(1, weight=3)
        
        # Componentes de Gaussian Splatting
        ttk.Label(form_frame, text="Entrada:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_s = ttk.Entry(form_frame, font=('Arial', 14))
        self.entry_s.grid(row=0, column=1, sticky="ew", pady=5)
        self.entry_s.insert(0, self.preferences.preferences.get("s", ""))
        
        ttk.Label(form_frame, text="Salida:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_m = ttk.Entry(form_frame, font=('Arial', 14))
        self.entry_m.grid(row=1, column=1, sticky="ew", pady=5)
        self.entry_m.insert(0, self.preferences.preferences.get("m", ""))
        
        ttk.Label(form_frame, text="Resolución:").grid(row=2, column=0, sticky="w", pady=5)
        self.combo_resolution = ttk.Combobox(form_frame, values=[1, 2, 4, 8],style='TCombobox')
        self.combo_resolution.grid(row=2, column=1, sticky="ew", pady=5)
        self.combo_resolution.set(self.preferences.preferences.get("resolution", 1))
        
        ttk.Label(form_frame, text="Iteraciones:").grid(row=3, column=0, sticky="w", pady=5)
        self.entry_iterations = ttk.Entry(form_frame, font=('Arial', 14))
        self.entry_iterations.grid(row=3, column=1, sticky="ew", pady=5)
        self.entry_iterations.insert(0, self.preferences.preferences.get("iterations", ""))
        
        ttk.Label(form_frame, text="Guardar en las iteraciones:").grid(row=4, column=0, sticky="w", pady=5)
        self.entry_save_iterations = ttk.Entry(form_frame, font=('Arial', 14))
        self.entry_save_iterations.grid(row=4, column=1, sticky="ew", pady=5)
        self.entry_save_iterations.insert(0, self.preferences.preferences.get("save_iterations", ""))
        
        ttk.Label(form_frame, text="Optimizador:").grid(row=5, column=0, sticky="w", pady=5)
        self.entry_optimizer = ttk.Entry(form_frame, font=('Arial', 14))
        self.entry_optimizer.grid(row=5, column=1, sticky="ew", pady=5)
        self.entry_optimizer.insert(0, self.preferences.preferences.get("optimizer_type", ""))
        
        self.antialiasing_var = BooleanVar(value=self.preferences.preferences.get("antialiasing", False))
        self.check_antialiasing = ttk.Checkbutton(
            form_frame, 
            text="Antialiasing", 
            variable=self.antialiasing_var,
            style='TCheckbutton'
        )
        self.check_antialiasing.grid(row=6, column=0, columnspan=2, sticky="w", pady=5)

        # Frame principal para los componentes de exposición
        self.exposure_frame = ttk.Frame(form_frame)
        self.exposure_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=0)

        # Checkbutton para compensar exposición
        self.train_test_exp = BooleanVar(value=self.preferences.preferences.get("train_test_exp", False))
        self.check_exp = ttk.Checkbutton(
            self.exposure_frame,
            text="Compensar exposición",
            variable=self.train_test_exp,
            style='TCheckbutton',
            command=self.toggle_exposure_entries
        )
        self.check_exp.grid(row=0, column=0, sticky="w", pady=(10,0))

        # Botón/Separador desplegable
        self.toggle_expand_btn = ttk.Button(
            self.exposure_frame,
            text="▼ Configuración Avanzada de Exposición ▼",
            style='Toggle.TButton',
            command=self.toggle_expandable_menu
        )
        self.toggle_expand_btn.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5,0))

        # Frame contenedor del menú desplegable (fuera del exposure_frame)
        self.expandable_content = ttk.Frame(form_frame)
        self.expandable_content.grid(row=8, column=0, columnspan=2, sticky="ew", pady=0)
        self.expandable_content.grid_remove()  # Oculto inicialmente

        # Campos de exposición
        ttk.Label(self.expandable_content, text="Exposure lr init:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_exp_lr_init = ttk.Entry(self.expandable_content, font=('Arial', 14))
        self.entry_exp_lr_init.grid(row=0, column=1, sticky="ew", pady=5)
        self.entry_exp_lr_init.insert(0, str(self.preferences.preferences.get("exposure_lr_init", 0.01)))

        ttk.Label(self.expandable_content, text="Exposure lr final:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_exp_lr_final = ttk.Entry(self.expandable_content, font=('Arial', 14))
        self.entry_exp_lr_final.grid(row=1, column=1, sticky="ew", pady=5)
        self.entry_exp_lr_final.insert(0, str(self.preferences.preferences.get("exposure_lr_final", 0.0001)))

        ttk.Label(self.expandable_content, text="Exposure lr delay steps:").grid(row=2, column=0, sticky="w", pady=5)
        self.entry_exp_lr_delay_steps = ttk.Entry(self.expandable_content, font=('Arial', 14))
        self.entry_exp_lr_delay_steps.grid(row=2, column=1, sticky="ew", pady=5)
        self.entry_exp_lr_delay_steps.insert(0, str(self.preferences.preferences.get("exposure_lr_delay_steps", 1000)))

        ttk.Label(self.expandable_content, text="Exposure lr delay mult:").grid(row=3, column=0, sticky="w", pady=5)
        self.entry_exp_lr_delay_mult = ttk.Entry(self.expandable_content, font=('Arial', 14))
        self.entry_exp_lr_delay_mult.grid(row=3, column=1, sticky="ew", pady=5)
        self.entry_exp_lr_delay_mult.insert(0, str(self.preferences.preferences.get("exposure_lr_delay_mult", 0.01)))

        # Estado inicial
        self.expanded = False
        self.toggle_exposure_entries() 

    def toggle_exposure_entries(self):
        state = "normal" if self.train_test_exp.get() else "disabled"
        self.entry_exp_lr_init.config(state=state)
        self.entry_exp_lr_final.config(state=state)
        self.entry_exp_lr_delay_steps.config(state=state)
        self.entry_exp_lr_delay_mult.config(state=state)

    def toggle_expandable_menu(self):
        if self.expanded:
            self.expandable_content.grid_remove()
            self.toggle_expand_btn.config(text="▼ Configuración Avanzada de Exposición ▼")
        else:
            self.expandable_content.grid()
            self.toggle_expand_btn.config(text="▲ Configuración Avanzada de Exposición ▲")
        
        self.expanded = not self.expanded
        self.root.update_idletasks()

    def execute_3dgs_reconstruction(self):
        """Ejecuta el comando para crear la reconstrucción 3DGS con todos los parámetros configurados"""
        if not self.verify_environment():
            return
        try:
            # Verificar que tenemos los datos necesarios
            if not all([self.entry_s.get(), self.entry_m.get(), self.entry_entorno.get(), self.entry_ruta_herramienta.get()]):
                messagebox.showerror("Error", "Faltan parámetros esenciales (entrada, salida, entorno o ruta herramienta)")
                return

            # Construir el comando base
            env_name = self.entry_entorno.get()
            tool_path = self.entry_ruta_herramienta.get()
            base_cmd = f'conda run -n {env_name} python "{tool_path}/train.py"'

            # Parámetros normales (nombre: valor)
            normal_params = {
                'resolution': self.combo_resolution.get(),
                'iterations': self.entry_iterations.get(),
                'save_iterations': self.entry_save_iterations.get(),
                'optimizer_type': self.entry_optimizer.get(),
            }

            # Parámetros booleanos (solo se añaden si son True)
            bool_params = {
                'train_test_exp': self.train_test_exp.get(),
                'antialiasing': self.antialiasing_var.get()
            }

            # Parámetros especiales (rutas entre comillas)
            path_params = {
                's': self.entry_s.get(),
                'm': self.entry_m.get()
            }

            # Parámetros de exposición (solo si train_test_exp es True)
            exp_params = {}
            if bool_params['train_test_exp']:
                exp_params = {
                    'exposure_lr_init': self.entry_exp_lr_init.get(),
                    'exposure_lr_final': self.entry_exp_lr_final.get(),
                    'exposure_lr_delay_steps': self.entry_exp_lr_delay_steps.get(),
                    'exposure_lr_delay_mult': self.entry_exp_lr_delay_mult.get()
                }

            # Construir la parte de parámetros del comando
            param_str = ""
            
            # 1. Añadir parámetros de rutas (entre comillas)
            for param, value in path_params.items():
                if value:
                    prefix = "-"  # -s y -m son de un solo carácter
                    param_str += f' {prefix}{param} "{value}"'
            
            # 2. Añadir parámetros normales
            for param, value in normal_params.items():
                if value:
                    prefix = "--" if len(param) > 1 else "-"
                    param_str += f" {prefix}{param} {value}"
            
            # 3. Añadir parámetros booleanos (solo si son True)
            for param, value in bool_params.items():
                if value:
                    prefix = "--"  # Todos los booleanos tienen más de un carácter
                    param_str += f" {prefix}{param}"
            
            # 4. Añadir parámetros de exposición (si aplica)
            for param, value in exp_params.items():
                if value:
                    prefix = "--"  # Todos los de exposición tienen más de un carácter
                    param_str += f" {prefix}{param} {value}"

            # Comando final
            full_cmd = f"{base_cmd}{param_str}"
            print(f"Ejecutando comando: {full_cmd}")  # Para depuración

            # Ejecutar en un hilo para no bloquear la interfaz
            threading.Thread(
                target=self.run_3dgs_command,
                args=(full_cmd,),
                daemon=True
            ).start()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo preparar el comando: {str(e)}")

    """def run_3dgs_command(self, command):
        try:
            self.btn_create_3dgs.config(state="disabled")
            
            # Ejecutar el comando
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Leer la salida en tiempo real
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())  # Puedes redirigir esto a un log si lo prefieres
            
            # Verificar el resultado
            return_code = process.poll()
            if return_code == 0:
                messagebox.showinfo("Éxito", "Reconstrucción 3DGS completada con éxito")
            else:
                error = process.stderr.read()
                messagebox.showerror("Error", f"Error en la reconstrucción:\n{error}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al ejecutar el comando: {str(e)}")
        finally:
            self.btn_create_3dgs.config(state="normal")"""
    def run_3dgs_command(self, command):
        try:
            self.btn_create_3dgs.config(state="disabled")
            
            # Verificar dependencias primero
            check_cmd = f'conda run -n {self.entry_entorno.get()} python -c "import torch; import subprocess; print(\'Dependencias OK\')"'
            check_process = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            
            if check_process.returncode != 0:
                error_msg = "Error: Paquetes esenciales no instalados\n\n"
                if "No module named 'torch'" in check_process.stderr:
                    error_msg += "• PyTorch no está instalado\n"
                if "No module named 'subprocess'" in check_process.stderr:
                    error_msg += "• Paquetes básicos de Python faltantes\n"
                
                error_msg += "\nPor favor instale los paquetes requeridos con:\n"
                error_msg += f"conda activate {self.entry_entorno.get()}\n"
                error_msg += "conda install pytorch torchvision torchaudio -c pytorch\n"
                messagebox.showerror("Dependencias faltantes", error_msg)
                return

            # Si las dependencias están OK, ejecutar el comando principal
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Crear ventana de progreso
            progress = tk.Toplevel(self.root)
            progress.title("Progreso de la reconstrucción")
            progress.geometry("600x400")
            
            tk.Label(progress, text="Ejecutando reconstrucción 3DGS...", font=('Arial', 12)).pack(pady=10)
            
            progress_text = tk.Text(progress, wrap=tk.WORD)
            progress_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scrollbar = tk.Scrollbar(progress_text)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            progress_text.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=progress_text.yview)
            
            def update_output():
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        progress_text.insert(tk.END, output)
                        progress_text.see(tk.END)
                        progress.update()
                progress.destroy()
            
            threading.Thread(target=update_output, daemon=True).start()
            
            # Esperar a que termine el proceso
            return_code = process.wait()
            
            if return_code == 0:
                messagebox.showinfo("Éxito", "Reconstrucción 3DGS completada con éxito")
            else:
                error = process.stderr.read()
                error_msg = f"Error en la reconstrucción (código {return_code}):\n\n"
                
                # Errores comunes y sus soluciones
                if "No module named 'torch'" in error:
                    error_msg += "ERROR: PyTorch no está instalado en el entorno.\n\n"
                    error_msg += "Solución:\n"
                    error_msg += f"1. Activar el entorno: conda activate {self.entry_entorno.get()}\n"
                    error_msg += "2. Instalar PyTorch: conda install pytorch torchvision torchaudio -c pytorch\n"
                elif "CUDA out of memory" in error:
                    error_msg += "ERROR: Memoria GPU insuficiente.\n\n"
                    error_msg += "Solución:\n"
                    error_msg += "1. Reducir la resolución (--resolution)\n"
                    error_msg += "2. Cerrar otras aplicaciones que usen GPU\n"
                    error_msg += "3. Usar un modelo con menos parámetros\n"
                else:
                    error_msg += error
                
                messagebox.showerror("Error", error_msg)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al ejecutar el comando: {str(e)}")
        finally:
            self.btn_create_3dgs.config(state="normal")

    def verify_environment(self):
        """Verifica que el entorno tenga todas las dependencias necesarias"""
        try:
            env_name = self.entry_entorno.get()
            if not env_name:
                messagebox.showerror("Error", "No se ha especificado un entorno Conda")
                return False
            
            # Comando para verificar paquetes esenciales
            check_cmd = (
                f'conda run -n {env_name} python -c '
                '"import torch; import torchvision; import numpy; print(\'Dependencias OK\')"'
            )
            
            process = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            
            if process.returncode != 0:
                error_msg = "Faltan dependencias esenciales:\n"
                if "No module named 'torch'" in process.stderr:
                    error_msg += "\n- PyTorch no está instalado"
                if "No module named 'torchvision'" in process.stderr:
                    error_msg += "\n- TorchVision no está instalado"
                if "No module named 'numpy'" in process.stderr:
                    error_msg += "\n- NumPy no está instalado"
                
                error_msg += "\n\nInstale las dependencias con:\n"
                error_msg += f"conda activate {env_name}\n"
                error_msg += "conda install pytorch torchvision numpy -c pytorch"
                
                messagebox.showerror("Dependencias faltantes", error_msg)
                return False
            
            return True
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo verificar el entorno: {str(e)}")
            return False
        
    def actualizar_contador(self):
        if not self.ruta_imagenes or not os.path.exists(self.ruta_imagenes):
            self.label_contador.config(text="Imágenes cargadas: 0")
            self.label_carpeta_actual.config(text="Carpeta actual: Ninguna")
            self.label_advertencia.config(text="Antes de continuar asegúrate que desde la carpeta\nseleccionada puedas ver la carpeta 'input'", style='Warning.TLabel')
            return

        formatos_imagen = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"]
        lista_archivos = [archivo for archivo in os.listdir(self.ruta_imagenes) 
                        if any(archivo.lower().endswith(formato) for formato in formatos_imagen)]

        self.label_contador.config(text=f"Imágenes cargadas: {len(lista_archivos)}")
        self.label_carpeta_actual.config(text=f"Carpeta actual: {self.ruta_imagenes}")

        ruta_input = os.path.join(self.ruta_imagenes, "input")
        if os.path.exists(ruta_input) and os.path.isdir(ruta_input):
            self.label_advertencia.config(text="Carpeta 'input' encontrada", style='Success.TLabel')
        else:
            self.label_advertencia.config(text="Antes de continuar asegúrate que desde la carpeta\nseleccionada puedas ver la carpeta 'input'", style='Warning.TLabel')
    
    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory()
        if not carpeta: 
            return

        self.entry_framerate.delete(0, "end")
        self.ruta_imagenes = carpeta
        self.actualizar_contador()
    
    def seleccionar_carpeta_herramienta(self):
        carpeta_seleccionada = filedialog.askdirectory() 
        if carpeta_seleccionada: 
            self.entry_ruta_herramienta.delete(0, "end") 
            self.entry_ruta_herramienta.insert(0, carpeta_seleccionada)
    
    def cargar_video(self):
        ruta_video = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mkv")])
        if not ruta_video: 
            return

        threading.Thread(
            target=self.extraer_frames,
            args=(ruta_video,),
            daemon=True
        ).start()
    
    def extraer_frames(self, ruta_video):
        try:
            carpeta_frames = os.path.join(os.path.dirname(ruta_video), "input")
            os.makedirs(carpeta_frames, exist_ok=True)

            cap = cv2.VideoCapture(ruta_video)
            fps_video = int(cap.get(cv2.CAP_PROP_FPS))

            self.root.after(0, self.entry_framerate.delete, 0, "end")
            self.root.after(0, self.entry_framerate.insert, 0, str(fps_video))

            rotation_code = self.obtener_rotacion_video(ruta_video)
            frame_count = 0
            saved_count = 0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if rotation_code is not None:
                    frame = self.rotar_frame(frame, rotation_code)

                ruta_frame = os.path.join(carpeta_frames, f"frame_{saved_count:04d}.jpg")
                cv2.imwrite(ruta_frame, frame)
                saved_count += 1

                progreso = (frame_count + 1) / total_frames * 100
                self.root.after(0, self.actualizar_progreso, progreso)
                frame_count += 1

            cap.release()
            self.root.after(0, messagebox.showinfo, "Éxito", f"Se extrajeron {saved_count} frames en {carpeta_frames}")

            self.ruta_imagenes = carpeta_frames
            self.root.after(0, self.actualizar_contador)
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", f"No se pudo extraer los frames: {e}")
    
    def actualizar_progreso(self, valor):
        self.progressbar["value"] = valor
        self.root.update_idletasks()
    
    def obtener_rotacion_video(self, ruta_video):
        try:
            import ffmpeg 
            metadata = ffmpeg.probe(ruta_video)
            for stream in metadata.get("streams", []):
                if stream.get("codec_type") == "video":
                    rotation = stream.get("tags", {}).get("rotate")
                    if rotation:
                        return int(rotation)
            return None
        except Exception:
            return None
    
    def rotar_frame(self, frame, rotation_code):
        if rotation_code == 90:
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif rotation_code == 180:
            return cv2.rotate(frame, cv2.ROTATE_180)
        elif rotation_code == 270:
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return frame
    
    def extraer_mejores_tomas(self):
        if not self.ruta_imagenes:
            self.root.after(0, messagebox.showwarning, "Atención", "No hay imágenes cargadas.")
            return

        self.root.after(0, lambda: self.btn_extraer.config(state="disabled"))

        try:
            n = int(self.entry_n.get())
            if n <= 0:
                self.root.after(0, messagebox.showerror, "Error", "El número de imágenes por segundo debe ser mayor que 0.")
                self.root.after(0, lambda: self.btn_extraer.config(state="normal"))
                return
        except ValueError:
            self.root.after(0, messagebox.showerror, "Error", "El valor ingresado no es válido.")
            self.root.after(0, lambda: self.btn_extraer.config(state="normal"))
            return

        try:
            fps_video = int(self.entry_framerate.get()) if self.entry_framerate.get() else 30
        except ValueError:
            self.root.after(0, messagebox.showerror, "Error", "El framerate ingresado no es válido.")
            self.root.after(0, lambda: self.btn_extraer.config(state="normal"))
            return

        threading.Thread(
            target=self.procesar_mejores_tomas,
            args=(n, fps_video),
            daemon=True
        ).start()
    
    def procesar_mejores_tomas(self, n, fps_video):
        try:
            formatos_imagen = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"]
            lista_archivos = [archivo for archivo in os.listdir(self.ruta_imagenes) 
                            if any(archivo.lower().endswith(formato) for formato in formatos_imagen)]
            rutas_imagenes = [os.path.join(self.ruta_imagenes, archivo) for archivo in lista_archivos]

            evaluador = Evaluators([(ruta, Image.open(ruta).convert("RGB")) for ruta in rutas_imagenes])
            scores = evaluador.evalTenengradSobel()

            imagenes_por_segundo = {}
            total_imagenes = len(rutas_imagenes)
            for i, (ruta, score) in enumerate(zip(rutas_imagenes, scores)):
                segundo = i // fps_video
                if segundo not in imagenes_por_segundo:
                    imagenes_por_segundo[segundo] = []
                imagenes_por_segundo[segundo].append((ruta, score))

                progreso = (i + 1) / total_imagenes * 100
                self.root.after(0, self.actualizar_progreso, progreso)
                self.root.update_idletasks()

            nuevas_rutas = []
            for segundo, imagenes in imagenes_por_segundo.items():
                imagenes.sort(key=lambda x: x[1], reverse=True)
                nuevas_rutas.extend([ruta for ruta, _ in imagenes[:n]])

            carpeta_mejores_tomas = os.path.join(self.ruta_imagenes, "input")
            os.makedirs(carpeta_mejores_tomas, exist_ok=True)

            for ruta in nuevas_rutas:
                nombre_archivo = os.path.basename(ruta)
                shutil.copy(ruta, os.path.join(carpeta_mejores_tomas, nombre_archivo))

            self.ruta_imagenes = carpeta_mejores_tomas
            self.root.after(0, self.actualizar_contador)
            self.root.after(0, messagebox.showinfo, "Éxito", f"Se conservaron las mejores {n} imágenes por segundo en {carpeta_mejores_tomas}.")
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", f"No se pudo filtrar las imágenes: {e}")
        finally:
            self.root.after(0, lambda: self.btn_extraer.config(state="normal"))
    
    def probar_entorno_conda(self):
        try:
            self.root.after(0, lambda: self.btn_probar.config(state="disabled"))
            nombre_entorno = self.entry_entorno.get()
            comando = f'conda run -n {nombre_entorno} python -c "print(\'¡Entorno {nombre_entorno} cargado correctamente!\')"'
            
            proceso = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            salida, errores = proceso.communicate()

            if salida:
                self.root.after(0, messagebox.showinfo, "Salida", salida.decode("utf-8"))
            if errores:
                self.root.after(0, messagebox.showerror, "Errores", errores.decode("utf-8"))
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", f"No se pudo ejecutar el comando: {e}")
        finally:
            self.root.after(0, lambda: self.btn_probar.config(state="normal"))
    
    def ejecutar_colmap(self):
        if not self.ruta_imagenes:
            messagebox.showerror("Error", "No se ha seleccionado una carpeta con el nombre 'input'.")
            return

        ruta_input = os.path.join(self.ruta_imagenes, "input")
        if not os.path.exists(ruta_input) or not os.path.isdir(ruta_input):
            messagebox.showerror("Error", f"No se encontró la carpeta 'input' en: {self.ruta_imagenes}")
            return

        for boton in self.botones_colmap:
            self.root.after(0, lambda b=boton: b.config(state="disabled"))
        self.root.after(0, lambda: self.btn_colmap.config(state="disabled"))

        try:
            env_name = self.entry_entorno.get()
            ruta_herramienta = self.entry_ruta_herramienta.get()

            comando = f'conda run -n {env_name} py {ruta_herramienta}/convert.py -s {self.ruta_imagenes}'
            if self.chkbtn_resize.get():
                comando += " --resize"

            print("Ejecutando COLMAP...")
            proceso = subprocess.run(comando, shell=True, capture_output=True, text=True)

            if proceso.stdout:
                print("Salida de COLMAP:", proceso.stdout)
            if proceso.stderr:
                print("Errores de COLMAP:", proceso.stderr)

            messagebox.showinfo("Éxito", "Proceso de COLMAP completado.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo ejecutar el comando: {e}")
        finally:
            for boton in self.botones_colmap:
                self.root.after(0, lambda b=boton: b.config(state="normal"))
            self.root.after(0, lambda: self.btn_colmap.config(state="normal"))

    def on_close(self):
        self.save_preferences()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()