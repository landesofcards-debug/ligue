# <VALIDATED>
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QLabel, QStackedWidget, QInputDialog, QLineEdit, QMessageBox, QFrame)
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtCore import Qt, QSize
import qtawesome as qta

# Importation des pages
from views.admin_panel import AdminPanel
from views.saisie_match import SaisieMatchPanel
from views.classement import ClassementPanel
from views.profil_joueur import ProfilJoueurPanel
from views.accueil import AccueilPanel # Nouvelle Importation

class MainWindow(QMainWindow):
    """
    Fenêtre principale de l'application SuperLigue.
    """

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.setWindowTitle("SuperLigue LOC")
        self.resize(1280, 720)
        
        # Sécurité
        self.admin_pin = "23560552"
        
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.assets_dir = os.path.join(self.base_dir, 'assets')
        self.police_dir = os.path.join(self.assets_dir, 'police')
        self.bg_dir = os.path.join(self.assets_dir, 'image de fond')
        
        self._load_fonts()
        self._setup_ui()
        self._apply_global_style()

    def _setup_ui(self):
        # Widget Central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Zone de contenu (StackedWidget)
        self.pages = QStackedWidget()
        
        # Initialisation des panels
        self.admin_page = AdminPanel(self.db)
        self.saisie_page = SaisieMatchPanel(self.db)
        self.classement_page = ClassementPanel(self.db)
        self.profil_page = ProfilJoueurPanel(self.db)
        self.accueil_page = AccueilPanel(self.db) # Utilisation du nouveau Panel
        
        # Ajout au StackedWidget
        self.pages.addWidget(self.accueil_page)      # Index 0
        self.pages.addWidget(self.saisie_page)       # Index 1
        self.pages.addWidget(self.classement_page)   # Index 2
        self.pages.addWidget(self.profil_page)       # Index 3
        self.pages.addWidget(self.admin_page)        # Index 4
        
        self.main_layout.addWidget(self.pages)

        # Barre de Navigation (Bottom Bar)
        self._setup_nav_bar()

    def _setup_nav_bar(self):
        self.nav_bar = QFrame()
        self.nav_bar.setObjectName("bottom_bar")
        self.nav_bar.setFixedHeight(80)
        nav_layout = QHBoxLayout(self.nav_bar)
        nav_layout.setContentsMargins(20, 0, 20, 0)
        nav_layout.setSpacing(10)

        # Boutons de navigation
        self.btn_accueil = self._create_nav_btn("ACCUEIL", "fa5s.home", 0)
        self.btn_saisie = self._create_nav_btn("SAISIE", "fa5s.gamepad", 1)
        self.btn_classement = self._create_nav_btn("LIGUE", "fa5s.list-ol", 2)
        self.btn_profil = self._create_nav_btn("PROFIL", "fa5s.user", 3)
        self.btn_admin = self._create_nav_btn("ADMIN", "fa5s.cog", 4)

        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_accueil)
        nav_layout.addWidget(self.btn_saisie)
        nav_layout.addWidget(self.btn_classement)
        nav_layout.addWidget(self.btn_profil)
        nav_layout.addWidget(self.btn_admin)
        nav_layout.addStretch()

        self.main_layout.addWidget(self.nav_bar)

    def _create_nav_btn(self, text, icon, index):
        btn = QPushButton(text)
        btn.setObjectName("nav_button")
        btn.setIcon(qta.icon(icon, color="#00f3ff"))
        btn.setIconSize(QSize(24, 24))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._on_nav_clicked(index))
        return btn

    def _on_nav_clicked(self, index):
        if index == 4:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT valeur FROM systeme WHERE cle = 'admin_pin'")
            res = cursor.fetchone()
            db_pin = res['valeur'] if res else self.admin_pin
            conn.close()

            pin, ok = QInputDialog.getText(self, "Accès Restreint", "Entrez le code administrateur :", QLineEdit.EchoMode.Password)
            if ok and pin == db_pin:
                self.pages.setCurrentIndex(index)
            elif ok:
                QMessageBox.critical(self, "Erreur", "Code incorrect.")
        else:
            self.pages.setCurrentIndex(index)

    def _load_fonts(self):
        """Charge les polices personnalisées du dossier assets/police."""
        if os.path.exists(self.police_dir):
            for font_file in os.listdir(self.police_dir):
                if font_file.endswith('.ttf') or font_file.endswith('.otf'):
                    QFontDatabase.addApplicationFont(os.path.join(self.police_dir, font_file))

    def _apply_global_style(self):
        # Récupération du chemin du fond d'écran
        bg_image_path = ""
        png_path = os.path.join(self.bg_dir, "bg_accueil.png").replace("\\", "/")
        jpg_path = os.path.join(self.bg_dir, "bg_accueil.jpg").replace("\\", "/")
        
        if os.path.exists(png_path): bg_image_path = png_path
        elif os.path.exists(jpg_path): bg_image_path = jpg_path

        accueil_css = ""
        if bg_image_path:
            accueil_css = f"#accueil_page {{ background-image: url('{bg_image_path}'); background-position: center; background-repeat: no-repeat; }}"

        self.setStyleSheet(f"""
            QMainWindow {{ background-color: #050505; }}
            #bottom_bar {{ background-color: rgba(20, 25, 40, 0.95); border-top: 1px solid rgba(0, 243, 255, 0.3); }}
            #nav_button {{ background-color: transparent; color: white; border: none; border-radius: 12px; padding: 10px 20px; font-family: 'Orbitron'; font-weight: bold; }}
            #nav_button:hover {{ background-color: rgba(0, 243, 255, 0.1); border-bottom: 2px solid #00f3ff; }}
            {accueil_css}
        """)
# <VALIDATED>