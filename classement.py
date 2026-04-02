# <VALIDATED>
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QHBoxLayout)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QColor
import qtawesome as qta
import os
from controllers.league_mechanics import LeagueMechanics

class ClassementPanel(QWidget):
    """
    Hall of Fame - Tableau du classement de la Ligue LOC.
    """

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.mechanics = LeagueMechanics(self.db)
        self.setObjectName("classement_panel")
        self._setup_ui()
        self._apply_stylesheet()

    def showEvent(self, event):
        """Met à jour le classement à l'ouverture de l'onglet."""
        self._refresh_games_list()
        self._load_ranking()
        super().showEvent(event)

    def _refresh_games_list(self):
        """Recharge la liste des jeux dans le menu déroulant."""
        self.combo_filtre.blockSignals(True)
        self.combo_filtre.clear()
        self.combo_filtre.addItem("Classement Général (Basé sur l'XP)", None)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom FROM jeux WHERE actif = 1 ORDER BY nom ASC")
        for j in cursor.fetchall():
            self.combo_filtre.addItem(f"Classement : {j['nom']} (Forme: 12 derniers matchs)", j['id'])
        conn.close()
        self.combo_filtre.blockSignals(False)

    def _get_star_icon(self, star_type):
        """Récupère l'icône ou le QPixmap configuré en BDD."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        key = f"icon_star_{star_type}"
        cursor.execute("SELECT valeur FROM systeme WHERE cle = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        val = row['valeur'] if row else "fa5s.star"
        color = "#ffea00" if star_type == "normale" else "#bc13fe" if star_type == "pourpre" else "#FFD700"
        
        if val.startswith("fa5"):
            return qta.icon(val, color=color)
        else:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            path = os.path.join(base_dir, 'assets', 'icones', val)
            if os.path.exists(path):
                return QIcon(path)
        return qta.icon("fa5s.star", color=color)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(30)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Titre
        title = QLabel("HALL OF FAME - RÉSULTATS")
        title.setObjectName("page_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Filtre (Menu Déroulant)
        filtre_layout = QHBoxLayout()
        self.combo_filtre = QComboBox()
        self.combo_filtre.setFixedWidth(550)
        self.combo_filtre.currentIndexChanged.connect(self._load_ranking)
        filtre_layout.addStretch()
        filtre_layout.addWidget(self.combo_filtre)
        filtre_layout.addStretch()
        layout.addLayout(filtre_layout)

        # Le Tableau (5 Colonnes)
        self.table_ranking = QTableWidget(0, 5)
        self.table_ranking.setHorizontalHeaderLabels(["Rang", "Joueur", "Niveau", "Étoiles", "Score"])
        self.table_ranking.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_ranking.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_ranking.verticalHeader().setVisible(False)
        self.table_ranking.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_ranking.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table_ranking.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table_ranking.setIconSize(QSize(40, 40))

        layout.addWidget(self.table_ranking)

    def _create_stars_widget(self, normales, pourpres, couronnes, icon_n, icon_p, icon_c):
        """Crée un conteneur visuel affichant les icônes des étoiles acquises via les paramètres globaux."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for _ in range(couronnes):
            lbl = QLabel()
            lbl.setPixmap(icon_c.pixmap(20, 20))
            layout.addWidget(lbl)
            
        for _ in range(pourpres):
            lbl = QLabel()
            lbl.setPixmap(icon_p.pixmap(20, 20))
            layout.addWidget(lbl)
            
        for _ in range(normales):
            lbl = QLabel()
            lbl.setPixmap(icon_n.pixmap(20, 20))
            layout.addWidget(lbl)

        if couronnes == 0 and pourpres == 0 and normales == 0:
            lbl = QLabel("-")
            lbl.setStyleSheet("color: #555555; font-weight: bold; font-size: 20px;")
            layout.addWidget(lbl)

        return widget

    def _appliquer_icone(self, item, avatar_str, icone_niv_str):
        """Affiche l'avatar personnalisé s'il existe, sinon l'icône de niveau RPG."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        icon = None
        
        if avatar_str:
            avatar_path = os.path.join(base_dir, 'assets', 'avatars', avatar_str)
            if os.path.exists(avatar_path):
                icon = QIcon(avatar_path)
        
        if not icon:
            icone_path = os.path.join(base_dir, 'assets', 'icones', icone_niv_str)
            if os.path.exists(icone_path) and not icone_niv_str.startswith('fa5'):
                icon = QIcon(icone_path)
            else:
                try: 
                    icon = qta.icon(icone_niv_str, color="#00f3ff")
                except Exception: 
                    icon = qta.icon("fa5s.user-circle", color="#00f3ff")
                
        item.setIcon(icon)

    def _load_ranking(self):
        """Charge les données selon le filtre sélectionné (Général ou Par Jeu limité aux 12 derniers matchs)."""
        jeu_id = self.combo_filtre.currentData()
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        joueurs_calcules = []

        if jeu_id is None:
            # Mode Général : Tri par XP
            cursor.execute("SELECT id, surnom, avatar, xp_total, etoiles_normales, etoiles_pourpres, couronne_max FROM joueurs ORDER BY xp_total DESC")
            joueurs_calcules = [dict(row) for row in cursor.fetchall()]
        else:
            # Mode Par Jeu : Isoler les 12 derniers matchs par joueur
            cursor.execute("""
                SELECT DISTINCT j.id, j.surnom, j.avatar, j.xp_total, j.etoiles_normales, j.etoiles_pourpres, j.couronne_max
                FROM joueurs j
                JOIN matchs m ON m.joueur1_id = j.id OR m.joueur2_id = j.id
                WHERE m.jeu_id = ?
            """, (jeu_id,))
            
            joueurs_concernes = cursor.fetchall()
            
            for j in joueurs_concernes:
                cursor.execute("""
                    SELECT joueur1_id, resultat_j1, resultat_j2
                    FROM matchs
                    WHERE jeu_id = ? AND (joueur1_id = ? OR joueur2_id = ?)
                    ORDER BY date DESC, id DESC
                    LIMIT 12
                """, (jeu_id, j['id'], j['id']))
                
                matchs = cursor.fetchall()
                total_matchs = len(matchs)
                victoires = 0
                
                for m in matchs:
                    if m['joueur1_id'] == j['id'] and 'Victoire' in m['resultat_j1']:
                        victoires += 1
                    elif m['joueur1_id'] != j['id'] and 'Victoire' in m['resultat_j2']:
                        victoires += 1
                
                ratio = (victoires / total_matchs * 100) if total_matchs > 0 else 0
                
                joueur_dict = dict(j)
                joueur_dict['ratio'] = ratio
                joueur_dict['total_matchs'] = total_matchs
                joueurs_calcules.append(joueur_dict)
                
            # Tri Python : Ratio > Couronnes > Pourpres > Normales > XP
            joueurs_calcules.sort(key=lambda x: (x['ratio'], x['couronne_max'], x['etoiles_pourpres'], x['etoiles_normales'], x['xp_total']), reverse=True)
        
        self.table_ranking.setRowCount(0)
        
        # Pré-chargement des icônes d'étoiles personnalisées
        icon_normale = self._get_star_icon("normale")
        icon_pourpre = self._get_star_icon("pourpre")
        icon_couronne = self._get_star_icon("couronne")
        
        for index, joueur in enumerate(joueurs_calcules):
            self.table_ranking.insertRow(index)
            
            # Colonne 1 : Rang
            item_rang = QTableWidgetItem(f"#{index + 1}")
            item_rang.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if index == 0: item_rang.setForeground(QColor("#FFD700"))
            elif index == 1: item_rang.setForeground(QColor("#C0C0C0"))
            elif index == 2: item_rang.setForeground(QColor("#CD7F32"))
            self.table_ranking.setItem(index, 0, item_rang)
            
            # Colonne 2 : Joueur
            item_joueur = QTableWidgetItem(joueur['surnom'].upper())
            item_joueur.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_ranking.setItem(index, 1, item_joueur)
            
            # Colonne 3 : Niveau et Icône/Avatar
            level_info = self.mechanics.get_level_info(joueur['xp_total'])
            item_niveau = QTableWidgetItem(level_info['nom'].upper())
            self._appliquer_icone(item_niveau, joueur['avatar'], level_info['icone'])
            item_niveau.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_ranking.setItem(index, 2, item_niveau)
            
            # Colonne 4 : Étoiles
            widget_etoiles = self._create_stars_widget(joueur['etoiles_normales'], joueur['etoiles_pourpres'], joueur['couronne_max'], icon_normale, icon_pourpre, icon_couronne)
            self.table_ranking.setCellWidget(index, 3, widget_etoiles)
            
            # Colonne 5 : Score
            if jeu_id is None:
                score_text = f"{joueur['xp_total']:.1f} XP"
            else:
                nb = joueur['total_matchs']
                texte_match = "match" if nb == 1 else "derniers matchs" if nb == 12 else "matchs"
                score_text = f"{int(joueur['ratio'])}% WR ({nb} {texte_match})"
            
            item_score = QTableWidgetItem(score_text)
            item_score.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_ranking.setItem(index, 4, item_score)
            
        for r in range(self.table_ranking.rowCount()):
            self.table_ranking.setRowHeight(r, 55)

        conn.close()

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            #page_title { color: #bc13fe; font-family: 'Orbitron'; font-size: 48px; font-weight: 900; letter-spacing: 3px; }
            
            QComboBox { background-color: #141928; color: #00f3ff; border: 2px solid #bc13fe; border-radius: 8px; padding: 10px; font-family: 'Rajdhani'; font-size: 18px; font-weight: bold; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #141928; color: white; selection-background-color: #bc13fe; }
            
            QTableWidget { background-color: rgba(20, 25, 40, 0.8); color: white; border: 2px solid rgba(0, 243, 255, 0.2); border-radius: 12px; font-family: 'Rajdhani'; font-size: 18px; alternate-background-color: rgba(20, 25, 40, 0.5); }
            QHeaderView::section { background-color: #0a0a1a; color: #00f3ff; font-family: 'Orbitron'; font-size: 16px; font-weight: bold; padding: 15px; border: none; border-bottom: 2px solid #bc13fe; }
            QTableWidget::item { padding: 5px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
        """)
# <VALIDATED>