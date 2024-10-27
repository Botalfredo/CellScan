import cv2
from PIL import Image
import numpy as np
import csv
import os


class ImageProcessor:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        # Vérifier si l'image est chargée correctement
        if self.image is None:
            raise FileNotFoundError(f"Image not found or cannot be loaded: {image_path}")

    def process(self, params):
        # Appliquer CLAHE
        clahe = cv2.createCLAHE(clipLimit=params['clahe_clip'],
                                tileGridSize=(params['clahe_grid'], params['clahe_grid']))
        image_clahe = clahe.apply(self.image)

        # Appliquer le contraste et gamma
        enhanced_image = cv2.convertScaleAbs(image_clahe, alpha=params['contrast'], beta=0)
        enhanced_image = self.adjust_gamma(enhanced_image, gamma=params['gamma'])

        # Appliquer le flou Gaussien
        gaussian_kernel = max(1, params['gaussian_kernel'] * 2 + 1)
        blurred_image = cv2.GaussianBlur(enhanced_image, (gaussian_kernel, gaussian_kernel), 0)

        # Appliquer le seuil et les opérations morphologiques pour obtenir l'image binaire
        _, binary_image = cv2.threshold(blurred_image, params['threshold'], 255, cv2.THRESH_BINARY_INV)
        kernel = np.ones((params['kernel_size'], params['kernel_size']), np.uint8)
        opening = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel)

        # Compter les contours pour déterminer le nombre de cellules
        contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cell_count = len(contours)

        # Dessiner les contours sur l'image traitée pour l'image des contours
        contours_image = cv2.cvtColor(blurred_image, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(contours_image, contours, -1, (0, 255, 0), 2)

        # Convertir les images en format PIL pour l'affichage
        processed_pil = Image.fromarray(cv2.cvtColor(blurred_image, cv2.COLOR_GRAY2RGB))
        binary_pil = Image.fromarray(cv2.cvtColor(opening, cv2.COLOR_GRAY2RGB))
        contours_pil = Image.fromarray(contours_image)

        # Enregistrer les aires des cellules en CSV
        self.save_cell_areas_to_csv(contours, params.get("csv_path"))

        return processed_pil, binary_pil, contours_pil, cell_count

    def save_cell_areas_to_csv(self, contours, csv_path=None):
        """Enregistre le nombre de pixels de chaque cellule détectée dans un fichier CSV."""
        # Utiliser un nom de fichier par défaut si aucun chemin n'est spécifié
        if not csv_path:
            csv_path = os.path.splitext(self.image_path)[0] + "_cell_areas.csv"

        # Calculer l'aire de chaque contour (cellule)
        cell_areas = [cv2.contourArea(contour) for contour in contours]

        # Écrire les aires des cellules dans un fichier CSV
        with open(csv_path, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Cell ID", "Pixel Count"])  # En-tête du CSV
            for i, area in enumerate(cell_areas, start=1):
                writer.writerow([i, int(area)])  # ID de la cellule et aire en pixels

        print(f"Cell areas saved to {csv_path}")

    @staticmethod
    def adjust_gamma(image, gamma=1.0):
        invGamma = 1.0 / gamma
        table = np.array([(i / 255.0) ** invGamma * 255 for i in range(256)]).astype("uint8")
        return cv2.LUT(image, table)
