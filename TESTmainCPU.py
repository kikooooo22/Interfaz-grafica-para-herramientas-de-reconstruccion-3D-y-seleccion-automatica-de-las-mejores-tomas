import os
import threading
import cv2
import evaluators
import shutil 
from tkinter import ttk,Tk, Button, Frame, Label, filedialog, messagebox, Entry
from PIL import Image

# Lista para guardar imágenes y sus rutas
imagenes_guardadas = []

def seleccionar_carpeta(carpeta, label_contador, progressbar, entry_framerate):
    global imagenes_guardadas
    imagenes_guardadas = []

    # Limpiar el campo de framerate al cargar una carpeta
    entry_framerate.delete(0, "end")

    formatos_imagen = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"]
    lista_archivos = [archivo for archivo in os.listdir(carpeta) if any(archivo.lower().endswith(formato) for formato in formatos_imagen)]

    total_imagenes = len(lista_archivos)

    def cargar_imagenes():
        for i, archivo in enumerate(lista_archivos):
            ruta_imagen = os.path.join(carpeta, archivo)
            try:
                # Cargar y redimensionar la imagen
                imagen = Image.open(ruta_imagen).convert("RGB")
                imagen.thumbnail((150, 150))  # Redimensionar para ahorrar memoria

                # Guardar la imagen redimensionada en la lista
                imagenes_guardadas.append((ruta_imagen, imagen))

                # Actualizar la barra de progreso y el contador
                progreso = (i + 1) / total_imagenes * 100
                ventana.after(0, actualizar_interfaz, progressbar, progreso, label_contador, len(imagenes_guardadas))
            except Exception as e:
                print(f"No se pudo abrir la imagen {archivo}: {e}")
                ventana.after(0, messagebox.showerror, "Error", f"No se pudo abrir la imagen {archivo}: {e}")

    # Ejecutar el proceso de carga en un hilo separado
    threading.Thread(target=cargar_imagenes).start()

def actualizar_interfaz(progressbar, valor, label_contador, contador_imagenes):
    # Actualizar la barra de progreso
    progressbar["value"] = valor
    # Actualizar el contador de imágenes
    label_contador.config(text=f"Imágenes cargadas: {contador_imagenes}")
    ventana.update_idletasks()

def evaluar_imagenes():
    if not imagenes_guardadas:
        messagebox.showwarning("Atención", "No hay imágenes cargadas.")
        return

    evaluador = evaluators.Evaluators(imagenes_guardadas)
    scores = evaluador.evalTenengradSobel()

    for (ruta, _), score in zip(imagenes_guardadas, scores):
        print(f"Calidad Tenengrad+Sobel para {os.path.basename(ruta)}: {score}")

def cargar_video(label_contador, progressbar, entry_framerate):
    ruta_video = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mkv")])
    if ruta_video:
        try:
            # Crear una carpeta para guardar los frames
            carpeta_frames = os.path.join(os.path.dirname(ruta_video), "frames")
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

                frame_count += 1

            cap.release()
            messagebox.showinfo("Éxito", f"Se extrajeron {saved_count} frames en {carpeta_frames}")

            # Cargar los frames en la interfaz
            seleccionar_carpeta(carpeta_frames, label_contador, progressbar, entry_framerate)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo extraer los frames: {e}")

def obtener_rotacion_video(ruta_video):
    """
    Obtiene el código de rotación del video a partir de sus metadatos.
    """
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

