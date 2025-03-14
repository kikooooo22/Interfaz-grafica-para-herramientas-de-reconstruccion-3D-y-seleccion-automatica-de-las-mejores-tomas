import os
import subprocess
import cv2
import shutil
import threading 
from tkinter import Tk, Button, Frame, Label, Entry, BooleanVar, Checkbutton, filedialog, messagebox, ttk
from PIL import Image

from Evaluators import Evaluators
from ManagePreferences import Preferences

# Variable global para almacenar la ruta de la carpeta de imágenes
ruta_imagenes = None
label_advertencia = None

def actualizar_contador(label_contador, label_carpeta_actual):
    global ruta_imagenes, label_advertencia

    if not ruta_imagenes or not os.path.exists(ruta_imagenes):
        label_contador.config(text="Imágenes cargadas: 0")
        label_carpeta_actual.config(text="Carpeta actual: Ninguna")
        label_advertencia.config(text="Antes de continuar asegúrate que desde la carpeta\nseleccionada puedas ver la carpeta 'input'")
        return

    # Contar las imágenes en la carpeta
    formatos_imagen = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"]
    lista_archivos = [archivo for archivo in os.listdir(ruta_imagenes) if any(archivo.lower().endswith(formato) for formato in formatos_imagen)]

    # Actualizar el contador de imágenes
    label_contador.config(text=f"Imágenes cargadas: {len(lista_archivos)}")
    label_carpeta_actual.config(text=f"Carpeta actual: {ruta_imagenes}")

    # Verificar si la carpeta 'input' existe
    ruta_input = os.path.join(ruta_imagenes, "input")
    if os.path.exists(ruta_input) and os.path.isdir(ruta_input):
        label_advertencia.config(text="Carpeta 'input' encontrada", fg="green")
    else:
        label_advertencia.config(text="Antes de continuar asegúrate que desde la carpeta\nseleccionada puedas ver la carpeta 'input'", fg="red")

def probar_entorno_conda(nombre_entorno, btn_probar):

    try:

        # Deshabilitar el botón para evitar múltiples clics
        ventana.after(0, btn_probar.config, {"state": "disabled"})

        # Comando para activar el entorno y ejecutar un comando de prueba
        comando = f'conda run -n {nombre_entorno} python -c "print(\'¡Entorno {nombre_entorno} cargado correctamente!\')"'

        # Ejecutar el comando en la terminal
        proceso = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        salida, errores = proceso.communicate()

        # Mostrar la salida y los errores en la interfaz
        if salida:
            ventana.after(0, messagebox.showinfo, "Salida", salida.decode("utf-8"))
        if errores:
            ventana.after(0, messagebox.showerror, "Errores", errores.decode("utf-8"))
    except Exception as e:
        ventana.after(0, messagebox.showerror, "Error", f"No se pudo ejecutar el comando: {e}")
    finally:
        # Rehabilitar el botón al finalizar, ya sea con éxito o con error
        ventana.after(0, btn_probar.config, {"state": "normal"})

def seleccionar_carpeta(label_contador, entry_framerate, label_carpeta_actual):

    global ruta_imagenes, label_advertencia

    # Pedir al usuario que seleccione una carpeta
    carpeta = filedialog.askdirectory()
    if not carpeta: 
        return

    # Limpiar el campo de framerate al cargar una carpeta
    entry_framerate.delete(0, "end")

    # Actualizar la ruta de la carpeta de imágenes
    ruta_imagenes = carpeta

    # Actualizar el contador y la carpeta actual
    actualizar_contador(label_contador, label_carpeta_actual)

def seleccionar_carpeta_herramienta(entry_widget):

    carpeta_seleccionada = filedialog.askdirectory() 
    if carpeta_seleccionada: 
        entry_widget.delete(0, "end") 
        entry_widget.insert(0, carpeta_seleccionada)

def cargar_video(label_contador, progressbar, entry_framerate, label_carpeta_actual):

    global ruta_imagenes

    # Pedir al usuario que seleccione un video
    ruta_video = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mkv")])
    if not ruta_video: 
        return

    # Ejecutar la extracción de frames en un hilo separado
    threading.Thread(
        target=extraer_frames,
        args=(ruta_video, label_contador, progressbar, entry_framerate, label_carpeta_actual),
        # El hilo se detendrá cuando se cierre la aplicación
        daemon=True 
    ).start()

