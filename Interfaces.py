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

class MainApp:
    def __init__(self, root, preferences):
        self.root = root
        self.preferences = preferences
        self.ruta_imagenes = None
        self.root.title("Visualizador de Imágenes")
        self.root.geometry("1000x700")
        self.root.configure(bg="#1E1E1E")
        
        # Variables de estado
        self.gs_visible = False
        self.animation_speed = 5
        self.panel_width = 0.25  # Ancho relativo de los paneles
        
        # Frame principal
        self.main_frame = tk.Frame(root, bg="#1E1E1E")
        self.main_frame.pack(fill="both", expand=True)
        
        # Frame COLMAP
        self.colmap_frame = tk.Frame(self.main_frame, bg="#1E1E1E")
        self.colmap_frame.pack(fill="both", expand=True)
        
        # Frame Gaussian Splatting (inicialmente oculto)
        self.gs_frame = tk.Frame(self.main_frame, bg="#252526")
        
        # Botón de alternancia derecho (para COLMAP)
        self.toggle_btn_right = tk.Button(self.main_frame, 
                                        text="Gaussian\nSplatting >", 
                                        font=("Arial", 10, "bold"), 
                                        fg="white", bg="#007ACC",
                                        relief="flat", 
                                        borderwidth=0,
                                        command=self.toggle_gs_panel)
        self.toggle_btn_right.place(relx=1, rely=0, anchor="ne", 
                                  width=60, relheight=1)
        
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
        self.gs_frame = Frame(self.main_frame, bg="#252526")
        
        # Botón de alternancia
        self.toggle_btn = Button(self.main_frame, text="> Gaussian Splatting", 
                               font=("Arial", 10, "bold"), fg="white", bg="#007ACC",
                               relief="flat", command=self.toggle_gs_panel)
        self.toggle_btn.place(relx=0, rely=0.5, anchor="w", width=120, height=40)
        
        self.setup_colmap_interface()
        self.setup_gs_interface()
    
    def setup_colmap_interface(self):
        frame_botones = Frame(self.colmap_frame, bg="#1E1E1E")
        frame_botones.place(relx=0.5, rely=0.5, anchor="center")

        # Label de advertencia
        self.label_advertencia = Label(frame_botones, 
                                     text="Antes de continuar asegúrate que desde la carpeta\nseleccionada puedas ver la carpeta 'input'", 
                                     font=("Arial", 12), fg="red", bg="#1E1E1E")

        # Label carpeta actual
        self.label_carpeta_actual = Label(frame_botones, text="Carpeta actual: Ninguna", 
                                        font=("Arial", 12), fg="white", bg="#1E1E1E")
        self.label_carpeta_actual.pack(pady=5)

        # Barra de progreso
        self.progressbar = ttk.Progressbar(frame_botones, orient="horizontal", 
                                         length=300, mode="determinate")
        self.progressbar.pack(pady=10)

        # Contador de imágenes
        self.label_contador = Label(frame_botones, text="Imágenes cargadas: 0", 
                                  font=("Arial", 12), fg="white", bg="#1E1E1E")
        self.label_contador.pack(pady=5)

        # Frame botones de carga
        frame_carga = Frame(frame_botones, bg="#1E1E1E")
        frame_carga.pack(pady=10)

        # Botón cargar carpeta
        self.btn_carpeta = Button(frame_carga, text="📁 Cargar Carpeta", width=20, height=2,
                                fg="white", bg="#3A3A3A", relief="flat",
                                activebackground="#505050", font=("Arial", 12, "bold"),
                                command=self.seleccionar_carpeta)
        self.btn_carpeta.pack(side="left", padx=10)

        # Botón cargar video
        self.btn_video = Button(frame_carga, text="🎥 Cargar Video", width=20, height=2,
                              fg="white", bg="#3A3A3A", relief="flat",
                              activebackground="#505050", font=("Arial", 12, "bold"),
                              command=self.cargar_video)
        self.btn_video.pack(side="left", padx=10)

        # Frame opciones
        frame_opciones = Frame(frame_botones, bg="#1E1E1E")
        frame_opciones.pack(pady=10)

        # Campos para mejores tomas
        Label(frame_opciones, text="Elegir las mejores", font=("Arial", 12), 
             fg="white", bg="#1E1E1E").pack(side="left", padx=5)
        
        self.entry_n = Entry(frame_opciones, font=("Arial", 12), bg="#3A3A3A", 
                           fg="white", insertbackground="white", width=5)
        self.entry_n.pack(side="left", padx=5)
        self.entry_n.insert(0, "5")

        Label(frame_opciones, text="tomas cada", font=("Arial", 12), 
             fg="white", bg="#1E1E1E").pack(side="left", padx=5)
        
        self.entry_framerate = Entry(frame_opciones, font=("Arial", 12), bg="#3A3A3A", 
                                   fg="white", insertbackground="white", width=5)
        self.entry_framerate.pack(side="left", padx=5)
        self.entry_framerate.insert(0, "30")

        Label(frame_opciones, text="imágenes", font=("Arial", 12), 
             fg="white", bg="#1E1E1E").pack(side="left", padx=5)

        # Botón extraer mejores tomas
        self.btn_extraer = Button(frame_botones, text="⭐ Extraer Mejores Tomas ⭐", 
                                width=30, height=2, fg="white", bg="#3A3A3A", 
                                relief="flat", activebackground="#505050", 
                                font=("Arial", 14, "bold"),
                                command=self.extraer_mejores_tomas)
        self.btn_extraer.pack(pady=20)

        # Frame prueba entorno
        frame_prueba = Frame(frame_botones, bg="#1E1E1E")
        frame_prueba.pack(pady=10)

        # Configuración entorno conda
        Label(frame_prueba, text="Nombre del entorno (conda):", font=("Arial", 12), 
             fg="white", bg="#1E1E1E").pack(side="left", padx=5)
        
        self.entry_entorno = Entry(frame_prueba, font=("Arial", 12), bg="#3A3A3A", 
                                 fg="white", insertbackground="white", width=20)
        self.entry_entorno.pack(side="left", padx=5)
        self.entry_entorno.insert(0, self.preferences.preferences["environment_name"])

        # Botón probar entorno
        self.btn_probar = Button(frame_prueba, text="Probar Entorno", width=15, height=1,
                               fg="white", bg="#3A3A3A", relief="flat",
                               activebackground="#505050", font=("Arial", 12, "bold"),
                               command=self.probar_entorno_conda)
        self.btn_probar.pack(side="left", padx=5)

        # Frame ruta herramienta
        frame_ruta_herramienta = Frame(frame_botones, bg="#1E1E1E")
        frame_ruta_herramienta.pack(pady=10)

        # Configuración ruta herramienta
        Label(frame_ruta_herramienta, text="Ruta de la herramienta:", 
             font=("Arial", 12), fg="white", bg="#1E1E1E").pack(side="left", padx=5)
        
        self.entry_ruta_herramienta = Entry(frame_ruta_herramienta, font=("Arial", 12), 
                                          bg="#3A3A3A", fg="white", 
                                          insertbackground="white", width=30)
        self.entry_ruta_herramienta.pack(side="left", padx=5)
        self.entry_ruta_herramienta.insert(0, self.preferences.preferences["path_tool"])

        # Botón seleccionar carpeta
        self.btn_seleccionar_carpeta = Button(frame_ruta_herramienta, text="📁", 
                                            font=("Arial", 18), fg="white", 
                                            bg="#3A3A3A", relief="flat",
                                            activebackground="#505050", 
                                            command=self.seleccionar_carpeta_herramienta)
        self.btn_seleccionar_carpeta.pack(side="left", padx=5)

        # Label advertencia
        self.label_advertencia.pack(pady=10)

        # Frame COLMAP
        frame_colmap = Frame(frame_botones, bg="#1E1E1E")
        frame_colmap.pack(pady=10)

        # Checkbutton reescalar
        self.chkbtn_resize = BooleanVar(value=False)
        self.check_reescalar = Checkbutton(frame_colmap, 
                                          text="Reescalar (1/2, 1/4 y 1/8)", 
                                          font=("Arial", 14), 
                                          fg="white", bg="#1E1E1E", 
                                          selectcolor="#3A3A3A", 
                                          variable=self.chkbtn_resize)
        self.check_reescalar.pack(side="left", padx=5)

        # Lista de botones para deshabilitar
        self.botones_colmap = [self.btn_carpeta, self.btn_video, self.btn_extraer, 
                              self.btn_probar, self.btn_seleccionar_carpeta]

        # Botón ejecutar COLMAP
        self.btn_colmap = Button(frame_colmap, text="📐COLMAP (convert)", 
                               font=("Arial", 14), fg="white", bg="#3A3A3A", 
                               relief="flat", activebackground="#505050", 
                               command=self.ejecutar_colmap)
        self.btn_colmap.pack(side="left", padx=5)

        # Separador inferior
        ttk.Separator(self.colmap_frame, orient="horizontal").pack(fill="x", pady=20, side="bottom")
    
    def setup_gs_interface(self):
        # Contenido básico para Gaussian Splatting
        Label(self.gs_frame, text="Herramientas Gaussian Splatting", 
             font=("Arial", 16), fg="white", bg="#252526").pack(pady=50)
        
        Button(self.gs_frame, text="< Volver a COLMAP", 
              font=("Arial", 10), fg="white", bg="#3E3E40",
              command=self.toggle_gs_panel).pack(pady=20)
        
    def animate_panel_hide(self):
        self.gs_visible = False
        self.toggle_btn_right.config(text="Gaussian\nSplatting >")
        
        # Animación de deslizamiento
        for i in range(self.animation_speed + 1):
            relx = (1 - self.panel_width) + (self.panel_width * i/self.animation_speed)
            self.gs_frame.place_configure(relx=relx)
            self.root.update()
            time.sleep(0.02)
        
        self.gs_frame.place_forget()
        self.toggle_btn_left.place_forget()
        self.colmap_frame.pack(fill="both", expand=True)
    
    def toggle_gs_panel(self):
        if self.gs_visible:
            self.animate_panel_hide()
        else:
            self.animate_panel_show()

    def animate_panel_show(self):
        self.gs_visible = True
        self.toggle_btn_right.config(text="< Ocultar")
        self.toggle_btn_left.place(relx=0, rely=0, anchor="nw", 
                                  width=60, relheight=1)
        
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
    
    # Métodos convertidos de funciones originales
    def actualizar_contador(self):
        if not self.ruta_imagenes or not os.path.exists(self.ruta_imagenes):
            self.label_contador.config(text="Imágenes cargadas: 0")
            self.label_carpeta_actual.config(text="Carpeta actual: Ninguna")
            self.label_advertencia.config(text="Antes de continuar asegúrate que desde la carpeta\nseleccionada puedas ver la carpeta 'input'")
            return

        formatos_imagen = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"]
        lista_archivos = [archivo for archivo in os.listdir(self.ruta_imagenes) 
                         if any(archivo.lower().endswith(formato) for formato in formatos_imagen)]

        self.label_contador.config(text=f"Imágenes cargadas: {len(lista_archivos)}")
        self.label_carpeta_actual.config(text=f"Carpeta actual: {self.ruta_imagenes}")

        ruta_input = os.path.join(self.ruta_imagenes, "input")
        if os.path.exists(ruta_input) and os.path.isdir(ruta_input):
            self.label_advertencia.config(text="Carpeta 'input' encontrada", fg="green")
        else:
            self.label_advertencia.config(text="Antes de continuar asegúrate que desde la carpeta\nseleccionada puedas ver la carpeta 'input'", fg="red")
    
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

        self.root.after(0, self.btn_extraer.config, {"state": "disabled"})

        try:
            n = int(self.entry_n.get())
            if n <= 0:
                self.root.after(0, messagebox.showerror, "Error", "El número de imágenes por segundo debe ser mayor que 0.")
                self.root.after(0, self.btn_extraer.config, {"state": "normal"})
                return
        except ValueError:
            self.root.after(0, messagebox.showerror, "Error", "El valor ingresado no es válido.")
            self.root.after(0, self.btn_extraer.config, {"state": "normal"})
            return

        try:
            fps_video = int(self.entry_framerate.get()) if self.entry_framerate.get() else 30
        except ValueError:
            self.root.after(0, messagebox.showerror, "Error", "El framerate ingresado no es válido.")
            self.root.after(0, self.btn_extraer.config, {"state": "normal"})
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
            self.root.after(0, self.btn_extraer.config, {"state": "normal"})
    
    def probar_entorno_conda(self):
        try:
            self.root.after(0, self.btn_probar.config, {"state": "disabled"})
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
            self.root.after(0, self.btn_probar.config, {"state": "normal"})
    
    def ejecutar_colmap(self):
        if not self.ruta_imagenes:
            messagebox.showerror("Error", "No se ha seleccionado una carpeta con el nombre 'input'.")
            return

        ruta_input = os.path.join(self.ruta_imagenes, "input")
        if not os.path.exists(ruta_input) or not os.path.isdir(ruta_input):
            messagebox.showerror("Error", f"No se encontró la carpeta 'input' en: {self.ruta_imagenes}")
            return

        for boton in self.botones_colmap:
            self.root.after(0, boton.config, {"state": "disabled"})
        self.root.after(0, self.btn_colmap.config, {"state": "disabled"})

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
                self.root.after(0, boton.config, {"state": "normal"})
            self.root.after(0, self.btn_colmap.config, {"state": "normal"})

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()