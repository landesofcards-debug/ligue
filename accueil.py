# <VALIDATED>
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QProgressBar, QScrollArea, QStackedWidget, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QPixmap, QIcon
import qtawesome as qta

class AccueilPanel(QWidget):
    """
    Tableau de bord dynamique (Dashboard) de la Ligue - Format Cinématique.
    Affiche la liste des Boss, le Top 8 par jeu (rotation auto) et les Piliers de la semaine.
    """
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.setObjectName("accueil_page")
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # Timer pour la rotation du Hall of Fame (10 secondes)
        self.rotation_timer = QTimer(self)
        self.rotation_timer.timeout.connect(self._rotate_podium)
        
        self._setup_ui()

# <VALIDATED>
    def showEvent(self, event):
        self._refresh_data()
        self.rotation_timer.start(10000) # 10 secondes
        super().showEvent(event)
        # On décale l'alerte d'une demi-seconde pour laisser l'interface s'afficher d'abord
        QTimer.singleShot(500, self._verifier_alerte_hebdo)

    def _verifier_alerte_hebdo(self):
        """Vérifie en BDD si une nouvelle semaine vient de commencer pour afficher le rapport."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT valeur FROM systeme WHERE cle = 'alerte_hebdo'")
        alerte = cursor.fetchone()
        
        if alerte and alerte['valeur'] == '1':
            cursor.execute("SELECT valeur FROM systeme WHERE cle = 'rapport_hebdo'")
            rapport_row = cursor.fetchone()
            texte_rapport = rapport_row['valeur'] if rapport_row else "Mise à jour effectuée."
            
            # On remet l'alerte à zéro pour ne pas réafficher la popup en boucle
            cursor.execute("UPDATE systeme SET valeur = '0' WHERE cle = 'alerte_hebdo'")
            conn.commit()
            
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "🗓️ NOUVELLE SEMAINE DE LIGUE !", 
                                    f"Le reset hebdomadaire a eu lieu !\n\nBilan des événements :\n\n{texte_rapport}")
            
            # Rafraîchissement final des compteurs de l'accueil
            self._refresh_data()
            
        conn.close()
# <VALIDATED>

    def hideEvent(self, event):
        self.rotation_timer.stop()
        super().hideEvent(event)

    def _setup_ui(self):
        # Layout principal avec marges pour laisser respirer le fond
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(50, 100, 50, 30)
        self.main_layout.setSpacing(40)

        # --- PARTIE HAUTE (2 BLOCS RECTANGULAIRES) ---
        layout_haut = QHBoxLayout()
        layout_haut.setSpacing(40)

        # Bloc A : Liste des Boss (Scrollable)
        self.box_boss = self._create_box(" LISTE DES BOSS", "fa5s.skull-crossbones", "#ff0055")
        self.scroll_boss = QScrollArea()
        self.scroll_boss.setWidgetResizable(True)
        self.scroll_boss.setStyleSheet("background: transparent; border: none;")
        self.container_boss = QWidget()
        self.container_boss.setStyleSheet("background: transparent;")
        self.layout_boss_list = QVBoxLayout(self.container_boss)
        self.scroll_boss.setWidget(self.container_boss)
        self.box_boss.findChild(QVBoxLayout).addWidget(self.scroll_boss)
        
        # Bloc B : Hall of Fame (Top 8 tournant)
        self.box_podium = self._create_box(" HALL OF FAME", "fa5s.trophy", "#FFD700")
        self.podium_stack = QStackedWidget()
        self.podium_stack.setStyleSheet("background: transparent; border: none;")
        self.box_podium.findChild(QVBoxLayout).addWidget(self.podium_stack)

        layout_haut.addWidget(self.box_boss, 1)
        layout_haut.addWidget(self.box_podium, 1)
        self.main_layout.addLayout(layout_haut, 2)

        # --- PARTIE BASSE (BANDEAU ACTIVITÉ) ---
        self.box_activite = self._create_box(" PILIERS DE LA SEMAINE", "fa5s.bolt", "#00ff9d")
        self.box_activite.setFixedHeight(180)
        self.layout_piliers = QHBoxLayout()
        self.layout_piliers.setSpacing(20)
        self.box_activite.findChild(QVBoxLayout).addLayout(self.layout_piliers)
        
        # Centrage horizontal du bloc activité
        layout_bas = QHBoxLayout()
        layout_bas.addStretch()
        layout_bas.addWidget(self.box_activite, 2)
        layout_bas.addStretch()
        
        self.main_layout.addLayout(layout_bas, 1)

    def _create_box(self, title, icon_name, color):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(10, 10, 20, 0.8);
                border: 2px solid {color};
                border-radius: 15px;
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        layout = QVBoxLayout(frame)
        
        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icon_name, color=color).pixmap(20, 20))
        txt_lbl = QLabel(title)
        txt_lbl.setStyleSheet(f"color: {color}; font-family: 'Orbitron'; font-size: 16px; font-weight: bold;")
        header.addWidget(icon_lbl)
        header.addWidget(txt_lbl)
        header.addStretch()
        
        layout.addLayout(header)
        return frame

    def _refresh_data(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # 1. Refresh Boss List (Tous les Boss actifs)
        self._clear_layout(self.layout_boss_list)
        cursor.execute("""
            SELECT b.*, j.surnom, j.avatar, g.nom as jeu_nom 
            FROM event_boss b 
            JOIN joueurs j ON b.joueur_id = j.id 
            JOIN jeux g ON b.jeu_id = g.id 
            WHERE b.statut = 'ACTIF'
        """)
        bosses = cursor.fetchall()
        if bosses:
            for boss in bosses:
                self.layout_boss_list.addWidget(self._create_boss_item(boss))
        else:
            lbl_none = QLabel("Aucun Boss en vue...")
            lbl_none.setStyleSheet("color: #555; font-family: 'Rajdhani'; font-size: 14px;")
            self.layout_boss_list.addWidget(lbl_none)
        self.layout_boss_list.addStretch()

        # 2. Refresh Podium (Top 8 par jeu - Option B)
        current_idx = self.podium_stack.currentIndex()
        self._clear_layout_stacked(self.podium_stack)
        cursor.execute("SELECT id, nom FROM jeux WHERE actif = 1")
        jeux = cursor.fetchall()
        for jeu in jeux:
            self.podium_stack.addWidget(self._create_top8_page(jeu['id'], jeu['nom']))
        
        if current_idx < self.podium_stack.count():
            self.podium_stack.setCurrentIndex(current_idx)

        # 3. Refresh Piliers (Activité Hebdo - Top 4)
        self._clear_layout(self.layout_piliers)
        cursor.execute("SELECT valeur FROM systeme WHERE cle = 'dernier_reset_mardi'")
        reset_date_row = cursor.fetchone()
        reset_date = reset_date_row['valeur'] if reset_date_row else "2000-01-01"
        
        cursor.execute("""
            SELECT j.surnom, j.avatar, COUNT(m.id) as nb_matchs
            FROM joueurs j
            JOIN matchs m ON (j.id = m.joueur1_id OR j.id = m.joueur2_id)
            WHERE m.date >= ? AND j.surnom != 'Anonyme'
            GROUP BY j.id ORDER BY nb_matchs DESC LIMIT 4
        """, (reset_date,))
        for p in cursor.fetchall():
            self.layout_piliers.addWidget(self._create_pilier_item(p))

        conn.close()

    def _create_boss_item(self, boss):
        widget = QWidget()
        lay = QHBoxLayout(widget)
        lay.setContentsMargins(5, 5, 5, 5)
        
        lbl_img = QLabel()
        lbl_img.setFixedSize(40, 40)
        lbl_img.setStyleSheet("border: 1px solid #ff0055; border-radius: 20px;")
        
        avatar_path = ""
        if boss['avatar']:
            avatar_path = os.path.join(self.base_dir, 'assets', 'avatars', boss['avatar'])
            
        if avatar_path and os.path.exists(avatar_path):
            lbl_img.setPixmap(QIcon(avatar_path).pixmap(36, 36))
        else:
            lbl_img.setPixmap(qta.icon("fa5s.user-ninja", color="#ff0055").pixmap(30, 30))
        
        infos = QVBoxLayout()
        name = QLabel(f"{boss['surnom'].upper()}")
        name.setStyleSheet("color: white; font-family: 'Orbitron'; font-size: 13px; font-weight: bold;")
        game = QLabel(boss['jeu_nom'])
        game.setStyleSheet("color: #ff0055; font-family: 'Rajdhani'; font-size: 11px;")
        infos.addWidget(name)
        infos.addWidget(game)

        bar_hp = QProgressBar()
        bar_hp.setRange(0, boss['pv_max'])
        bar_hp.setValue(boss['pv_actuels'])
        bar_hp.setFixedHeight(6)
        bar_hp.setTextVisible(False)
        bar_hp.setStyleSheet("""
            QProgressBar { background: #222; border-radius: 3px; border: none; } 
            QProgressBar::chunk { background: #ff0055; border-radius: 3px; }
        """)

        lay.addWidget(lbl_img)
        lay.addLayout(infos)
        lay.addWidget(bar_hp)
        return widget

    def _create_top8_page(self, jeu_id, jeu_nom):
        page = QWidget()
        lay = QVBoxLayout(page)
        
        title = QLabel(f"Top 8 - {jeu_nom}")
        title.setStyleSheet("color: #FFD700; font-family: 'Orbitron'; font-size: 14px; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT j.surnom, COUNT(m.id) as victoires
            FROM joueurs j
            JOIN matchs m ON (j.id = m.joueur1_id OR j.id = m.joueur2_id)
            WHERE m.jeu_id = ? AND (
                (m.joueur1_id = j.id AND m.resultat_j1 LIKE '%Victoire%') OR
                (m.joueur2_id = j.id AND m.resultat_j2 LIKE '%Victoire%')
            )
            GROUP BY j.id ORDER BY victoires DESC LIMIT 8
        """, (jeu_id,))
        players = cursor.fetchall()
        conn.close()

        grid = QGridLayout()
        grid.setSpacing(10)
        
        if not players:
            lbl_v = QLabel("Aucun duel enregistré.")
            lbl_v.setStyleSheet("color: #555; font-family: 'Rajdhani'; font-size: 13px;")
            lay.addWidget(lbl_v, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            for i, p in enumerate(players):
                row = i % 4
                col = 0 if i < 4 else 1
                icon_name = "fa5s.medal" if i < 3 else "fa5s.user"
                color = "#FFD700" if i==0 else "#C0C0C0" if i==1 else "#CD7F32" if i==2 else "#555"
                
                lbl = QLabel(f"{i+1}. {p['surnom']} ({p['victoires']}V)")
                lbl.setStyleSheet("color: white; font-family: 'Rajdhani'; font-size: 12px;")
                icon = QLabel()
                icon.setPixmap(qta.icon(icon_name, color=color).pixmap(14, 14))
                
                grid.addWidget(icon, row, col*2)
                grid.addWidget(lbl, row, col*2 + 1)
        
        lay.addLayout(grid)
        lay.addStretch()
        return page

    def _create_pilier_item(self, player):
        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_img = QLabel()
        lbl_img.setFixedSize(60, 60)
        lbl_img.setStyleSheet("border: 2px solid #00ff9d; border-radius: 30px; background: rgba(0,255,157,0.05);")
        lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        avatar_path = ""
        if player['avatar']:
            avatar_path = os.path.join(self.base_dir, 'assets', 'avatars', player['avatar'])
            
        if avatar_path and os.path.exists(avatar_path):
            lbl_img.setPixmap(QIcon(avatar_path).pixmap(54, 54))
        else:
            lbl_img.setPixmap(qta.icon("fa5s.fire", color="#00ff9d").pixmap(40, 40))
        
        name = QLabel(player['surnom'])
        name.setStyleSheet("color: white; font-family: 'Orbitron'; font-size: 12px; font-weight: bold;")
        count = QLabel(f"{player['nb_matchs']} MATCHS")
        count.setStyleSheet("color: #00ff9d; font-family: 'Rajdhani'; font-size: 11px;")
        
        lay.addWidget(lbl_img, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(name, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(count, alignment=Qt.AlignmentFlag.AlignCenter)
        return widget

    def _rotate_podium(self):
        if self.podium_stack.count() > 1:
            next_idx = (self.podium_stack.currentIndex() + 1) % self.podium_stack.count()
            self.podium_stack.setCurrentIndex(next_idx)

    def _clear_layout(self, layout):
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
                elif item.layout(): self._clear_layout(item.layout())

    def _clear_layout_stacked(self, stack):
        while stack.count():
            widget = stack.widget(0)
            stack.removeWidget(widget)
            widget.deleteLater()
# <VALIDATED>