def extraer_frames(ruta_video, label_contador, progressbar, entry_framerate, label_carpeta_actual):

    global ruta_imagenes, label_advertencia

    try:
        # Crear una carpeta para guardar los frames
        carpeta_frames = os.path.join(os.path.dirname(ruta_video), "input")
        os.makedirs(carpeta_frames, exist_ok=True)

        # Extraer todos los frames del video
        cap = cv2.VideoCapture(ruta_video)
        # Obtener los FPS del video
        fps_video = int(cap.get(cv2.CAP_PROP_FPS))

        # Mostrar el framerate en el campo de texto
        ventana.after(0, entry_framerate.delete, 0, "end")
        ventana.after(0, entry_framerate.insert, 0, str(fps_video))

        # Obtener la orientación del video (si está disponible en los metadatos)
        rotation_code = obtener_rotacion_video(ruta_video)

        frame_count = 0
        saved_count = 0

        # Total de frames en el video
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Rotar el frame si es necesario
            if rotation_code is not None:
                frame = rotar_frame(frame, rotation_code)

            # Guardar el frame
            ruta_frame = os.path.join(carpeta_frames, f"frame_{saved_count:04d}.jpg")
            cv2.imwrite(ruta_frame, frame)
            saved_count += 1

            # Actualizar la barra de progreso
            progreso = (frame_count + 1) / total_frames * 100
            ventana.after(0, actualizar_progreso, progressbar, progreso)
            frame_count += 1

        cap.release()
        ventana.after(0, messagebox.showinfo, "Éxito", f"Se extrajeron {saved_count} frames en {carpeta_frames}")

        # Actualizar la ruta de la carpeta de imágenes
        ruta_imagenes = carpeta_frames

        # Actualizar el contador y la carpeta actual
        ventana.after(0, actualizar_contador, label_contador, label_carpeta_actual, label_advertencia)
    except Exception as e:
        ventana.after(0, messagebox.showerror, "Error", f"No se pudo extraer los frames: {e}")

def actualizar_progreso(progressbar, valor):

    progressbar["value"] = valor
    ventana.update_idletasks()

def obtener_rotacion_video(ruta_video):

    try:
        import ffmpeg 

        # Obtener los metadatos del video
        metadata = ffmpeg.probe(ruta_video)

        # Buscar la etiqueta de rotación en los metadatos
        for stream in metadata.get("streams", []):
            if stream.get("codec_type") == "video":
                rotation = stream.get("tags", {}).get("rotate")
                if rotation:
                    return int(rotation)
        return None
    except Exception:
        return None

def rotar_frame(frame, rotation_code):

    if rotation_code == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    elif rotation_code == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    elif rotation_code == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    else:
        return frame

def extraer_mejores_tomas(entry_n, label_contador, entry_framerate, label_carpeta_actual, progressbar, btn_extraer):

    global ruta_imagenes

    if not ruta_imagenes:
        ventana.after(0, messagebox.showwarning, "Atención", "No hay imágenes cargadas.")
        return

    # Deshabilitar el botón para evitar múltiples clics
    ventana.after(0, btn_extraer.config, {"state": "disabled"})

    # Obtener el número de mejores imágenes por segundo
    try:
        n = int(entry_n.get())
        if n <= 0:
            ventana.after(0, messagebox.showerror, "Error", "El número de imágenes por segundo debe ser mayor que 0.")
            # Rehabilitar el botón en caso de error
            ventana.after(0, btn_extraer.config, {"state": "normal"}) 
            return
    except ValueError:
        ventana.after(0, messagebox.showerror, "Error", "El valor ingresado no es válido.")
        # Rehabilitar el botón en caso de error
        ventana.after(0, btn_extraer.config, {"state": "normal"})
        return

    # Obtener los FPS del video desde el campo de texto
    try:
        fps_video = int(entry_framerate.get()) if entry_framerate.get() else 30
    except ValueError:
        ventana.after(0, messagebox.showerror, "Error", "El framerate ingresado no es válido.")
        # Rehabilitar el botón en caso de error
        ventana.after(0, btn_extraer.config, {"state": "normal"})
        return

    # Ejecutar la extracción de mejores tomas en un hilo separado
    threading.Thread(
        target=procesar_mejores_tomas,
        args=(n, fps_video, label_contador, label_carpeta_actual, progressbar, btn_extraer),
        # Rehabilitar el botón en caso de error
        daemon=True 
    ).start()

