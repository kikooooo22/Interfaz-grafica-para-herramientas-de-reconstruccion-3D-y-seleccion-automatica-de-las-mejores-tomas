import os
import subprocess
import cv2
import evaluators
import shutil
from tkinter import ttk, Tk, Button, Frame, Label, filedialog, messagebox, Entry
from PIL import Image

# Variable global para almacenar la ruta de la carpeta de imágenes
ruta_imagenes = None

def actualizar_contador(label_contador, label_carpeta_actual):
    """
    Cuenta las imágenes en la carpeta actual y actualiza el contador en la interfaz.
    """
    global ruta_imagenes

    if not ruta_imagenes or not os.path.exists(ruta_imagenes):
        label_contador.config(text="Imágenes cargadas: 0")
        label_carpeta_actual.config(text="Carpeta actual: Ninguna")
        return

    # Contar las imágenes en la carpeta
    formatos_imagen = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"]
    lista_archivos = [archivo for archivo in os.listdir(ruta_imagenes) if any(archivo.lower().endswith(formato) for formato in formatos_imagen)]

    # Actualizar el contador de imágenes
    label_contador.config(text=f"Imágenes cargadas: {len(lista_archivos)}")
    label_carpeta_actual.config(text=f"Carpeta actual: {ruta_imagenes}")

def probar_entorno_conda(nombre_entorno):
    """
    Prueba si el entorno de Conda se carga correctamente.
    """
    try:

        # Comando para activar el entorno y ejecutar un comando de prueba
        comando = f'conda run -n {nombre_entorno} python -c "print(\'¡Entorno {nombre_entorno} cargado correctamente!\')"'

        # Ejecutar el comando en la terminal
        proceso = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        salida, errores = proceso.communicate()

        # Mostrar la salida y los errores en la interfaz
        if salida:
            messagebox.showinfo("Salida", salida.decode("utf-8"))
        if errores:
            messagebox.showerror("Errores", errores.decode("utf-8"))
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo ejecutar el comando: {e}")

def seleccionar_carpeta(label_contador, entry_framerate, label_carpeta_actual):
    global ruta_imagenes

    # Pedir al usuario que seleccione una carpeta
    carpeta = filedialog.askdirectory()
    if not carpeta:  # Si el usuario cancela, no hacer nada
        return

    # Limpiar el campo de framerate al cargar una carpeta
    entry_framerate.delete(0, "end")

    # Actualizar la ruta de la carpeta de imágenes
    ruta_imagenes = carpeta

    # Actualizar el contador y la carpeta actual
    actualizar_contador(label_contador, label_carpeta_actual)

def cargar_video(label_contador, progressbar, entry_framerate, label_carpeta_actual):
    global ruta_imagenes

    # Pedir al usuario que seleccione un video
    ruta_video = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mkv")])
    if not ruta_video:  # Si el usuario cancela, no hacer nada
        return

    try:
        # Crear una carpeta para guardar los frames
        carpeta_frames = os.path.join(os.path.dirname(ruta_video), "input")
        os.makedirs(carpeta_frames, exist_ok=True)

        # Extraer todos los frames del video
        cap = cv2.VideoCapture(ruta_video)
        fps_video = int(cap.get(cv2.CAP_PROP_FPS))  # Obtener los FPS del video

        # Mostrar el framerate en el campo de texto
        entry_framerate.delete(0, "end")
        entry_framerate.insert(0, str(fps_video))

        # Obtener la orientación del video (si está disponible en los metadatos)
        rotation_code = obtener_rotacion_video(ruta_video)

        frame_count = 0
        saved_count = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # Total de frames en el video

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
        messagebox.showinfo("Éxito", f"Se extrajeron {saved_count} frames en {carpeta_frames}")

        # Actualizar la ruta de la carpeta de imágenes
        ruta_imagenes = carpeta_frames

        # Actualizar el contador y la carpeta actual
        actualizar_contador(label_contador, label_carpeta_actual)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo extraer los frames: {e}")

def actualizar_progreso(progressbar, valor):
    progressbar["value"] = valor
    ventana.update_idletasks()

