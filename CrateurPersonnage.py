#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Créateur de Personnages Articulés
VERSION RESPONSIVE - TOP BAR, SIDE BAR DÉFILANTE, FOND TRANSPARENT ET CHAMPS TEXTE POUR DIMENSIONS
"""

import sys
import subprocess
import json
import math
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox

# --- Installation des dépendances ---

def install_dependencies():
    """Installe tkinter (si manquant sur Linux) et Pillow."""
    try:
        import tkinter
    except ImportError:
        print("Installation de tkinter...")
        if sys.platform == "linux":
            subprocess.run(["sudo", "apt-get", "install", "-y", "python3-tk"])
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Installation de Pillow...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors de l'installation de Pillow: {e}")
            print("Veuillez installer Pillow manuellement: pip install Pillow")
            
install_dependencies()

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Erreur: Pillow n'est pas installé. L'application ne peut pas démarrer.")
    sys.exit(1)


# --- Classes de Données (Inchanggées) ---

class Joint:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Limb:
    def __init__(self, start_joint, mid_joint, end_joint, mid_length=35, end_length=35, width=28):
        self.start = start_joint
        self.mid = mid_joint
        self.end = end_joint
        self.width = width
        self.mid_length = mid_length
        self.end_length = end_length

class Character:
    def __init__(self, x=400, y=300, scale=1.0):
        self.x = x
        self.y = y
        self.scale = scale
        self.rotation = 0
        self.color = "#9370DB"
        self.outline_width = 6 
        self.selected_joint = None
        self.head_rotation = 0
        self.corner_radius = 45
        self.neck_gap_y = 15
        self.head_offset_y = 0
        self.global_outline = False
        
        # Dimensions de base
        self.head_radius = 50
        self.body_height = 90
        self.body_width = 65
        self.limb_width = 28 

        # Points centraux (relativement au char.x, char.y)
        self.neck = Joint(0, -self.head_radius - self.neck_gap_y)
        self.waist = Joint(0, self.body_height - self.head_radius - self.neck_gap_y)
        
        # Initialisation des membres avec des longueurs
        l_arm_len = 35
        l_forearm_len = 35
        l_leg_len = 45
        l_foot_len = 45
        
        # Bras Gauche
        self.left_shoulder = Joint(-self.body_width//2, 5)
        self.left_elbow = Joint(-self.body_width//2 - l_arm_len, 40)
        self.left_hand = Joint(-self.body_width//2 - l_arm_len, 40 + l_forearm_len)
        self.left_arm = Limb(self.left_shoulder, self.left_elbow, self.left_hand, l_arm_len, l_forearm_len, self.limb_width)
        
        # Bras Droit
        self.right_shoulder = Joint(self.body_width//2, 5)
        self.right_elbow = Joint(self.body_width//2 + l_arm_len, 40)
        self.right_hand = Joint(self.body_width//2 + l_arm_len, 40 + l_forearm_len)
        self.right_arm = Limb(self.right_shoulder, self.right_elbow, self.right_hand, l_arm_len, l_forearm_len, self.limb_width)
        
        # Jambe Gauche
        self.left_hip = Joint(-20, self.body_height - self.head_radius - self.neck_gap_y)
        self.left_knee = Joint(-20, self.body_height - self.head_radius - self.neck_gap_y + l_leg_len)
        self.left_foot = Joint(-20, self.body_height - self.head_radius - self.neck_gap_y + l_leg_len + l_foot_len)
        self.left_leg = Limb(self.left_hip, self.left_knee, self.left_foot, l_leg_len, l_foot_len, self.limb_width)
        
        # Jambe Droite
        self.right_hip = Joint(20, self.body_height - self.head_radius - self.neck_gap_y)
        self.right_knee = Joint(20, self.body_height - self.head_radius - self.neck_gap_y + l_leg_len)
        self.right_foot = Joint(20, self.body_height - self.head_radius - self.neck_gap_y + l_leg_len + l_foot_len)
        self.right_leg = Limb(self.right_hip, self.right_knee, self.right_foot, l_leg_len, l_foot_len, self.limb_width)
        
        self.limbs = [self.left_arm, self.right_arm, self.left_leg, self.right_leg]
        
    def get_world_pos(self, joint):
        angle = math.radians(self.rotation)
        sx = joint.x * self.scale
        sy = joint.y * self.scale
        rx = sx * math.cos(angle) - sy * math.sin(angle)
        ry = sx * math.sin(angle) + sy * math.cos(angle)
        return (self.x + rx, self.y + ry)
    
    def set_from_world_pos(self, joint, wx, wy):
        dx = wx - self.x
        dy = wy - self.y
        angle = math.radians(-self.rotation)
        rx = dx * math.cos(angle) - dy * math.sin(angle)
        ry = dx * math.sin(angle) + dy * math.cos(angle)
        joint.x = rx / self.scale
        joint.y = ry / self.scale

# --- Application Tkinter ---

class CharacterCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Créateur de Personnages Articulés")
        self.root.geometry("1400x900")
        
        self.characters = []
        self.selected_char = None
        self.dragging = False
        self.history = []
        self.history_index = -1
        
        self.canvas_width = 800
        self.canvas_height = 800
        self.background_mode = tk.StringVar(value="white") # 'white' or 'transparent'

        self.setup_ui()
        self.add_character()
        self.save_history() 
        
    def setup_ui(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # --- TOP BAR (Ligne 0) ---
        top_frame = ttk.Frame(self.root, padding="5 5 5 5", relief=tk.RAISED)
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        # Boutons d'action dans la Top Bar
        ttk.Button(top_frame, text="↶ Annuler", command=self.undo).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="💾 Sauvegarder Scène", command=self.save_scene).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="📂 Charger Scène", command=self.load_scene).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="🎨 Changer couleur", command=self.choose_color).pack(side=tk.LEFT, padx=15)
        
        # Contrôles de l'image dans la Top Bar
        export_frame = ttk.Frame(top_frame)
        export_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(export_frame, text="📸 Export PNG", command=lambda: self.export_image("png")).pack(side=tk.LEFT, padx=2)
        ttk.Button(export_frame, text="📸 Export JPEG", command=lambda: self.export_image("jpeg")).pack(side=tk.LEFT, padx=2)
        
        # Sélecteur de fond (Blanc/Transparent)
        bg_frame = ttk.Frame(top_frame)
        bg_frame.pack(side=tk.RIGHT, padx=15)
        ttk.Label(bg_frame, text="Fond:").pack(side=tk.LEFT)
        ttk.Radiobutton(bg_frame, text="Blanc", variable=self.background_mode, value="white", command=self.draw).pack(side=tk.LEFT)
        ttk.Radiobutton(bg_frame, text="Transp.", variable=self.background_mode, value="transparent", command=self.draw).pack(side=tk.LEFT)

        # --- SIDE BAR (Ligne 1, Colonne 0) ---
        side_frame = ttk.Frame(self.root, width=350)
        side_frame.grid(row=1, column=0, sticky="ns")
        side_frame.grid_propagate(False)

        # Ajout du Scrollbar et du Canvas pour rendre le menu défilant
        canvas_control = tk.Canvas(side_frame, width=330)
        scrollbar = ttk.Scrollbar(side_frame, orient="vertical", command=canvas_control.yview)
        scrollable_frame = ttk.Frame(canvas_control)
        
        scrollable_frame.bind("<Configure>", 
            lambda e: canvas_control.configure(scrollregion=canvas_control.bbox("all"))
        )
        canvas_control.create_window((0, 0), window=scrollable_frame, anchor="nw", width=330)
        canvas_control.configure(yscrollcommand=scrollbar.set)
        
        canvas_control.pack(side="left", fill="y", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        ttk.Label(scrollable_frame, text="Contrôles Détaillés", font=("Arial", 16, "bold")).pack(pady=10)
        
        # --- Contrôles Personnages ---
        char_frame = ttk.LabelFrame(scrollable_frame, text="Gestion Personnages", padding=10)
        char_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Button(char_frame, text="➕ Ajouter", command=self.add_character).pack(fill=tk.X, pady=2)
        ttk.Button(char_frame, text="🗑️ Supprimer", command=self.delete_character).pack(fill=tk.X, pady=2)
        
        # --- Contrôles Canvas (MODIFIÉ: TEXT ENTRY) ---
        canvas_frame = ttk.LabelFrame(scrollable_frame, text="Dimensions Canvas", padding=10)
        canvas_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Largeur
        width_row = ttk.Frame(canvas_frame)
        width_row.pack(fill=tk.X, pady=2)
        ttk.Label(width_row, text="Largeur (px):").pack(side=tk.LEFT)
        self.width_var = tk.StringVar(value=str(self.canvas_width))
        self.width_var.trace_add("write", self.update_canvas_size_entry)
        self.width_entry = ttk.Entry(width_row, textvariable=self.width_var, width=10)
        self.width_entry.pack(side=tk.RIGHT)
        
        # Hauteur
        height_row = ttk.Frame(canvas_frame)
        height_row.pack(fill=tk.X, pady=2)
        ttk.Label(height_row, text="Hauteur (px):").pack(side=tk.LEFT)
        self.height_var = tk.StringVar(value=str(self.canvas_height))
        self.height_var.trace_add("write", self.update_canvas_size_entry)
        self.height_entry = ttk.Entry(height_row, textvariable=self.height_var, width=10)
        self.height_entry.pack(side=tk.RIGHT)
        
        # --- Contrôles Tête/Corps (MODIFIÉ: MAX RANGE) ---

        head_body_frame = ttk.LabelFrame(scrollable_frame, text="Articulation Tête/Corps", padding=10)
        head_body_frame.pack(fill=tk.X, pady=5, padx=5)

        ttk.Label(head_body_frame, text="Écart Tête/Corps (Y):").pack()
        # Plage augmentée de 5 à 100
        self.neck_gap_slider = ttk.Scale(head_body_frame, from_=5, to=100, orient=tk.HORIZONTAL, command=self.update_neck_gap)
        self.neck_gap_slider.set(15)
        self.neck_gap_slider.pack(fill=tk.X, pady=2)
        
        ttk.Label(head_body_frame, text="Décalage Tête (Y):").pack()
        self.head_offset_slider = ttk.Scale(head_body_frame, from_=-40, to=40, orient=tk.HORIZONTAL, command=self.update_head_offset)
        self.head_offset_slider.set(0)
        self.head_offset_slider.pack(fill=tk.X, pady=2)

        # --- Contrôles Taille et Contour ---

        size_frame = ttk.LabelFrame(scrollable_frame, text="Taille & Contour", padding=10)
        size_frame.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Label(size_frame, text="Échelle:").pack()
        self.scale_slider = ttk.Scale(size_frame, from_=0.3, to=3.0, orient=tk.HORIZONTAL, command=self.update_scale)
        self.scale_slider.set(1.0)
        self.scale_slider.pack(fill=tk.X, pady=2)
        
        self.global_outline_var = tk.BooleanVar()
        self.global_outline_check = ttk.Checkbutton(size_frame, text="Tournoi (Contour) Global", variable=self.global_outline_var, command=self.update_global_outline)
        self.global_outline_check.pack(fill=tk.X, pady=5)
        
        ttk.Label(size_frame, text="Épaisseur contour (pts jaunes):").pack()
        self.outline_slider = ttk.Scale(size_frame, from_=2, to=15, orient=tk.HORIZONTAL, command=self.update_outline)
        self.outline_slider.set(6)
        self.outline_slider.pack(fill=tk.X, pady=2)
        
        ttk.Label(size_frame, text="Épaisseur membres:").pack()
        self.limb_width_slider = ttk.Scale(size_frame, from_=10, to=50, orient=tk.HORIZONTAL, command=self.update_limb_width)
        self.limb_width_slider.set(28)
        self.limb_width_slider.pack(fill=tk.X, pady=2)
        
        ttk.Label(size_frame, text="Arrondi coins (Corps):").pack()
        self.corner_slider = ttk.Scale(size_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.update_corner)
        self.corner_slider.set(45)
        self.corner_slider.pack(fill=tk.X, pady=2)
        
        # --- Contrôles Segments ---

        limb_control_frame = ttk.LabelFrame(scrollable_frame, text="Contrôle Segments", padding=10)
        limb_control_frame.pack(fill=tk.X, pady=5, padx=5)

        ttk.Label(limb_control_frame, text="Segment à modifier :").pack()
        self.limb_choice = ttk.Combobox(limb_control_frame, values=["Bras G - Haut", "Bras G - Bas", "Bras D - Haut", "Bras D - Bas", "Jambe G - Haut", "Jambe G - Bas"])
        self.limb_choice.set("Bras G - Haut")
        self.limb_choice.bind("<<ComboboxSelected>>", self.on_limb_select)
        self.limb_choice.pack(fill=tk.X, pady=2)

        ttk.Label(limb_control_frame, text="Longueur du Segment:").pack()
        self.length_slider = ttk.Scale(limb_control_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.update_segment_length)
        self.length_slider.set(35)
        self.length_slider.pack(fill=tk.X, pady=2)

        # --- Contrôles Rotation ---

        rot_frame = ttk.LabelFrame(scrollable_frame, text="Rotation", padding=10)
        rot_frame.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Label(rot_frame, text="Corps:").pack()
        self.rotation_slider = ttk.Scale(rot_frame, from_=0, to=360, orient=tk.HORIZONTAL, command=self.update_rotation)
        self.rotation_slider.set(0)
        self.rotation_slider.pack(fill=tk.X, pady=2)
        
        ttk.Label(rot_frame, text="Tête:").pack()
        self.head_rotation_slider = ttk.Scale(rot_frame, from_=-90, to=90, orient=tk.HORIZONTAL, command=self.update_head_rotation)
        self.head_rotation_slider.set(0)
        self.head_rotation_slider.pack(fill=tk.X, pady=2)

        # --- CANVAS ZONE (Ligne 1, Colonne 1) ---

        canvas_container = ttk.Frame(self.root)
        canvas_container.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        self.canvas = tk.Canvas(canvas_container, bg="white", width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack(fill=tk.BOTH, expand=True) # Rendre le canvas responsive dans son container
        
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Configure>", self.on_canvas_resize) # Capture le redimensionnement de la fenêtre

    # --- Méthodes de Redimensionnement ---

    def on_canvas_resize(self, event):
        """Met à jour les dimensions internes du canvas Tkinter lorsque la fenêtre est redimensionnée."""
        if self.canvas.winfo_width() > 0 and self.canvas.winfo_height() > 0:
            self.canvas_width = self.canvas.winfo_width()
            self.canvas_height = self.canvas.winfo_height()
            # Met à jour les champs de texte sans déclencher de boucle de redimensionnement
            self.width_var.set(str(self.canvas_width))
            self.height_var.set(str(self.canvas_height))
            self.draw()

    def update_canvas_size_entry(self, *args):
        """Met à jour le canvas lorsque les champs de texte sont modifiés."""
        try:
            new_width = int(self.width_var.get())
            new_height = int(self.height_var.get())
            
            if new_width > 0 and new_height > 0 and (new_width != self.canvas_width or new_height != self.canvas_height):
                self.canvas_width = new_width
                self.canvas_height = new_height
                self.canvas.config(width=self.canvas_width, height=self.canvas_height)
                self.draw()
        except ValueError:
            # Gère le cas où l'utilisateur entre du texte non numérique
            pass


    def update_canvas_size(self, value=None):
        """Méthode de compatibilité, non utilisée avec les Entry fields."""
        pass # Désactivée au profit de update_canvas_size_entry
        
    def add_character(self):
        """Ajoute un nouveau personnage à la scène."""
        if len(self.characters) >= 2:
            messagebox.showwarning("Limite", "Maximum 2 personnages autorisés.")
            return
        # Positionnement par défaut
        char = Character(x=self.canvas_width//2 + len(self.characters)*100, y=self.canvas_height//2)
        self.characters.append(char)
        self.selected_char = char
        self.update_sliders()
        self.save_history()
        self.draw()
        
    def delete_character(self):
        """Supprime le personnage sélectionné."""
        if self.selected_char and self.selected_char in self.characters:
            self.characters.remove(self.selected_char)
            self.selected_char = self.characters[0] if self.characters else None
            self.save_history()
            self.draw()
            
    def choose_color(self):
        """Ouvre un sélecteur de couleur pour le personnage sélectionné."""
        if not self.selected_char:
            return
        color = colorchooser.askcolor(self.selected_char.color)
        if color[1]:
            self.selected_char.color = color[1]
            self.draw()
            self.save_history() 

    # --- Fonctions de Mise à Jour ---
    
    def update_neck_gap(self, value):
        if self.selected_char:
            self.selected_char.neck_gap_y = float(value)
            self.selected_char.neck.y = -self.selected_char.head_radius - self.selected_char.neck_gap_y
            self.selected_char.waist.y = self.selected_char.body_height - self.selected_char.head_radius - self.selected_char.neck_gap_y
            self.draw()

    def update_head_offset(self, value):
        if self.selected_char:
            self.selected_char.head_offset_y = float(value)
            self.draw()

    def update_global_outline(self):
        if self.selected_char:
            self.selected_char.global_outline = self.global_outline_var.get()
            self.draw()

    def on_limb_select(self, event):
        """Met à jour le slider de longueur de segment lors de la sélection."""
        if self.selected_char:
            segment = self._get_selected_segment()
            if segment:
                if "Haut" in self.limb_choice.get():
                    self.length_slider.set(segment.mid_length)
                else:
                    self.length_slider.set(segment.end_length)

    def _get_selected_segment(self):
        """Fonction utilitaire pour obtenir le membre sélectionné."""
        if not self.selected_char:
            return None
        choice = self.limb_choice.get()
        if "Bras G" in choice:
            return self.selected_char.left_arm
        elif "Bras D" in choice:
            return self.selected_char.right_arm
        elif "Jambe G" in choice:
            return self.selected_char.left_leg
        elif "Jambe D" in choice:
            return self.selected_char.right_leg
        return None

    def update_segment_length(self, value):
        if not self.selected_char:
            return
            
        new_length = float(value)
        limb = self._get_selected_segment()
        if not limb:
            return

        choice = self.limb_choice.get()
        # Calcule le vecteur du segment (pour garder la direction lors du redimensionnement)
        if "Haut" in choice:
            limb.mid_length = new_length
            dx = limb.mid.x - limb.start.x
            dy = limb.mid.y - limb.start.y
            current_len = math.sqrt(dx**2 + dy**2)
            
            if current_len > 0:
                ratio = new_length / current_len
                limb.mid.x = limb.start.x + dx * ratio
                limb.mid.y = limb.start.y + dy * ratio

        else: # Segment END
            limb.end_length = new_length
            dx = limb.end.x - limb.mid.x
            dy = limb.end.y - limb.mid.y
            current_len = math.sqrt(dx**2 + dy**2)
            
            if current_len > 0:
                ratio = new_length / current_len
                limb.end.x = limb.mid.x + dx * ratio
                limb.end.y = limb.mid.y + dy * ratio
        
        self.draw()


    def update_scale(self, value):
        if self.selected_char:
            self.selected_char.scale = float(value)
            self.draw()
            
    def update_outline(self, value):
        if self.selected_char:
            self.selected_char.outline_width = int(float(value)) 
            self.draw()
            
    def update_limb_width(self, value):
        if self.selected_char:
            new_width = int(float(value))
            self.selected_char.limb_width = new_width
            for limb in self.selected_char.limbs:
                limb.width = new_width
            self.draw()
    
    def update_corner(self, value):
        if self.selected_char:
            self.selected_char.corner_radius = int(float(value))
            self.draw()
            
    def update_rotation(self, value):
        if self.selected_char:
            self.selected_char.rotation = float(value)
            self.draw()
            
    def update_head_rotation(self, value):
        if self.selected_char:
            self.selected_char.head_rotation = float(value)
            self.draw()
            
    def on_canvas_release(self, event):
        if self.dragging:
            self.dragging = False
            self.save_history()
            if self.selected_char:
                self.selected_char.selected_joint = None
                
    def update_sliders(self):
        """Met à jour tous les sliders."""
        if self.selected_char:
            self.scale_slider.set(self.selected_char.scale)
            self.outline_slider.set(self.selected_char.outline_width)
            self.rotation_slider.set(self.selected_char.rotation)
            self.head_rotation_slider.set(self.selected_char.head_rotation)
            self.limb_width_slider.set(self.selected_char.limb_width)
            self.corner_slider.set(self.selected_char.corner_radius)
            # Nouveaux sliders
            self.neck_gap_slider.set(self.selected_char.neck_gap_y)
            self.head_offset_slider.set(self.selected_char.head_offset_y)
            self.global_outline_var.set(self.selected_char.global_outline)
            self.on_limb_select(None)
        
    # --- Fonctions de Dessin ---

    def draw_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius, color, outline_color=""):
        """Dessine un rectangle avec coins arrondis."""
        radius = min(radius, abs(x2-x1)/2, abs(y2-y1)/2)
        
        # Remplissage principal
        canvas.create_rectangle(x1+radius, y1, x2-radius, y2, fill=color, outline=outline_color)
        canvas.create_rectangle(x1, y1+radius, x2, y2-radius, fill=color, outline=outline_color)
        
        # Coins arrondis (arcs de cercle)
        canvas.create_arc(x1, y1, x1+2*radius, y1+2*radius, start=90, extent=90, fill=color, outline=outline_color) 
        canvas.create_arc(x2-2*radius, y1, x2, y1+2*radius, start=0, extent=90, fill=color, outline=outline_color)   
        canvas.create_arc(x1, y2-2*radius, x1+2*radius, y2, start=180, extent=90, fill=color, outline=outline_color)
        canvas.create_arc(x2-2*radius, y2-2*radius, x2, y2, start=270, extent=90, fill=color, outline=outline_color)

    def draw_limb_segment(self, canvas, x1, y1, x2, y2, width, color, outline_color=""):
        """Dessine un segment de membre avec volume."""
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        if length < 5:
            return
        
        angle = math.atan2(dy, dx)
        perp_x = -math.sin(angle) * width / 2
        perp_y = math.cos(angle) * width / 2
        
        points = [(x1 + perp_x, y1 + perp_y), (x2 + perp_x, y2 + perp_y), 
                  (x2 - perp_x, y2 - perp_y), (x1 - perp_x, y1 - perp_y)]
        
        canvas.create_polygon(points, fill=color, outline=outline_color) 
        
        r = width / 2
        canvas.create_oval(x1-r, y1-r, x1+r, y1+r, fill=color, outline=outline_color)
        canvas.create_oval(x2-r, y2-r, x2+r, y2+r, fill=color, outline=outline_color)

    def draw(self):
        """Dessine la scène complète."""
        self.canvas.delete("all")
        bg_color = "white" if self.background_mode.get() == "white" else self.canvas["bg"]
        self.canvas.config(bg=bg_color)
        
        for char in self.characters:
            
            outline = "black" if char.global_outline else ""
            
            # --- Membres ---
            for limb in char.limbs:
                start_pos = char.get_world_pos(limb.start)
                mid_pos = char.get_world_pos(limb.mid)
                end_pos = char.get_world_pos(limb.end)
                width = limb.width * char.scale
                
                self.draw_limb_segment(self.canvas, start_pos[0], start_pos[1], mid_pos[0], mid_pos[1], width, char.color, outline)
                self.draw_limb_segment(self.canvas, mid_pos[0], mid_pos[1], end_pos[0], end_pos[1], width, char.color, outline)
                
            # --- Corps (Rounded Rectangle) ---
            neck_pos_y = char.y + char.neck.y * char.scale
            waist_pos_y = char.y + char.waist.y * char.scale
            body_width = char.body_width * char.scale
            radius = char.corner_radius * char.scale / 10 
            
            self.draw_rounded_rectangle(self.canvas, 
                                        char.x - body_width//2, neck_pos_y - 5 * char.scale, 
                                        char.x + body_width//2, waist_pos_y + 15 * char.scale, 
                                        radius, char.color, outline)
            
            # --- Tête (Cercle parfait) ---
            head_radius = char.head_radius * char.scale
            head_center_y = char.y + char.neck.y * char.scale + char.head_offset_y * char.scale
            
            self.canvas.create_oval(char.x - head_radius, head_center_y - head_radius, 
                                    char.x + head_radius, head_center_y + head_radius, 
                                    fill=char.color, outline=outline)
            
            # --- Indicateur rotation tête ---
            head_angle = math.radians(char.head_rotation) 
            indicator_length = head_radius * 0.7 
            
            indicator_x = char.x + indicator_length * math.sin(head_angle)
            indicator_y = head_center_y - indicator_length * math.cos(head_angle)
            
            self.canvas.create_line(char.x, head_center_y, indicator_x, indicator_y, 
                                    fill="red", width=4, capstyle=tk.ROUND)

            # --- Affichage des articulations mobiles (Points jaunes) ---
            for limb in char.limbs:
                for joint in [limb.mid, limb.end]:
                    joint_pos = char.get_world_pos(joint)
                    r = 8 
                    self.canvas.create_oval(joint_pos[0]-r, joint_pos[1]-r, joint_pos[0]+r, joint_pos[1]+r, 
                                            fill="yellow", outline="black", width=2)
                    
            # --- Indicateur de Sélection ---
            if char == self.selected_char:
                bounds = 150 * char.scale 
                self.canvas.create_rectangle(char.x - bounds, char.y - bounds, char.x + bounds, char.y + bounds, 
                                            outline="red", width=3, dash=(5, 5))


    # --- Export Image (Gestion de la Transparence) ---

    def export_image(self, fmt):
        is_png = (fmt == "png")
        
        filetypes = [("PNG", "*.png")] if is_png else [("JPEG", "*.jpeg")]
        filename = filedialog.asksaveasfilename(defaultextension=f".{fmt}", filetypes=filetypes)
        if not filename:
            return
            
        # Définition du fond
        if is_png and self.background_mode.get() == "transparent":
            img = Image.new('RGBA', (self.canvas_width, self.canvas_height), (0, 0, 0, 0))
        else:
            img = Image.new('RGB', (self.canvas_width, self.canvas_height), 'white')
        
        draw = ImageDraw.Draw(img)
        
        # Le dessin sur Pillow reste inchangé, mais le fond (0, 0, 0, 0) permet la transparence si PNG
        for char in self.characters:
            
            outline_width_export = 4 if char.global_outline else 0
            outline_color = "black"
            
            # --- Membres et Corps/Tête (omitted for brevity, drawing logic unchanged) ---
            
            # --- Membres ---
            for limb in char.limbs:
                start_pos = char.get_world_pos(limb.start)
                mid_pos = char.get_world_pos(limb.mid)
                end_pos = char.get_world_pos(limb.end)
                width = int(limb.width * char.scale)
                
                draw.line(start_pos + mid_pos, fill=char.color, width=width, joint='curve')
                draw.line(mid_pos + end_pos, fill=char.color, width=width, joint='curve')
                
                for jpos in [start_pos, mid_pos, end_pos]:
                    r = width // 2
                    draw.ellipse([jpos[0]-r, jpos[1]-r, jpos[0]+r, jpos[1]+r], fill=char.color)
                    if outline_width_export > 0:
                         draw.ellipse([jpos[0]-r, jpos[1]-r, jpos[0]+r, jpos[1]+r], outline=outline_color, width=outline_width_export)
            
            # --- Corps (Rounded Rectangle) ---
            neck_pos_y = char.y + char.neck.y * char.scale
            waist_pos_y = char.y + char.waist.y * char.scale
            body_width = char.body_width * char.scale
            radius_pil = int(char.corner_radius * char.scale / 10) 
            
            body_coords = [
                char.x - body_width//2, neck_pos_y - 5 * char.scale, 
                char.x + body_width//2, waist_pos_y + 15 * char.scale
            ]
            
            try:
                draw.rounded_rectangle(body_coords, radius=radius_pil, fill=char.color, outline=outline_color, width=outline_width_export)
            except AttributeError:
                draw.rectangle(body_coords, fill=char.color, outline=outline_color, width=outline_width_export)
            
            # --- Tête (Cercle parfait) ---
            head_radius = char.head_radius * char.scale
            head_center_y = char.y + char.neck.y * char.scale + char.head_offset_y * char.scale
            
            head_coords = [char.x - head_radius, head_center_y - head_radius, 
                           char.x + head_radius, head_center_y + head_radius]
                           
            draw.ellipse(head_coords, fill=char.color, outline=outline_color, width=outline_width_export)

        # Finalisation de l'export
        if fmt == "jpeg":
            img = img.convert('RGB')
        img.save(filename, fmt.upper())
        messagebox.showinfo("Succès", f"Exporté en {fmt.upper()}!")

    # --- Historique/Chargement (omitted for brevity, logic unchanged) ---
    
    # ... (les fonctions save_history, undo, load_state, save_scene, load_scene, on_canvas_click, on_canvas_drag sont conservées telles quelles)

    def save_history(self):
        state = []
        for char in self.characters:
            char_data = {
                'x': char.x, 'y': char.y, 'scale': char.scale, 
                'rotation': char.rotation, 'head_rotation': char.head_rotation, 
                'color': char.color, 'outline_width': char.outline_width, 
                'limb_width': char.limb_width, 'corner_radius': char.corner_radius, 
                'neck_gap_y': char.neck_gap_y,                 
                'head_offset_y': char.head_offset_y,           
                'global_outline': char.global_outline,         
                'joints': {}
            }
            for i, limb in enumerate(char.limbs):
                char_data['joints'][f'limb_{i}_mid'] = (limb.mid.x, limb.mid.y)
                char_data['joints'][f'limb_{i}_end'] = (limb.end.x, limb.end.y)
                char_data['joints'][f'limb_{i}_mid_len'] = limb.mid_length
                char_data['joints'][f'limb_{i}_end_len'] = limb.end_length
            state.append(char_data)
            
        self.history = self.history[:self.history_index+1]
        self.history.append(state)
        self.history_index += 1

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            state = self.history[self.history_index]
            self.load_state(state) 
            self.update_sliders()
            self.draw()
        else:
            messagebox.showinfo("Annuler", "Plus d'actions à annuler.")
            
    def load_state(self, state):
        try:
            while len(self.characters) > len(state):
                self.characters.pop()
            while len(self.characters) < len(state):
                self.characters.append(Character())
            
            for i, char_data in enumerate(state):
                char = self.characters[i]
                char.x = char_data['x']
                char.y = char_data['y']
                char.scale = char_data['scale']
                char.rotation = char_data['rotation']
                char.head_rotation = char_data.get('head_rotation', 0)
                char.color = char_data['color']
                char.outline_width = char_data['outline_width']
                char.limb_width = char_data.get('limb_width', 28)
                char.corner_radius = char_data.get('corner_radius', 45)
                char.neck_gap_y = char_data.get('neck_gap_y', 15)            
                char.head_offset_y = char_data.get('head_offset_y', 0)       
                char.global_outline = char_data.get('global_outline', False) 

                char.neck.y = -char.head_radius - char.neck_gap_y
                char.waist.y = char.body_height - char.head_radius - char.neck_gap_y
                
                for j, limb in enumerate(char.limbs):
                    mid_pos = char_data['joints'][f'limb_{j}_mid']
                    end_pos = char_data['joints'][f'limb_{j}_end']
                    limb.mid.x, limb.mid.y = mid_pos
                    limb.end.x, limb.end.y = end_pos
                    limb.width = char.limb_width

                    limb.mid_length = char_data['joints'].get(f'limb_{j}_mid_len', 35)
                    limb.end_length = char_data['joints'].get(f'limb_{j}_end_len', 35)

            self.selected_char = self.characters[0] if self.characters else None
            
        except Exception as e:
            messagebox.showerror("Erreur de chargement", f"Erreur lors du chargement de l'état: {e}")

    def save_scene(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not filename:
            return
            
        scene_data = {
            'canvas_width': self.canvas_width, 
            'canvas_height': self.canvas_height, 
            'background_mode': self.background_mode.get(), # Sauvegarde le mode de fond
            'characters': self.history[self.history_index]
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(scene_data, f, indent=2)
            messagebox.showinfo("Succès", "Scène sauvegardée!")
        except Exception as e:
            messagebox.showerror("Erreur de Sauvegarde", f"Impossible d'écrire le fichier: {e}")

    def load_scene(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not filename:
            return
        
        try:
            with open(filename, 'r') as f:
                scene_data = json.load(f)
            
            # Mise à jour des dimensions via les variables de texte
            self.canvas_width = scene_data.get('canvas_width', 800)
            self.canvas_height = scene_data.get('canvas_height', 800)
            self.width_var.set(str(self.canvas_width))
            self.height_var.set(str(self.canvas_height))
            
            # Mise à jour du mode de fond
            self.background_mode.set(scene_data.get('background_mode', 'white'))
            
            self.canvas.config(width=self.canvas_width, height=self.canvas_height)

            characters_state = scene_data['characters']
            self.load_state(characters_state)
            
            self.history = [characters_state]
            self.history_index = 0

            self.update_sliders()
            self.draw()
            messagebox.showinfo("Succès", "Scène chargée!")
            
        except Exception as e:
            messagebox.showerror("Erreur de Chargement", f"Impossible de charger le fichier JSON: {e}")

    def on_canvas_click(self, event):
        self.selected_char = None
        
        for char in self.characters:
            for limb in char.limbs:
                for joint in [limb.mid, limb.end]:
                    wx, wy = char.get_world_pos(joint)
                    dist = math.sqrt((event.x - wx)**2 + (event.y - wy)**2)
                    if dist < 15: 
                        self.selected_char = char
                        char.selected_joint = joint
                        self.dragging = True
                        self.update_sliders()
                        self.draw()
                        return
                        
        for char in self.characters:
            dist = math.sqrt((event.x - char.x)**2 + (event.y - char.y)**2)
            if dist < 100 * char.scale: 
                self.selected_char = char
                char.selected_joint = None
                self.dragging = True
                self.update_sliders()
                self.draw()
                return

        self.draw()

    def on_canvas_drag(self, event):
        if not self.dragging or not self.selected_char:
            return
        
        if self.selected_char.selected_joint:
            self.selected_char.set_from_world_pos(self.selected_char.selected_joint, event.x, event.y)
        else:
            self.selected_char.x = event.x
            self.selected_char.y = event.y
        self.draw()

# --- Point d'entrée du programme ---

def main():
    root = tk.Tk()
    app = CharacterCreatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()