def procesar_mejores_tomas(n, fps_video, label_contador, label_carpeta_actual, progressbar, btn_extraer):

    global ruta_imagenes, label_advertencia

    try:
        # Cargar las imágenes desde la carpeta
        formatos_imagen = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"]
        lista_archivos = [archivo for archivo in os.listdir(ruta_imagenes) if any(archivo.lower().endswith(formato) for formato in formatos_imagen)]
        rutas_imagenes = [os.path.join(ruta_imagenes, archivo) for archivo in lista_archivos]

        # Evaluar las imágenes y obtener sus scores
        evaluador = Evaluators([(ruta, Image.open(ruta).convert("RGB")) for ruta in rutas_imagenes])
        scores = evaluador.evalTenengradSobel()

        # Ordenar las imágenes por segundo y seleccionar las mejores n por segundo
        imagenes_por_segundo = {}
        total_imagenes = len(rutas_imagenes)
        for i, (ruta, score) in enumerate(zip(rutas_imagenes, scores)):
            segundo = i // fps_video
            if segundo not in imagenes_por_segundo:
                imagenes_por_segundo[segundo] = []
            imagenes_por_segundo[segundo].append((ruta, score))

            # Actualizar la barra de progreso
            progreso = (i + 1) / total_imagenes * 100
            ventana.after(0, actualizar_progreso, progressbar, progreso)
             # Forzar la actualización de la interfaz
            ventana.update_idletasks() 

        # Conservar solo las mejores n imágenes por segundo
        nuevas_rutas = []
        for segundo, imagenes in imagenes_por_segundo.items():
            # Ordenar por score
            imagenes.sort(key=lambda x: x[1], reverse=True)  
            # Conservar las mejores n
            nuevas_rutas.extend([ruta for ruta, _ in imagenes[:n]])  

        # Crear una carpeta para guardar las mejores tomas
        carpeta_mejores_tomas = os.path.join(ruta_imagenes, "input")
        os.makedirs(carpeta_mejores_tomas, exist_ok=True)

        # Copiar las mejores imágenes a la nueva carpeta
        for ruta in nuevas_rutas:
            nombre_archivo = os.path.basename(ruta)
            shutil.copy(ruta, os.path.join(carpeta_mejores_tomas, nombre_archivo))

        # Actualizar la ruta de la carpeta de imágenes
        ruta_imagenes = carpeta_mejores_tomas

        # Actualizar el contador y la carpeta actual
        ventana.after(0, actualizar_contador, label_contador, label_carpeta_actual, label_advertencia)

        ventana.after(0, messagebox.showinfo, "Éxito", f"Se conservaron las mejores {n} imágenes por segundo en {carpeta_mejores_tomas}.")
    except Exception as e:
        ventana.after(0, messagebox.showerror, "Error", f"No se pudo filtrar las imágenes: {e}")
    finally:
        # Rehabilitar el botón al finalizar, ya sea con éxito o con error
        ventana.after(0, btn_extraer.config, {"state": "normal"})

def ejecutar_colmap(ruta_imagenes, entry_entorno, entry_ruta_herramienta, chkbtn_resize, botones, btn_colmap):
    
    # Verificar si se ha seleccionado una carpeta
    if not ruta_imagenes:
        messagebox.showerror("Error", "No se ha seleccionado una carpeta.")
        return

    # Verificar si la carpeta seleccionada existe
    if not os.path.exists(ruta_imagenes):
        messagebox.showerror("Error", f"La carpeta seleccionada no existe: {ruta_imagenes}")
        return

    # Verificar si existe una carpeta 'input' dentro de la carpeta seleccionada
    ruta_input = os.path.join(ruta_imagenes, "input")
    if not os.path.exists(ruta_input) or not os.path.isdir(ruta_input):
        messagebox.showerror("Error", f"No se encontró la carpeta 'input' en: {ruta_imagenes}")
        return

    # Deshabilitar todos los botones
    for boton in botones:
        ventana.after(0, boton.config, {"state": "disabled"})
    ventana.after(0, btn_colmap.config, {"state": "disabled"})

    try:
        # Obtener los valores de los campos de entrada
        env_name = entry_entorno.get()
        ruta_herramienta = entry_ruta_herramienta.get()

        # Construir el comando
        comando = f'conda run -n {env_name} py {ruta_herramienta}/convert.py -s {ruta_imagenes}'
        if chkbtn_resize.get():
            comando += " --resize"

        # Ejecutar el comando de COLMAP
        print("Ejecutando COLMAP...")  # Mensaje de depuración
        proceso = subprocess.run(comando, shell=True, capture_output=True, text=True)

        # Mostrar la salida y los errores
        if proceso.stdout:
            print("Salida de COLMAP:", proceso.stdout)  # Mostrar en la consola
        if proceso.stderr:
            print("Errores de COLMAP:", proceso.stderr)  # Mostrar en la consola

        # Mostrar un mensaje de éxito
        messagebox.showinfo("Éxito", "Proceso de COLMAP completado.")
    except Exception as e:
        # Mostrar un mensaje de error
        messagebox.showerror("Error", f"No se pudo ejecutar el comando: {e}")
    finally:
        # Rehabilitar todos los botones
        for boton in botones:
            ventana.after(0, boton.config, {"state": "normal"})
        ventana.after(0, btn_colmap.config, {"state": "normal"})