def obtener_rotacion_video(ruta_video):
    """
    Obtiene el código de rotación del video a partir de sus metadatos.
    """
    try:
        import ffmpeg  # Necesitas instalar ffmpeg-python: pip install ffmpeg-python

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
    """
    Rota el frame según el código de rotación.
    """
    if rotation_code == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    elif rotation_code == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    elif rotation_code == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    else:
        return frame

def extraer_mejores_tomas(entry_n, label_contador, entry_framerate, label_carpeta_actual):
    global ruta_imagenes

    if not ruta_imagenes:
        messagebox.showwarning("Atención", "No hay imágenes cargadas.")
        return

    try:
        n = int(entry_n.get())  # Obtener el número de mejores imágenes por segundo
        if n <= 0:
            messagebox.showerror("Error", "El número de imágenes por segundo debe ser mayor que 0.")
            return

        # Obtener los FPS del video desde el campo de texto
        fps_video = int(entry_framerate.get()) if entry_framerate.get() else 30  # Valor predeterminado si no se especifica

        # Cargar las imágenes desde la carpeta
        formatos_imagen = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"]
        lista_archivos = [archivo for archivo in os.listdir(ruta_imagenes) if any(archivo.lower().endswith(formato) for formato in formatos_imagen)]
        rutas_imagenes = [os.path.join(ruta_imagenes, archivo) for archivo in lista_archivos]

        # Evaluar las imágenes y obtener sus scores
        evaluador = evaluators.Evaluators([(ruta, Image.open(ruta).convert("RGB")) for ruta in rutas_imagenes])
        scores = evaluador.evalTenengradSobel()

        # Ordenar las imágenes por segundo y seleccionar las mejores n por segundo
        imagenes_por_segundo = {}
        for i, (ruta, score) in enumerate(zip(rutas_imagenes, scores)):
            segundo = i // fps_video
            if segundo not in imagenes_por_segundo:
                imagenes_por_segundo[segundo] = []
            imagenes_por_segundo[segundo].append((ruta, score))

        # Conservar solo las mejores n imágenes por segundo
        nuevas_rutas = []
        for segundo, imagenes in imagenes_por_segundo.items():
            imagenes.sort(key=lambda x: x[1], reverse=True)  # Ordenar por score
            nuevas_rutas.extend([ruta for ruta, _ in imagenes[:n]])  # Conservar las mejores n

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
        actualizar_contador(label_contador, label_carpeta_actual)

        messagebox.showinfo("Éxito", f"Se conservaron las mejores {n} imágenes por segundo en {carpeta_mejores_tomas}.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo filtrar las imágenes: {e}")

def main():
    global ventana
    print("Inicializando interfaz gráfica...")

    ventana = Tk()
    ventana.title("Visualizador de Imágenes")
    ventana.geometry("600x500")  # Ventana más grande
    ventana.configure(bg="#1E1E1E")  # Fondo oscuro

    frame_botones = Frame(ventana, bg="#1E1E1E")
    frame_botones.place(relx=0.5, rely=0.5, anchor="center")

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
                     command=lambda: extraer_mejores_tomas(entry_n, label_contador, entry_framerate, label_carpeta_actual))
    btn_extraer.pack(pady=20)

    # Frame para el campo de texto y el botón de prueba del entorno
    frame_prueba = Frame(frame_botones, bg="#1E1E1E")
    frame_prueba.pack(pady=10)

    # Campo de texto para el nombre del entorno
    Label(frame_prueba, text="Nombre del entorno:", font=("Arial", 12), fg="white", bg="#1E1E1E").pack(side="left", padx=5)
    entry_entorno = Entry(frame_prueba, font=("Arial", 12), bg="#3A3A3A", fg="white", insertbackground="white", width=20)
    entry_entorno.pack(side="left", padx=5)
    entry_entorno.insert(0, "gaussian_splatting_v2")  # Valor predeterminado

    # Botón para probar el entorno
    btn_probar = Button(frame_prueba, text="Probar Entorno", width=15, height=1, fg="white", bg="#3A3A3A", relief="flat",
                     activebackground="#505050", font=("Arial", 12, "bold"),
                     command=lambda: probar_entorno_conda(entry_entorno.get()))
    btn_probar.pack(side="left", padx=5)

    ventana.mainloop()

if __name__ == "__main__":
    main()