import cv2
import numpy as np
from dom import DOM
from tkinter import messagebox

class Evaluators:
    def __init__(self, imagenes_cargadas):
        self.imagenes_cargadas = imagenes_cargadas

    def evalDOM(self):
        if not self.imagenes_cargadas:
            messagebox.showwarning("Atención", "No hay imágenes cargadas.")
            return []

        domEval = DOM()
        scores = [domEval.get_sharpness(cv2.imread(ruta)) for ruta, _ in self.imagenes_cargadas]
        return scores

    def evalTenengrad(self):
        if not self.imagenes_cargadas:
            messagebox.showwarning("Atención", "No hay imágenes cargadas.")
            return []

        scores = []
        for ruta, _ in self.imagenes_cargadas:
            img = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
            if img is None:
                print(f"Error al leer la imagen {ruta}")
                scores.append(None)
                continue

            sobel_x = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
            tenengrad = np.sum(sobel_x**2 + sobel_y**2) / (img.shape[0] * img.shape[1])

            scores.append(tenengrad)
        return scores

    def evalSobel(self):
        if not self.imagenes_cargadas:
            messagebox.showwarning("Atención", "No hay imágenes cargadas.")
            return []

        scores = []
        for ruta, _ in self.imagenes_cargadas:
            img = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
            if img is None:
                print(f"Error al leer la imagen {ruta}")
                scores.append(None)
                continue

            sobel_x = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
            sobel_combined = np.sum(cv2.magnitude(sobel_x, sobel_y)**2) / (img.shape[0] * img.shape[1])

            scores.append(sobel_combined)
        return scores

    def evalTenengradSobel(self):
        if not self.imagenes_cargadas:
            messagebox.showwarning("Atención", "No hay imágenes cargadas.")
            return []

        scores = []
        for ruta, _ in self.imagenes_cargadas:
            img = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
            if img is None:
                print(f"Error al leer la imagen {ruta}")
                scores.append(None)
                continue

            # Calcular gradientes
            sobel_x = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)

            # Tenengrad: Promedio de la suma de los gradientes al cuadrado
            tenengrad = np.sum(sobel_x**2 + sobel_y**2) / (img.shape[0] * img.shape[1])

            # Sobel: Magnitud del gradiente normalizada
            sobel_combined = np.sum(cv2.magnitude(sobel_x, sobel_y)**2) / (img.shape[0] * img.shape[1])

            # Combinar ambos puntajes (puedes ajustar la ponderación si es necesario)
            score = tenengrad + sobel_combined
            scores.append(score)

        return scores
