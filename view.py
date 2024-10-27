import tkinter as tk
from tkinter import ttk, filedialog
from processing import ImageProcessor
from PIL import Image, ImageTk
from tkinter import messagebox

class CellCounterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CellScan")
        self.root.geometry("1350x700")

        # Initialisation du traitement d'image avec un fichier par défaut
        self.processor = ImageProcessor("image.png")

        # Variables pour le traitement
        self.contrast = tk.IntVar(value=1)
        self.gamma = tk.DoubleVar(value=1.0)
        self.clahe_clip = tk.DoubleVar(value=1.0)
        self.clahe_grid = tk.IntVar(value=8)
        self.gaussian_kernel = tk.IntVar(value=1)
        self.threshold = tk.IntVar(value=128)
        self.kernel_size = tk.IntVar(value=3)
        self.csv_file_path = None  # Variable pour stocker le chemin du fichier CSV

        # Configuration de l'interface
        self.create_widgets()

    def create_widgets(self):
        # Cadre supérieur pour les boutons de sélection de fichier
        top_frame = ttk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Bouton pour choisir le fichier image
        file_button = ttk.Button(top_frame, text="Choose an image file", command=self.select_image_file)
        file_button.pack(side=tk.LEFT)

        # Étiquette pour afficher le nom du fichier image sélectionné
        self.file_label = ttk.Label(top_frame, text="Current image file : " + self.shorten_path("image.png"))
        self.file_label.pack(side=tk.LEFT, padx=10)

        # Bouton pour choisir le fichier CSV de destination
        csv_button = ttk.Button(top_frame, text="Choose a CSV file", command=self.select_csv_file)
        csv_button.pack(side=tk.LEFT)

        # Étiquette pour afficher le nom du fichier CSV sélectionné
        self.csv_label = ttk.Label(top_frame, text="CSV file: Not specified (use current folder)")
        self.csv_label.pack(side=tk.LEFT, padx=10)

        # Cadre des curseurs et du nombre de cellules
        control_frame = ttk.Frame(self.root)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Curseurs de contrôle
        self.create_slider(control_frame, "Contrast", self.contrast, 1, 3)
        self.create_slider(control_frame, "Gamma", self.gamma, 0.1, 2.0, resolution=0.1)
        self.create_slider(control_frame, "CLAHE Clip Limit", self.clahe_clip, 0.1, 10.0, resolution=0.1)
        self.create_slider(control_frame, "CLAHE Grid Size", self.clahe_grid, 1, 50)
        self.create_slider(control_frame, "Gaussian Kernel", self.gaussian_kernel, 1, 20)
        self.create_slider(control_frame, "Threshold", self.threshold, 0, 255)
        self.create_slider(control_frame, "Kernel Size", self.kernel_size, 1, 20)

        # Étiquette pour afficher le nombre de cellules détectées en gras
        bold_font = ("TkDefaultFont", 10, "bold")
        self.cell_count_label = ttk.Label(control_frame, text="Cells Detected: 0", font=bold_font)
        self.cell_count_label.pack(pady=20)

        # Étiquette des crédits
        credits_label = ttk.Label(
            control_frame,
            text="CellScan - Developed by Alfred.\nAll rights not necessarily reserved\nAnd it's for my sister !\nV0.0.1",
            font=("TkDefaultFont", 8, "italic")
        )
        credits_label.pack(side=tk.RIGHT)

        # Cadre pour les images
        self.image_frame = ttk.Frame(self.root)
        self.image_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        # Sous-cadre pour l'image des contours à gauche
        self.contours_frame = ttk.Frame(self.image_frame)
        self.contours_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Sous-cadre pour les deux autres images empilées à droite
        self.processed_binary_frame = ttk.Frame(self.image_frame)
        self.processed_binary_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Création des labels pour les images
        self.contours_image_label = ttk.Label(self.contours_frame)
        self.contours_image_label.pack(expand=True, fill=tk.BOTH)

        self.processed_image_label = ttk.Label(self.processed_binary_frame)
        self.processed_image_label.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        self.binary_image_label = ttk.Label(self.processed_binary_frame)
        self.binary_image_label.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH)

        # Initialisation des images
        self.process_and_display_image()

        # Mettre à jour l'affichage à chaque changement de curseur
        self.root.bind("<Configure>", self.process_and_display_image)

    def select_image_file(self):
        """Ouvre une boîte de dialogue pour sélectionner un fichier image et met à jour l'affichage."""
        file_path = filedialog.askopenfilename(
            title="Sélectionnez une image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff")]
        )
        if file_path:
            try:
                self.processor = ImageProcessor(file_path)  # Recharger le processeur avec la nouvelle image
                self.file_label.config(
                    text=f"Fichier image actuel : {self.shorten_path(file_path)}")  # Mettre à jour le label du fichier
                self.process_and_display_image()  # Mettre à jour l'affichage avec la nouvelle image
            except FileNotFoundError as e:
                messagebox.showerror("Erreur de chargement", str(e))

    def select_csv_file(self):
        """Ouvre une boîte de dialogue pour sélectionner le fichier CSV de sortie."""
        self.csv_file_path = filedialog.asksaveasfilename(
            title="Save as",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if self.csv_file_path:
            self.csv_label.config(text=f"CSV file  : {self.shorten_path(self.csv_file_path)}")

    def shorten_path(self, path, max_length=30):
        """Raccourcit le chemin du fichier s'il dépasse max_length caractères."""
        if len(path) > max_length:
            return "..." + path[-(max_length - 3):]
        return path

    def create_slider(self, parent, label, variable, from_, to_, resolution=1):
        """Fonction utilitaire pour créer un curseur avec une étiquette."""
        ttk.Label(parent, text=label).pack()
        slider = ttk.Scale(parent, variable=variable, from_=from_, to=to_, orient="horizontal", length=200)
        slider.pack(pady=5)
        slider.bind("<Motion>", lambda event: self.process_and_display_image())

    def process_and_display_image(self, event=None):
        # Obtenir les paramètres des curseurs et traiter l'image
        params = {
            "contrast": self.contrast.get(),
            "gamma": self.gamma.get(),
            "clahe_clip": self.clahe_clip.get(),
            "clahe_grid": self.clahe_grid.get(),
            "gaussian_kernel": self.gaussian_kernel.get(),
            "threshold": self.threshold.get(),
            "kernel_size": self.kernel_size.get(),
            "csv_path": self.csv_file_path  # Passer le chemin du fichier CSV au traitement
        }

        # Effectuer le traitement et obtenir les images traitées et le nombre de cellules
        processed_image, binary_image, contours_image, cell_count = self.processor.process(params)

        # Mettre à jour l'affichage du nombre de cellules
        self.cell_count_label.config(text=f"Cells Detected: {cell_count}")

        # Obtenir la taille du cadre pour l'affichage des images
        contours_width = self.contours_frame.winfo_width()
        contours_height = self.contours_frame.winfo_height()

        processed_width = self.processed_binary_frame.winfo_width()
        processed_height = int(self.processed_binary_frame.winfo_height() / 2)  # Diviser en deux pour deux images

        # Vérifier que la largeur et la hauteur sont valides avant de redimensionner et afficher les images
        if contours_width > 0 and contours_height > 0:
            self.display_image(contours_image, self.contours_image_label, contours_width, contours_height)
        if processed_width > 0 and processed_height > 0:
            self.display_image(processed_image, self.processed_image_label, processed_width, processed_height)
            self.display_image(binary_image, self.binary_image_label, processed_width, processed_height)

    def display_image(self, image, label, max_width, max_height):
        """Redimensionne l'image pour qu'elle tienne dans max_width et max_height tout en conservant le ratio d'aspect."""
        original_width, original_height = image.size

        # Calculer le facteur d'échelle pour préserver le ratio d'aspect
        scale = min(max_width / original_width, max_height / original_height)
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        # Redimensionner l'image tout en conservant le ratio d'aspect
        resized_image = image.resize((new_width, new_height), Image.LANCZOS)

        # Convertir l'image redimensionnée en format Tkinter et l'afficher
        tk_image = ImageTk.PhotoImage(resized_image)
        label.config(image=tk_image)
        label.image = tk_image

    def run(self):
        self.root.mainloop()