def extraer_mejores_tomas(entry_n, label_contador, progressbar, entry_framerate):
    try:
        n = int(entry_n.get())  # Obtener el número de mejores imágenes por segundo
        if n <= 0:
            messagebox.showerror("Error", "El número de imágenes por segundo debe ser mayor que 0.")
            return

        # Obtener los FPS del video desde el campo de texto
        fps_video = int(entry_framerate.get()) if entry_framerate.get() else 30  # Valor predeterminado si no se especifica

        # Evaluar las imágenes y obtener sus scores
        evaluador = evaluators.Evaluators(imagenes_guardadas)
        scores = evaluador.evalTenengradSobel()

        # Combinar las imágenes con sus scores
        imagenes_con_scores = list(zip(imagenes_guardadas, scores))

        # Ordenar las imágenes por segundo y seleccionar las mejores n por segundo
        imagenes_por_segundo = {}
        for i, ((ruta, imagen), score) in enumerate(imagenes_con_scores):  # Desempaquetar correctamente
            segundo = i // fps_video
            if segundo not in imagenes_por_segundo:
                imagenes_por_segundo[segundo] = []
            imagenes_por_segundo[segundo].append((ruta, imagen, score))  # Agregar la tupla correcta

        # Conservar solo las mejores n imágenes por segundo
        nuevas_imagenes = []
        for segundo, imagenes in imagenes_por_segundo.items():
            imagenes.sort(key=lambda x: x[2], reverse=True)  # Ordenar por score
            nuevas_imagenes.extend(imagenes[:n])  # Conservar las mejores n

        # Crear una carpeta para guardar las mejores tomas
        carpeta_mejores_tomas = os.path.join(os.path.dirname(imagenes_guardadas[0][0]), "mejores_tomas")
        os.makedirs(carpeta_mejores_tomas, exist_ok=True)

        # Copiar las mejores imágenes a la nueva carpeta y actualizar la lista
        nuevas_rutas_imagenes = []
        for ruta, imagen, _ in nuevas_imagenes:
            nombre_archivo = os.path.basename(ruta)
            nueva_ruta = os.path.join(carpeta_mejores_tomas, nombre_archivo)
            shutil.copy(ruta, nueva_ruta)  # Copiar la imagen a la nueva carpeta
            nuevas_rutas_imagenes.append((nueva_ruta, imagen))  # Actualizar la lista con las nuevas rutas

        # Actualizar la lista de imágenes cargadas
        imagenes_guardadas[:] = nuevas_rutas_imagenes

        # Actualizar la interfaz
        label_contador.config(text=f"Imágenes cargadas: {len(imagenes_guardadas)}")
        progressbar["value"] = 100  # Completar la barra de progreso
        ventana.update_idletasks()

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
                     command=lambda: seleccionar_carpeta(filedialog.askdirectory(), label_contador, progressbar, entry_framerate))
    btn_carpeta.pack(side="left", padx=10)

    # Botón para cargar video
    btn_video = Button(frame_carga, text="🎥 Cargar Video", width=20, height=2, fg="white", bg="#3A3A3A", relief="flat",
                   activebackground="#505050", font=("Arial", 12, "bold"),
                   command=lambda: cargar_video(label_contador, progressbar, entry_framerate))
    btn_video.pack(side="left", padx=10)

    # Campo de texto para mejores imágenes por segundo
    Label(frame_botones, text="Mejores imágenes por segundo:", font=("Arial", 14), fg="white", bg="#1E1E1E").pack(pady=5)
    entry_n = Entry(frame_botones, font=("Arial", 14), bg="#3A3A3A", fg="white", insertbackground="white", width=10)
    entry_n.pack(pady=5)
    entry_n.insert(0, "5")

    # Campo de texto para el framerate
    Label(frame_botones, text="Framerate del video:", font=("Arial", 14), fg="white", bg="#1E1E1E").pack(pady=5)
    entry_framerate = Entry(frame_botones, font=("Arial", 14), bg="#3A3A3A", fg="white", insertbackground="white", width=10)
    entry_framerate.pack(pady=5)

    # Botón para extraer mejores tomas (más largo y grande)
    btn_extraer = Button(frame_botones, text="⭐ Extraer Mejores Tomas ⭐", width=30, height=2, fg="white", bg="#3A3A3A", relief="flat",
                     activebackground="#505050", font=("Arial", 14, "bold"),
                     command=lambda: extraer_mejores_tomas(entry_n, label_contador, progressbar, entry_framerate))
    btn_extraer.pack(pady=20)

    ventana.mainloop()

if __name__ == "__main__":
    main()