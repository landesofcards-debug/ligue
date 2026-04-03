# <VALIDATED>
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QPushButton, QFrame, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QGridLayout, QProgressBar, QDialog, QScrollArea, QCompleter)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
import qtawesome as qta
import os
from controllers.league_mechanics import LeagueMechanics

class RewardDialog(QDialog):
    """
    Fenêtre personnalisée pour l'ouverture des lots.
    """
    def __init__(self, parent, preview_data):
        super().__init__(parent)
        self.setWindowTitle("BUTIN DÉBLOQUÉ")
        self.setFixedSize(550, 500)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet("background-color: #0a0a1a; border: 3px solid #FFD700; border-radius: 20px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        title_icon = qta.icon("fa5s.box-open", color="#FFD700")
        
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon = QLabel()
        lbl_icon.setPixmap(title_icon.pixmap(26, 26))
        lbl_text = QLabel("VOS RÉCOMPENSES")
        lbl_text.setStyleSheet("color: #FFD700; font-family: 'Orbitron'; font-size: 26px; font-weight: bold; border: none;")
        title_layout.addWidget(lbl_icon)
        title_layout.addWidget(lbl_text)
        layout.addWidget(title_widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        for g in preview_data['rapport']:
            frame = QFrame()
            couleur_bordure = '#FFD700' if g['type'] == 'NIVEAU' else '#00ff9d'
            frame.setStyleSheet(f"background-color: rgba(255, 215, 0, 0.1); border: 1px solid {couleur_bordure}; border-radius: 10px; margin-bottom: 10px;")
            
            f_lay = QVBoxLayout(frame)
            
            icon_t_name = "fa5s.star" if g['type'] == 'NIVEAU' else "fa5s.ticket-alt"
            
            t_widget = QWidget()
            t_layout = QHBoxLayout(t_widget)
            t_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            t_layout.setContentsMargins(0,0,0,0)
            
            lbl_t_icon = QLabel()
            lbl_t_icon.setPixmap(qta.icon(icon_t_name, color=couleur_bordure).pixmap(18, 18))
            lbl_t_text = QLabel(g['titre'].replace('⭐ ', '').replace('🎫 ', '').replace('🎁 ', ''))
            lbl_t_text.setStyleSheet("color: white; font-weight: bold; font-family: 'Orbitron'; font-size: 18px; border: none;")
            
            t_layout.addWidget(lbl_t_icon)
            t_layout.addWidget(lbl_t_text)
            f_lay.addWidget(t_widget)
            
            for opt in g['options']:
                item = QLabel(f"• {opt}")
                item.setStyleSheet("color: #e0f7fa; font-family: 'Rajdhani'; font-size: 16px; border: none; padding-left: 10px;")
                f_lay.addWidget(item)
                
            content_layout.addWidget(frame)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("background-color: #333333; color: white; font-family: 'Orbitron'; font-weight: bold; padding: 12px; border-radius: 10px; border: 2px solid #555555;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_ok = QPushButton("Lots récupérés")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet("background-color: #FFD700; color: black; font-family: 'Orbitron'; font-weight: bold; padding: 12px; border-radius: 10px; border: none;")
        btn_ok.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)


class ProfilJoueurPanel(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.mechanics = LeagueMechanics(self.db)
        self.setObjectName("profil_panel")
        self.current_player_id = None
        
        self.etoiles_gauches = []
        self.etoiles_droites = []
        self.etoiles_couronnes = []
        
        self._setup_ui()
        self._apply_stylesheet()

# <VALIDATED>
    def showEvent(self, event):
        pseudo_actuel = self.combo_recherche.currentText()
        self.combo_recherche.blockSignals(True)
        self._refresh_player_list()
        
        # Si un joueur était déjà sélectionné, on le remet. 
        # Sinon, on vide complètement la barre (Index -1) pour faire apparaître le texte grisé.
        if pseudo_actuel and pseudo_actuel != "Sélectionnez un profil...":
            index = self.combo_recherche.findText(pseudo_actuel)
            if index >= 0:
                self.combo_recherche.setCurrentIndex(index)
            else:
                self.combo_recherche.setCurrentIndex(-1)
        else:
            self.combo_recherche.setCurrentIndex(-1)
            
        self.combo_recherche.blockSignals(False)
        self._load_profil()
        super().showEvent(event)

    def _refresh_player_list(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT surnom FROM joueurs WHERE surnom IS NOT NULL AND surnom != '' ORDER BY surnom ASC")
        pseudos = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        self.combo_recherche.clear()
        
        # On ajoute UNIQUEMENT les vrais joueurs (plus de faux joueur "Sélectionnez...")
        self.combo_recherche.addItems(pseudos)
        
        completer = QCompleter(pseudos)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.combo_recherche.setCompleter(completer)
# </VALIDATED>

    def _get_star_icon(self, star_type):
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

# <VALIDATED>
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        
        header = QHBoxLayout()
        title = QLabel("PROFIL JOUEUR")
        title.setObjectName("page_title")
        
        # --- MODIFICATION: Combobox centrée, plus large, plus haute et fluide ---
        self.combo_recherche = QComboBox()
        self.combo_recherche.setEditable(True)
        self.combo_recherche.setFixedWidth(400)
        self.combo_recherche.setFixedHeight(40)
        self.combo_recherche.lineEdit().setPlaceholderText(" Tapez un nom ou cliquez sur la flèche...")
        self.combo_recherche.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo_recherche.activated.connect(lambda: self._load_profil())
        self.combo_recherche.lineEdit().returnPressed.connect(self._load_profil_from_enter)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.combo_recherche)
        header.addStretch()
        layout.addLayout(header)
        # -------------------------------------------------------------------------

        top_split = QHBoxLayout()

        self.frame_identite = QFrame()
        self.frame_identite.setObjectName("frame_identite")
        self.frame_identite.setFixedWidth(320)
        
        bloc_gauche_layout = QVBoxLayout(self.frame_identite)
        bloc_gauche_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        bloc_gauche_layout.setSpacing(10)
        
        self.btn_image_profil = QPushButton()
        self.btn_image_profil.setObjectName("image_profil")
        self.btn_image_profil.setFixedSize(120, 120)
        
        self.lbl_nom = QLabel("---")
        self.lbl_nom.setObjectName("lbl_nom")
        self.lbl_nom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_rang = QLabel("RANG : ---")
        self.lbl_rang.setObjectName("lbl_rang")
        self.lbl_rang.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.frame_badge = QFrame()
        self.frame_badge.setObjectName("badge_niveau")
        badge_layout = QVBoxLayout(self.frame_badge)
        badge_layout.setContentsMargins(5, 5, 5, 5)
        self.lbl_niv = QLabel("NIVEAU")
        self.lbl_niv.setObjectName("lbl_niv_titre")
        self.lbl_niv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_layout.addWidget(self.lbl_niv)
        
        self.lbl_xp = QLabel("0.0 XP")
        self.lbl_xp.setObjectName("lbl_xp")
        self.lbl_xp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.bar_xp = QProgressBar()
        self.bar_xp.setFixedSize(220, 12)
        self.bar_xp.setTextVisible(False)
        
        self.btn_coffre = QPushButton()
        self.btn_coffre.setObjectName("btn_coffre_inactif")
        self.btn_coffre.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_coffre.clicked.connect(self._ouvrir_coffre)
        
        # --- BLOC ÉTOILES (Couronnes + Normales/Pourpres) ---
        etoiles_global_layout = QVBoxLayout()
        etoiles_global_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        etoiles_global_layout.setSpacing(8)

        lay_couronnes = QHBoxLayout()
        lay_couronnes.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_couronnes.setSpacing(2)
        for _ in range(6):
            star = QLabel()
            star.setFixedSize(20, 20)
            self.etoiles_couronnes.append(star)
            lay_couronnes.addWidget(star)

        etoiles_basses_layout = QHBoxLayout()
        etoiles_basses_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lay_gauches = QHBoxLayout()
        lay_gauches.setSpacing(2)
        for _ in range(6):
            star = QLabel()
            star.setFixedSize(20, 20)
            self.etoiles_gauches.append(star)
            lay_gauches.addWidget(star)
            
        lay_droites = QHBoxLayout()
        lay_droites.setSpacing(2)
        for _ in range(6):
            star = QLabel()
            star.setFixedSize(20, 20)
            self.etoiles_droites.append(star)
            lay_droites.addWidget(star)
            
        etoiles_basses_layout.addLayout(lay_gauches)
        etoiles_basses_layout.addSpacing(15)
        etoiles_basses_layout.addLayout(lay_droites)
        
        etoiles_global_layout.addLayout(lay_couronnes)
        etoiles_global_layout.addLayout(etoiles_basses_layout)
        # -------------------------------------------------------------
        
        bloc_gauche_layout.addWidget(self.btn_image_profil, alignment=Qt.AlignmentFlag.AlignCenter)
        bloc_gauche_layout.addWidget(self.lbl_nom)
        bloc_gauche_layout.addWidget(self.lbl_rang)
        bloc_gauche_layout.addWidget(self.frame_badge, alignment=Qt.AlignmentFlag.AlignCenter)
        bloc_gauche_layout.addWidget(self.lbl_xp)
        bloc_gauche_layout.addWidget(self.bar_xp, alignment=Qt.AlignmentFlag.AlignCenter)
        bloc_gauche_layout.addSpacing(20) 
        bloc_gauche_layout.addWidget(self.btn_coffre, alignment=Qt.AlignmentFlag.AlignCenter)
        bloc_gauche_layout.addSpacing(10)
        bloc_gauche_layout.addLayout(etoiles_global_layout)
        bloc_gauche_layout.addStretch() 
        
        top_split.addWidget(self.frame_identite)

        self.grid_stats = QGridLayout()
        self.grid_stats.setSpacing(15)
        
        self.card_nemesis = self._create_stat_card(" NÉMÉSIS", "fa5s.skull", "#ff0055")
        self.lay_nem = QVBoxLayout()
        self.lbl_nem_pseudo = QLabel("---")
        self.lbl_nem_pseudo.setStyleSheet("color: white; font-family: 'Orbitron'; font-size: 16px; font-weight: bold;")
        self.lbl_nem_details = QLabel("Rang: - | Niv: - | WR: -%")
        self.lbl_nem_details.setStyleSheet("color: #ff0055; font-family: 'Rajdhani'; font-size: 13px;")
        self.lay_nem.addWidget(self.lbl_nem_pseudo)
        self.lay_nem.addWidget(self.lbl_nem_details)
        self.card_nemesis.layout().addLayout(self.lay_nem)
        self.grid_stats.addWidget(self.card_nemesis, 0, 0)
        
        self.card_victime = self._create_stat_card(" PROIE", "fa5s.crosshairs", "#00ff9d")
        self.lay_vic = QVBoxLayout()
        self.lbl_vic_pseudo = QLabel("---")
        self.lbl_vic_pseudo.setStyleSheet("color: white; font-family: 'Orbitron'; font-size: 16px; font-weight: bold;")
        self.lbl_vic_details = QLabel("Rang: - | Niv: - | WR: -%")
        self.lbl_vic_details.setStyleSheet("color: #00ff9d; font-family: 'Rajdhani'; font-size: 13px;")
        self.lay_vic.addWidget(self.lbl_vic_pseudo)
        self.lay_vic.addWidget(self.lbl_vic_details)
        self.card_victime.layout().addLayout(self.lay_vic)
        self.grid_stats.addWidget(self.card_victime, 0, 1)
        
        self.card_global = self._create_stat_card(" WINRATE GLOBAL", "fa5s.trophy", "#FFD700")
        self.lbl_global_val = QLabel("0%")
        self.lbl_global_val.setObjectName("stat_value_large")
        self.bar_global = QProgressBar()
        self.bar_global.setFixedHeight(8)
        self.bar_global.setTextVisible(False)
        self.bar_global.setObjectName("bar_global")
        self.card_global.layout().addWidget(self.lbl_global_val)
        self.card_global.layout().addWidget(self.bar_global)
        self.grid_stats.addWidget(self.card_global, 1, 0)
        
        self.card_ratios = self._create_stat_card(" SPÉCIALISATION", "fa5s.gamepad", "#00f3ff")
        self.layout_ratios_jeux = QVBoxLayout()
        self.layout_ratios_jeux.setSpacing(5)
        self.card_ratios.layout().addLayout(self.layout_ratios_jeux)
        self.grid_stats.addWidget(self.card_ratios, 1, 1)

        self.card_event = self._create_stat_card(" DÉFIS BOSS ACTIFS", "fa5s.dragon", "#ff0055")
        self.card_event.setStyleSheet("background: rgba(255, 0, 85, 0.05); border: 2px solid #ff0055; border-radius: 10px;")
        
        self.scroll_boss = QScrollArea()
        self.scroll_boss.setWidgetResizable(True)
        self.scroll_boss.setStyleSheet("background: transparent; border: none;")
        
        self.container_boss = QWidget()
        self.container_boss.setStyleSheet("background: transparent;")
        self.layout_boss_list = QVBoxLayout(self.container_boss)
        self.layout_boss_list.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_boss.setWidget(self.container_boss)
        self.card_event.layout().addWidget(self.scroll_boss)
        
        self.grid_stats.addWidget(self.card_event, 0, 2, 2, 1)

        self.card_cibles = self._create_stat_card(" CONTRAT (CIBLE)", "fa5s.crosshairs", "#ffea00")
        self.card_cibles.setStyleSheet("background: rgba(255, 234, 0, 0.05); border: 1px solid #ffea00; border-radius: 10px;")
        self.layout_cibles = QVBoxLayout()
        self.layout_cibles.setSpacing(5)
        self.card_cibles.layout().addLayout(self.layout_cibles)
        self.grid_stats.addWidget(self.card_cibles, 2, 0, 1, 2) 

        self.card_event_2 = self._create_stat_card(" ÉVÉNEMENT 2 (À venir)", "fa5s.calendar-alt", "#555555")
        self.card_event_2.setStyleSheet("background: rgba(20, 25, 40, 0.4); border: 1px dashed #555555; border-radius: 10px;")
        lbl_event_2 = QLabel("En attente...")
        lbl_event_2.setStyleSheet("color: #777777; font-family: 'Rajdhani'; font-size: 14px;")
        self.card_event_2.layout().addWidget(lbl_event_2)
        self.card_event_2.hide() 

        frame_stats_container = QFrame()
        frame_stats_container.setLayout(self.grid_stats)
        top_split.addWidget(frame_stats_container)

        layout.addLayout(top_split)

        lbl_histo = QLabel("HISTORIQUE DE COMBAT (20 Derniers Matchs)")
        lbl_histo.setStyleSheet("color: #bc13fe; font-family: 'Orbitron'; font-size: 18px; font-weight: bold; margin-top: 15px;")
        layout.addWidget(lbl_histo)
        
        self.table_historique = QTableWidget(0, 4)
        self.table_historique.setHorizontalHeaderLabels(["Date", "Jeu", "Adversaire", "Résultat"])
        self.table_historique.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_historique)
# </VALIDATED>
    def _create_stat_card(self, title_text, icon_name, color):
        card = QFrame()
        card.setObjectName("stat_card")
        lay = QVBoxLayout(card)
        
        title_lay = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icon_name, color=color).pixmap(16, 16))
        txt_lbl = QLabel(title_text)
        txt_lbl.setStyleSheet(f"color: {color}; font-family: 'Orbitron'; font-size: 14px; font-weight: bold; border: none;")
        
        title_lay.addWidget(icon_lbl)
        title_lay.addWidget(txt_lbl)
        title_lay.addStretch()
        
        lay.addLayout(title_lay)
        return card

    def _load_profil_from_enter(self):
        self._load_profil()

    def _appliquer_image_profil(self, icone_str, avatar_str, base_dir):
        self.btn_image_profil.setIconSize(QSize(110, 110))
        
        if avatar_str:
            avatar_path = os.path.join(base_dir, 'assets', 'avatars', avatar_str)
            if os.path.exists(avatar_path):
                self.btn_image_profil.setIcon(QIcon(avatar_path))
                return
                
        icone_path = os.path.join(base_dir, 'assets', 'icones', icone_str)
        if os.path.exists(icone_path) and not icone_str.startswith('fa5'):
            self.btn_image_profil.setIcon(QIcon(icone_path))
        else:
            try: 
                self.btn_image_profil.setIcon(qta.icon(icone_str, color="#bc13fe"))
            except Exception: 
                self.btn_image_profil.setIcon(qta.icon("fa5s.user-circle", color="#bc13fe"))

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self._clear_layout(item.layout())

    def _create_boss_item_widget(self, boss, base_dir):
        widget = QWidget()
        layout_boss = QVBoxLayout(widget)
        layout_boss.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_boss.setContentsMargins(0, 0, 0, 15)
        
        layout_boss_header = QHBoxLayout()
        lbl_boss_avatar = QLabel()
        lbl_boss_avatar.setFixedSize(60, 60)
        lbl_boss_avatar.setStyleSheet("border: 2px solid #ff0055; border-radius: 30px; background: #050505;")
        lbl_boss_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout_boss_text = QVBoxLayout()
        lbl_boss_nom = QLabel(boss['boss_pseudo'].upper())
        lbl_boss_nom.setStyleSheet("color: white; font-family: 'Orbitron'; font-size: 16px; font-weight: bold; border: none;")
        lbl_boss_jeu = QLabel(f"Jeu: {boss['jeu_nom']}")
        lbl_boss_jeu.setStyleSheet("color: #ff0055; font-family: 'Rajdhani'; font-size: 12px; border: none;")
        layout_boss_text.addWidget(lbl_boss_nom)
        layout_boss_text.addWidget(lbl_boss_jeu)
        
        layout_boss_header.addWidget(lbl_boss_avatar)
        layout_boss_header.addLayout(layout_boss_text)
        layout_boss_header.addStretch()
        
        if boss['boss_avatar'] and os.path.exists(os.path.join(base_dir, 'assets', 'avatars', boss['boss_avatar'])):
            icon = QIcon(os.path.join(base_dir, 'assets', 'avatars', boss['boss_avatar']))
            lbl_boss_avatar.setPixmap(icon.pixmap(50, 50))
        else:
            niv_boss_icon = self.mechanics.get_level_info(boss['boss_xp'])['icone']
            try: 
                lbl_boss_avatar.setPixmap(qta.icon(niv_boss_icon, color="#ff0055").pixmap(40, 40))
            except:
                lbl_boss_avatar.setPixmap(qta.icon("fa5s.skull", color="#ff0055").pixmap(40, 40))

        layout_boss_stats = QHBoxLayout()
        
        layout_boss_hp = QVBoxLayout()
        lbl_boss_hp_text = QLabel("Points de Vie")
        lbl_boss_hp_text.setStyleSheet("color: #aaa; font-family: 'Rajdhani'; font-size: 10px; border: none;")
        layout_boss_hp_icons = QHBoxLayout()
        layout_boss_hp_icons.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout_boss_hp_icons.setSpacing(2)
        for i in range(boss['pv_max']):
            icon_lbl = QLabel()
            color_hp = "#ff0055" if i < boss['pv_actuels'] else "#333333"
            icon_lbl.setPixmap(qta.icon("fa5s.heart", color=color_hp).pixmap(12, 12))
            layout_boss_hp_icons.addWidget(icon_lbl)
        layout_boss_hp.addWidget(lbl_boss_hp_text)
        layout_boss_hp.addLayout(layout_boss_hp_icons)
        
        layout_boss_wins = QVBoxLayout()
        lbl_boss_wins_text = QLabel("Objectif Boss")
        lbl_boss_wins_text.setStyleSheet("color: #aaa; font-family: 'Rajdhani'; font-size: 10px; border: none;")
        layout_boss_wins_icons = QHBoxLayout()
        layout_boss_wins_icons.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout_boss_wins_icons.setSpacing(2)
        for i in range(boss['victoires_requises']):
            icon_lbl = QLabel()
            color_cup = "#FFD700" if i < boss['victoires_actuelles'] else "#333333"
            icon_lbl.setPixmap(qta.icon("fa5s.trophy", color=color_cup).pixmap(12, 12))
            layout_boss_wins_icons.addWidget(icon_lbl)
        layout_boss_wins.addWidget(lbl_boss_wins_text)
        layout_boss_wins.addLayout(layout_boss_wins_icons)
        
        layout_boss_stats.addLayout(layout_boss_hp)
        layout_boss_stats.addLayout(layout_boss_wins)

        lbl_boss_status = QLabel()
        lbl_boss_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if boss['joueur_id'] == self.current_player_id:
            lbl_boss_status.setText("C'EST VOUS LE BOSS !")
            lbl_boss_status.setStyleSheet("color: #ff0055; font-weight: bold; border: none; margin-top:5px; font-size: 12px;")
        else:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM event_boss_essais WHERE joueur_id = ? AND boss_id = ?", (self.current_player_id, boss['id']))
            deja_tente = cursor.fetchone()
            conn.close()
            
            if deja_tente:
                lbl_boss_status.setText("🔴 DÉFI RELEVÉ (Revenez mardi)")
                lbl_boss_status.setStyleSheet("color: #ff0055; border: none; margin-top:5px; font-size: 12px;")
            else:
                lbl_boss_status.setText("🟢 PRÊT AU COMBAT")
                lbl_boss_status.setStyleSheet("color: #00ff9d; font-weight: bold; border: none; margin-top:5px; font-size: 12px;")

        layout_boss.addLayout(layout_boss_header)
        layout_boss.addLayout(layout_boss_stats)
        layout_boss.addWidget(lbl_boss_status)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: rgba(255, 0, 85, 0.3);")
        layout_boss.addWidget(line)

        return widget

    def _load_profil(self):
        pseudo = self.combo_recherche.currentText()
        if "Sélectionnez" in pseudo or not pseudo: 
            return
            
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM joueurs WHERE surnom = ?", (pseudo,))
        joueur = cursor.fetchone()
        
        if not joueur: 
            conn.close()
            return
            
        self.current_player_id = joueur['id']
        
        self.lbl_nom.setText(joueur['surnom'].upper())
        self.lbl_xp.setText(f"{joueur['xp_total']:.1f} XP")
        
        cursor.execute("SELECT COUNT(*) as nb_mieux_classes FROM joueurs WHERE xp_total > ?", (joueur['xp_total'],))
        rang = cursor.fetchone()['nb_mieux_classes'] + 1
        suffixe = "er" if rang == 1 else "ème"
        self.lbl_rang.setText(f"RANG : {rang}{suffixe}")
        
        level_info = self.mechanics.get_level_info(joueur['xp_total'])
        self.lbl_niv.setText(level_info['nom'].upper())
        self.bar_xp.setValue(self.mechanics.get_xp_progress(joueur['xp_total'])['percent'])
        
        niveaux = self.mechanics.get_all_levels()
        xp_restante = 0.0
        for lvl in niveaux:
            if lvl["xp_min"] > joueur['xp_total']:
                xp_restante = lvl["xp_min"] - joueur['xp_total']
                break
                
        if xp_restante > 0:
            self.bar_xp.setToolTip(f"Il manque {xp_restante:.1f} XP pour le prochain niveau !")
        else:
            self.bar_xp.setToolTip("Niveau Maximum atteint !")
        
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self._appliquer_image_profil(level_info['icone'], joueur['avatar'], base_dir)
        
        icon_normale = self._get_star_icon("normale")
        icon_pourpre = self._get_star_icon("pourpre")
        icon_couronne = self._get_star_icon("couronne")
        
        for i, star_label in enumerate(self.etoiles_couronnes):
            if i < joueur['couronne_max']:
                star_label.setPixmap(icon_couronne.pixmap(18, 18))
            else:
                star_label.setPixmap(qta.icon("fa5s.crown", color="#333333").pixmap(18, 18))

        for i, star_label in enumerate(self.etoiles_gauches): 
            if i < joueur['etoiles_normales']:
                star_label.setPixmap(icon_normale.pixmap(18, 18))
            else:
                star_label.setPixmap(qta.icon("fa5s.star", color="#333333").pixmap(18, 18))
            
        for i, star_label in enumerate(self.etoiles_droites): 
            if i < joueur['etoiles_pourpres']:
                star_label.setPixmap(icon_pourpre.pixmap(18, 18))
            else:
                star_label.setPixmap(qta.icon("fa5s.star", color="#333333").pixmap(18, 18))
        
        status_lots = self.mechanics.get_rewards_status(self.current_player_id)
        has_rewards = (status_lots['attente_niveaux'] + status_lots['attente_paliers']) > 0
        
        if has_rewards:
            self.btn_coffre.setObjectName("btn_coffre_actif")
            self.btn_coffre.setIcon(qta.icon("fa5s.gift", color="#FFD700"))
            self.btn_coffre.setFixedSize(80, 80)
            self.btn_coffre.setIconSize(QSize(50, 50))
            self.btn_coffre.setEnabled(True)
        else:
            self.btn_coffre.setObjectName("btn_coffre_inactif")
            self.btn_coffre.setIcon(qta.icon("fa5s.gift", color="#333333"))
            self.btn_coffre.setFixedSize(60, 60)
            self.btn_coffre.setIconSize(QSize(40, 40))
            self.btn_coffre.setEnabled(False)

        stats = self.mechanics.get_player_stats(self.current_player_id)
        
        for key, lbl_pseudo, lbl_details in [('nemesis', self.lbl_nem_pseudo, self.lbl_nem_details), 
                                             ('victime', self.lbl_vic_pseudo, self.lbl_vic_details)]:
            rival_pseudo = stats[key].split(' (')[0]
            cursor.execute("SELECT id, xp_total FROM joueurs WHERE surnom = ?", (rival_pseudo,))
            rival = cursor.fetchone()
            
            if rival:
                cursor.execute("SELECT COUNT(*) as r FROM joueurs WHERE xp_total > ?", (rival['xp_total'],))
                r_rival = cursor.fetchone()['r'] + 1
                cursor.execute("SELECT SUM(CASE WHEN (joueur1_id=? AND resultat_j1 LIKE '%Victoire%') OR (joueur2_id=? AND resultat_j2 LIKE '%Victoire%') THEN 1 ELSE 0 END) as w, COUNT(*) as t FROM matchs WHERE joueur1_id=? OR joueur2_id=?", 
                               (rival['id'], rival['id'], rival['id'], rival['id']))
                m = cursor.fetchone()
                wr = int(m['w']/m['t']*100) if m['t']>0 else 0
                niv_r = self.mechanics.get_level_info(rival['xp_total'])['nom']
                
                lbl_pseudo.setText(f"{rival_pseudo.upper()} {stats[key].replace(rival_pseudo, '')}")
                lbl_details.setText(f"Rang: {r_rival} | Niv: {niv_r} | WR: {wr}%")
            else:
                lbl_pseudo.setText("AUCUN")
                lbl_details.setText("En attente de combats...")
        
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN (joueur1_id = ? AND resultat_j1 LIKE '%Victoire%') OR (joueur2_id = ? AND resultat_j2 LIKE '%Victoire%') THEN 1 ELSE 0 END) as wins,
                COUNT(id) as total
            FROM matchs 
            WHERE joueur1_id = ? OR joueur2_id = ?
        """, (self.current_player_id, self.current_player_id, self.current_player_id, self.current_player_id))
        
        row_global = cursor.fetchone()
        wins_global = row_global['wins'] if row_global and row_global['wins'] else 0
        total_global = row_global['total'] if row_global and row_global['total'] else 0
        winrate_global = int((wins_global / total_global * 100)) if total_global > 0 else 0
        
        self.lbl_global_val.setText(f"{winrate_global}%")
        self.bar_global.setValue(winrate_global)
        
        cursor.execute("""
            SELECT j.nom,
                   SUM(CASE WHEN (m.joueur1_id = ? AND m.resultat_j1 LIKE '%Victoire%') OR (m.joueur2_id = ? AND m.resultat_j2 LIKE '%Victoire%') THEN 1 ELSE 0 END) as wins,
                   COUNT(m.id) as total
            FROM matchs m
            JOIN jeux j ON m.jeu_id = j.id
            WHERE m.joueur1_id = ? OR m.joueur2_id = ?
            GROUP BY j.id
            ORDER BY total DESC
        """, (self.current_player_id, self.current_player_id, self.current_player_id, self.current_player_id))
        
        jeux_stats = cursor.fetchall()
        
        self._clear_layout(self.layout_ratios_jeux)
        
        if not jeux_stats:
            lbl_vide = QLabel("Aucun match joué.")
            lbl_vide.setStyleSheet("color: #777; font-family: 'Rajdhani'; font-size: 14px; border: none;")
            self.layout_ratios_jeux.addWidget(lbl_vide)
        else:
            for js in jeux_stats:
                nom_jeu = js['nom']
                total = js['total']
                wins = js['wins']
                wr = int((wins / total * 100)) if total > 0 else 0
                
                row_lay = QHBoxLayout()
                lbl = QLabel(f"{nom_jeu}")
                lbl.setStyleSheet("color: white; font-family: 'Rajdhani'; font-size: 14px; border: none;")
                lbl_pourcent = QLabel(f"{wr}%")
                lbl_pourcent.setStyleSheet("color: #00f3ff; font-family: 'Orbitron'; font-size: 12px; font-weight: bold; border: none;")
                
                bar = QProgressBar()
                bar.setFixedHeight(6)
                bar.setTextVisible(False)
                bar.setValue(wr)
                bar.setStyleSheet("""
                    QProgressBar { background-color: #333; border-radius: 3px; border: none; }
                    QProgressBar::chunk { background-color: #00f3ff; border-radius: 3px; }
                """)
                
                v_lay = QVBoxLayout()
                v_lay.setSpacing(2)
                h_title = QHBoxLayout()
                h_title.addWidget(lbl)
                h_title.addStretch()
                h_title.addWidget(lbl_pourcent)
                v_lay.addLayout(h_title)
                v_lay.addWidget(bar)
                
                self.layout_ratios_jeux.addLayout(v_lay)

        self._clear_layout(self.layout_boss_list)
        
        cursor.execute("""
            SELECT b.*, j.nom as jeu_nom, j2.surnom as boss_pseudo, j2.avatar as boss_avatar, j2.xp_total as boss_xp
            FROM event_boss b
            JOIN jeux j ON b.jeu_id = j.id
            JOIN joueurs j2 ON b.joueur_id = j2.id
            JOIN joueurs_jeux jj ON b.jeu_id = jj.jeu_id
            WHERE b.statut = 'ACTIF' AND jj.joueur_id = ?
        """, (self.current_player_id,))
        
        bosses = cursor.fetchall()
        
        if not bosses:
            lbl_none = QLabel("AUCUN DÉFI ACTUEL\nLa ligue est calme...")
            lbl_none.setStyleSheet("color: #777; font-family: 'Rajdhani'; font-size: 14px; border: none; text-align: center;")
            lbl_none.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout_boss_list.addWidget(lbl_none)
        else:
            for boss in bosses:
                self.layout_boss_list.addWidget(self._create_boss_item_widget(boss, base_dir))

        self._clear_layout(self.layout_cibles)

        cursor.execute("""
            SELECT j.nom as jeu_nom, cible.surnom as cible_pseudo
            FROM event_tueurs t
            JOIN jeux j ON t.jeu_id = j.id
            JOIN joueurs cible ON t.cible_id = cible.id
            WHERE t.chasseur_id = ? AND t.statut = 'ACTIF'
        """, (self.current_player_id,))
        
        contrats = cursor.fetchall()
        
        if not contrats:
            lbl_vide_cib = QLabel("Aucun contrat de traque en cours.")
            lbl_vide_cib.setStyleSheet("color: #777; font-family: 'Rajdhani'; font-size: 14px; border: none;")
            self.layout_cibles.addWidget(lbl_vide_cib)
        else:
            for contrat in contrats:
                lay_ligne = QHBoxLayout()
                
                icon_cible = QLabel()
                icon_cible.setPixmap(qta.icon("fa5s.crosshairs", color="#ffea00").pixmap(16, 16))
                
                lbl_titre_cible = QLabel(f" {contrat['jeu_nom']} :")
                lbl_titre_cible.setStyleSheet("color: white; font-family: 'Rajdhani'; font-size: 16px; font-weight: bold; border: none;")
                
                lbl_noms = QLabel(contrat['cible_pseudo'].upper())
                
                is_nemesis = (stats['nemesis'] != "---" and contrat['cible_pseudo'] in stats['nemesis'])
                if is_nemesis:
                    lbl_noms.setText(f"{contrat['cible_pseudo'].upper()} (💀 BONUS NÉMÉSIS)")
                    lbl_noms.setStyleSheet("color: #ff0055; font-family: 'Orbitron'; font-size: 16px; font-weight: bold; border: none;")
                else:
                    lbl_noms.setStyleSheet("color: #ffea00; font-family: 'Orbitron'; font-size: 16px; font-weight: bold; border: none;")
                
                lay_ligne.addWidget(icon_cible)
                lay_ligne.addWidget(lbl_titre_cible)
                lay_ligne.addWidget(lbl_noms)
                lay_ligne.addStretch()
                self.layout_cibles.addLayout(lay_ligne)


        self.table_historique.setRowCount(0)
        cursor.execute("""
            SELECT m.date, j.nom as jeu, 
            CASE WHEN m.joueur1_id = ? THEN j2.surnom ELSE j1.surnom END as opp,
            CASE WHEN m.joueur1_id = ? THEN m.resultat_j1 ELSE m.resultat_j2 END as res
            FROM matchs m 
            JOIN jeux j ON m.jeu_id = j.id
            JOIN joueurs j1 ON m.joueur1_id = j1.id 
            JOIN joueurs j2 ON m.joueur2_id = j2.id
            WHERE m.joueur1_id = ? OR m.joueur2_id = ? 
            ORDER BY m.date DESC LIMIT 20
        """, (self.current_player_id, self.current_player_id, self.current_player_id, self.current_player_id))
        
        for i, match in enumerate(cursor.fetchall()):
            self.table_historique.insertRow(i)
            self.table_historique.setItem(i, 0, QTableWidgetItem(str(match['date'])[:10]))
            self.table_historique.setItem(i, 1, QTableWidgetItem(match['jeu']))
            self.table_historique.setItem(i, 2, QTableWidgetItem(match['opp']))
            
            res_item = QTableWidgetItem(match['res'])
            if 'Victoire' in match['res']:
                res_item.setForeground(Qt.GlobalColor.green)
            else:
                res_item.setForeground(Qt.GlobalColor.white)
            self.table_historique.setItem(i, 3, res_item)

        self.setStyleSheet(self.styleSheet())
        conn.close()

    def _ouvrir_coffre(self):
        preview_data = self.mechanics.generate_rewards_preview(self.current_player_id)
        if preview_data and preview_data['rapport']:
            dialog = RewardDialog(self, preview_data)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.mechanics.confirm_rewards_claim(self.current_player_id, preview_data)
            
            self._load_profil()

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            #page_title { color: #00f3ff; font-family: 'Orbitron'; font-size: 26px; }
            
            #frame_identite { background: rgba(20, 25, 40, 0.8); border: 1px solid #bc13fe; border-radius: 15px; padding: 10px; }
            #lbl_nom { color: white; font-family: 'Orbitron'; font-size: 24px; font-weight: bold; margin-top: 10px; }
            #lbl_rang { color: #FFD700; font-family: 'Orbitron'; font-size: 16px; font-weight: bold; margin-bottom: 5px; }
            #lbl_xp { color: #00f3ff; font-family: 'Rajdhani'; font-size: 18px; font-weight: bold; }
            
            #badge_niveau { background: rgba(188, 19, 254, 0.1); border: 1px solid #bc13fe; border-radius: 8px; }
            #lbl_niv_titre { color: #bc13fe; font-family: 'Orbitron'; font-size: 18px; font-weight: bold; }
            
            #image_profil { border: 2px solid #00f3ff; border-radius: 10px; background-color: #050505; }
            
            #btn_coffre_actif { background-color: rgba(255, 215, 0, 0.15); border: 2px solid #FFD700; border-radius: 40px; }
            #btn_coffre_inactif { background: transparent; border: 2px dashed #333333; border-radius: 30px; }
            
            #stat_card { background: rgba(20, 25, 40, 0.8); border: 1px solid rgba(0, 243, 255, 0.3); border-radius: 10px; padding: 10px; }
            #stat_value { color: white; font-family: 'Rajdhani'; font-size: 18px; font-weight: bold; padding-left: 10px; }
            #stat_value_large { color: white; font-family: 'Orbitron'; font-size: 24px; font-weight: bold; padding-left: 10px; }
            
            #bar_global { background-color: #333; border-radius: 4px; }
            #bar_global::chunk { background-color: #FFD700; border-radius: 4px; }
            
            QComboBox { background-color: #141928; color: white; border: 1px solid #00f3ff; border-radius: 5px; padding: 5px; font-family: 'Rajdhani'; font-size: 16px; }
            QComboBox QAbstractItemView { background-color: #141928; color: white; selection-background-color: #bc13fe; }
            
            QTableWidget { background: #050505; color: white; font-family: 'Rajdhani'; font-size: 14px; border: 1px solid rgba(0, 243, 255, 0.2); }
            QHeaderView::section { background-color: #141928; color: #00f3ff; font-weight: bold; border: none; padding: 5px; }
            
            QProgressBar { background-color: #111; border-radius: 5px; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff9100, stop:1 #ffe600); border-radius: 5px; }
            QToolTip { background-color: #141928; color: #FFD700; border: 1px solid #FFD700; font-family: 'Rajdhani'; font-size: 14px; }
        """)
# <VALIDATED>