def habilitar_botones(botones, btn_colmap):
    print("Rehabilitando botones...") 
    for boton in botones:
        ventana.after(0, boton.config, {"state": "normal"})
    ventana.after(0, btn_colmap.config, {"state": "normal"})
    

def main():
    
    global ventana, btn_carpeta, btn_video, btn_extraer, btn_probar, btn_colmap, btn_seleccionar_carpeta
    global label_advertencia

    preferences = Preferences()

    preferences.load()

    print("Inicializando interfaz gráfica...")

    ventana = Tk()
    ventana.title("Visualizador de Imágenes")
    ventana.geometry("600x600") 
    ventana.configure(bg="#1E1E1E") 

    frame_botones = Frame(ventana, bg="#1E1E1E")
    frame_botones.place(relx=0.5, rely=0.5, anchor="center")

    # Declaramos label de advertencia, pero aun no lo metemos
    label_advertencia = Label(frame_botones, text="Antes de continuar asegúrate que desde la carpeta\nseleccionada puedas ver la carpeta 'input'", 
          font=("Arial", 12), fg="red", bg="#1E1E1E")

    # Label para mostrar la carpeta actual
    label_carpeta_actual = Label(frame_botones, text="Carpeta actual: Ninguna", font=("Arial", 12), fg="white", bg="#1E1E1E")
    label_carpeta_actual.pack(pady=5)

    # Barra de progreso
    progressbar = ttk.Progressbar(frame_botones, orient="horizontal", length=300, mode="determinate")
    progressbar.pack(pady=10)

    # Label contador de imágenes
    label_contador = Label(frame_botones, text="Imágenes cargadas: 0", font=("Arial", 12), fg="white", bg="#1E1E1E")
    label_contador.pack(pady=5)

    # Frame para los botones de carga
    frame_carga = Frame(frame_botones, bg="#1E1E1E")
    frame_carga.pack(pady=10)

    # Botón para cargar carpeta
    btn_carpeta = Button(frame_carga, text="📁 Cargar Carpeta", width=20, height=2, fg="white", bg="#3A3A3A", relief="flat",
                     activebackground="#505050", font=("Arial", 12, "bold"),
                     command=lambda: seleccionar_carpeta(label_contador, entry_framerate, label_carpeta_actual))
    btn_carpeta.pack(side="left", padx=10)

    # Botón para cargar video
    btn_video = Button(frame_carga, text="🎥 Cargar Video", width=20, height=2, fg="white", bg="#3A3A3A", relief="flat",
                   activebackground="#505050", font=("Arial", 12, "bold"),
                   command=lambda: cargar_video(label_contador, progressbar, entry_framerate, label_carpeta_actual))
    btn_video.pack(side="left", padx=10)

    # Frame para los campos de texto y el botón de extraer mejores tomas
    frame_opciones = Frame(frame_botones, bg="#1E1E1E")
    frame_opciones.pack(pady=10)

    # Texto y campo de texto para "Elegir las mejores _____ tomas cada _____ imágenes"
    Label(frame_opciones, text="Elegir las mejores", font=("Arial", 12), fg="white", bg="#1E1E1E").pack(side="left", padx=5)
    entry_n = Entry(frame_opciones, font=("Arial", 12), bg="#3A3A3A", fg="white", insertbackground="white", width=5)
    entry_n.pack(side="left", padx=5)
    entry_n.insert(0, "5")

    Label(frame_opciones, text="tomas cada", font=("Arial", 12), fg="white", bg="#1E1E1E").pack(side="left", padx=5)
    entry_framerate = Entry(frame_opciones, font=("Arial", 12), bg="#3A3A3A", fg="white", insertbackground="white", width=5)
    entry_framerate.pack(side="left", padx=5)
    entry_framerate.insert(0, "30")

    Label(frame_opciones, text="imágenes", font=("Arial", 12), fg="white", bg="#1E1E1E").pack(side="left", padx=5)

    # Botón para extraer mejores tomas (más largo y grande)
    btn_extraer = Button(frame_botones, text="⭐ Extraer Mejores Tomas ⭐", width=30, height=2, fg="white", bg="#3A3A3A", relief="flat",
                     activebackground="#505050", font=("Arial", 14, "bold"),
                     command=lambda: extraer_mejores_tomas(entry_n, label_contador, entry_framerate, label_carpeta_actual, progressbar, btn_extraer))
    btn_extraer.pack(pady=20)

    # Frame para el campo de texto y el botón de prueba del entorno
    frame_prueba = Frame(frame_botones, bg="#1E1E1E")
    frame_prueba.pack(pady=10)

    # Campo de texto para el nombre del entorno
    Label(frame_prueba, text="Nombre del entorno (conda):", font=("Arial", 12), fg="white", bg="#1E1E1E").pack(side="left", padx=5)
    entry_entorno = Entry(frame_prueba, font=("Arial", 12), bg="#3A3A3A", fg="white", insertbackground="white", width=20)
    entry_entorno.pack(side="left", padx=5)
    entry_entorno.insert(0, preferences.preferences["environment_name"]) 

    # Botón para probar el entorno
    btn_probar = Button(frame_prueba, text="Probar Entorno", width=15, height=1, fg="white", bg="#3A3A3A", relief="flat",
                     activebackground="#505050", font=("Arial", 12, "bold"),
                     command=lambda: threading.Thread(target=probar_entorno_conda, args=(entry_entorno.get(),btn_probar), daemon=True).start())
    btn_probar.pack(side="left", padx=5)

    # Frame para la ruta de la herramienta
    frame_ruta_herramienta = Frame(frame_botones, bg="#1E1E1E")
    frame_ruta_herramienta.pack(pady=10)

    # Label y campo de texto para la ruta de la herramienta
    Label(frame_ruta_herramienta, text="Ruta de la herramienta:", font=("Arial", 12), fg="white", bg="#1E1E1E").pack(side="left", padx=5)
    entry_ruta_herramienta = Entry(frame_ruta_herramienta, font=("Arial", 12), bg="#3A3A3A", fg="white", insertbackground="white", width=30)
    entry_ruta_herramienta.pack(side="left", padx=5)
    entry_ruta_herramienta.insert(0, preferences.preferences["path_tool"])

    # Botón para seleccionar carpeta
    btn_seleccionar_carpeta = Button(frame_ruta_herramienta, text="📁", font=("Arial", 18), fg="white", bg="#3A3A3A", relief="flat",
                                     activebackground="#505050", command=lambda: seleccionar_carpeta_herramienta(entry_ruta_herramienta))
    btn_seleccionar_carpeta.pack(side="left", padx=5)

    # Label en rojo para advertencia
    label_advertencia.pack(pady=10)

    # Frame para el Checkbutton y el botón de COLMAP
    frame_colmap = Frame(frame_botones, bg="#1E1E1E")
    frame_colmap.pack(pady=10)

    # Variable para el estado del Checkbutton
    chkbtn_resize = BooleanVar(value=False)  # Por defecto, no está activo

    # Checkbutton para reescalar
    check_reescalar = Checkbutton(frame_colmap, text="Reescalar (1/2, 1/4 y 1/8)", font=("Arial", 14), 
                                  fg="white", bg="#1E1E1E", selectcolor="#3A3A3A", variable=chkbtn_resize)
    check_reescalar.pack(side="left", padx=5)

    # Lista de botones que se deshabilitarán durante la ejecución de COLMAP
    botones = [btn_carpeta, btn_video, btn_extraer, btn_probar, btn_seleccionar_carpeta]

    # Botón para ejecutar COLMAP
    btn_colmap = Button(frame_colmap, text="📐COLMAP (convert)", font=("Arial", 14), fg="white", bg="#3A3A3A", relief="flat",
                        activebackground="#505050", command=lambda: ejecutar_colmap(ruta_imagenes, entry_entorno, entry_ruta_herramienta, chkbtn_resize, botones, btn_colmap))
    btn_colmap.pack(side="left", padx=5)

    # Guardar preferencias al cerrar la ventana
    ventana.protocol("WM_DELETE_WINDOW", lambda: [
        preferences.update(
            environment_name=entry_entorno.get(),
            path_tool=entry_ruta_herramienta.get()
        ),
        preferences.save(), 
        ventana.destroy() 
    ])

    ventana.mainloop()

if __name__ == "__main__":
    main()