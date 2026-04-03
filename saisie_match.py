# <VALIDATED>
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
                             QComboBox, QPushButton, QFrame, QRadioButton, QButtonGroup, 
                             QGridLayout, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from datetime import datetime
import qtawesome as qta
from controllers.league_mechanics import LeagueMechanics

class SaisieMatchPanel(QWidget):
    """
    Interface de saisie des résultats.
    Intègre les Matchs 1v1 (Standard, Boss, Contrats), le mode 2v2 et le Multijoueur.
    """

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.mechanics = LeagueMechanics(self.db)
        self.setObjectName("saisie_panel")
        self.current_boss_data = None
        
        self._setup_ui()
        self._apply_stylesheet()

    def showEvent(self, event):
        self._refresh_data()
        super().showEvent(event)

    def _refresh_data(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT nom FROM jeux WHERE actif = 1 ORDER BY nom ASC")
        jeux = [row["nom"] for row in cursor.fetchall()]
        conn.close()

        for combo in [self.combo_jeu_1v1, self.combo_jeu_2v2, self.combo_jeu_multi]:
            current_game = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(jeux)
            idx = combo.findText(current_game)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            combo.blockSignals(False)

        # Force la mise à jour des joueurs selon le jeu par défaut sélectionné
        self._on_jeu_1v1_changed()
        self._on_jeu_2v2_changed()
        self._on_jeu_multi_changed()

    def _update_player_combos(self, combo_jeu, combos_joueurs):
        """Filtre dynamiquement les listes déroulantes de joueurs selon le jeu."""
        nom_jeu = combo_jeu.currentText()
        if not nom_jeu:
            return

        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # On cherche uniquement les joueurs inscrits à ce jeu précis
        cursor.execute("""
            SELECT j.surnom 
            FROM joueurs j
            JOIN joueurs_jeux jj ON j.id = jj.joueur_id
            JOIN jeux jeu ON jj.jeu_id = jeu.id
            WHERE jeu.nom = ? AND j.surnom IS NOT NULL AND j.surnom != ''
            ORDER BY j.surnom ASC
        """, (nom_jeu,))
            
        pseudos = [row["surnom"] for row in cursor.fetchall()]
        conn.close()

        for combo in combos_joueurs:
            current_text = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Choisir un joueur...")
            combo.addItems(pseudos)
            
            idx = combo.findText(current_text)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            else:
                combo.setCurrentIndex(0)
            combo.blockSignals(False)

    def _on_jeu_1v1_changed(self):
        if hasattr(self, 'combo_p1') and hasattr(self, 'combo_p2'):
            self._update_player_combos(self.combo_jeu_1v1, [self.combo_p1, self.combo_p2])
            self._check_events_1v1()

    def _on_jeu_2v2_changed(self):
        if hasattr(self, 'combo_t1_p1'):
            self._update_player_combos(self.combo_jeu_2v2, [self.combo_t1_p1, self.combo_t1_p2, self.combo_t2_p1, self.combo_t2_p2])

    def _on_jeu_multi_changed(self):
        if hasattr(self, 'combo_gagnant') and hasattr(self, 'combos_multi_others'):
            combos = [self.combo_gagnant] + self.combos_multi_others
            self._update_player_combos(self.combo_jeu_multi, combos)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("saisie_tabs")
        
        self.tab_1v1 = QWidget()
        self._setup_tab_1v1()
        self.tabs.addTab(self.tab_1v1, "Match 1 VS 1")

        self.tab_2v2 = QWidget()
        self._setup_tab_2v2()
        self.tabs.addTab(self.tab_2v2, "Match 2 VS 2")

        self.tab_multi = QWidget()
        self._setup_tab_multi()
        self.tabs.addTab(self.tab_multi, "Multijoueur (3+)")

        layout.addWidget(self.tabs)

    def _setup_tab_1v1(self):
        layout = QVBoxLayout(self.tab_1v1)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addStretch(1)

        frame_jeu = QFrame()
        frame_jeu.setStyleSheet("background-color: rgba(20, 25, 40, 0.6); border: 1px solid rgba(0, 243, 255, 0.3); border-radius: 10px; padding: 15px;")
        layout_jeu = QVBoxLayout(frame_jeu)
        layout_jeu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.combo_jeu_1v1 = QComboBox()
        self.combo_jeu_1v1.setMinimumWidth(300)
        self.combo_jeu_1v1.currentIndexChanged.connect(self._on_jeu_1v1_changed)
        layout_jeu.addWidget(self.combo_jeu_1v1)
        
        self.lbl_event_alert = QLabel("")
        self.lbl_event_alert.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_event_alert.hide()
        layout_jeu.addWidget(self.lbl_event_alert)
        
        layout.addWidget(frame_jeu, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)

        layout_vs_global = QHBoxLayout()
        layout_vs_global.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        frame_p1 = QFrame()
        frame_p1.setStyleSheet("background-color: rgba(20, 25, 40, 0.6); border: 1px solid rgba(0, 243, 255, 0.3); border-radius: 10px; padding: 20px;")
        layout_p1 = QVBoxLayout(frame_p1)
        lbl_p1 = QLabel("JOUEUR 1")
        lbl_p1.setStyleSheet("color: white; font-family: 'Orbitron'; font-weight: bold; border: none; background: transparent; font-size: 18px;")
        self.combo_p1 = QComboBox()
        self.combo_p1.currentIndexChanged.connect(self._check_events_1v1)
        layout_p1.addWidget(lbl_p1, alignment=Qt.AlignmentFlag.AlignCenter)
        layout_p1.addWidget(self.combo_p1)
        
        lbl_vs = QLabel("VS")
        lbl_vs.setObjectName("lbl_vs")
        lbl_vs.setStyleSheet("color: #ff0055; font-family: 'Orbitron'; font-size: 36px; font-weight: 900; margin: 0px 30px;")
        
        frame_p2 = QFrame()
        frame_p2.setStyleSheet("background-color: rgba(20, 25, 40, 0.6); border: 1px solid rgba(0, 243, 255, 0.3); border-radius: 10px; padding: 20px;")
        layout_p2 = QVBoxLayout(frame_p2)
        lbl_p2 = QLabel("JOUEUR 2")
        lbl_p2.setStyleSheet("color: white; font-family: 'Orbitron'; font-weight: bold; border: none; background: transparent; font-size: 18px;")
        self.combo_p2 = QComboBox()
        self.combo_p2.currentIndexChanged.connect(self._check_events_1v1)
        layout_p2.addWidget(lbl_p2, alignment=Qt.AlignmentFlag.AlignCenter)
        layout_p2.addWidget(self.combo_p2)

        layout_vs_global.addWidget(frame_p1)
        layout_vs_global.addWidget(lbl_vs)
        layout_vs_global.addWidget(frame_p2)
        layout.addLayout(layout_vs_global)
        layout.addStretch(1)

        frame_scores = QFrame()
        frame_scores.setStyleSheet("background-color: rgba(20, 25, 40, 0.6); border: 1px solid rgba(0, 243, 255, 0.3); border-radius: 10px; padding: 15px;")
        layout_scores_main = QVBoxLayout(frame_scores)
        
        lbl_score_titre = QLabel("RÉSULTAT DU MATCH")
        lbl_score_titre.setStyleSheet("color: #00f3ff; font-family: 'Orbitron'; font-weight: bold; font-size: 16px; border: none; background: transparent;")
        layout_scores_main.addWidget(lbl_score_titre, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout_scores_btns = QHBoxLayout()
        self.group_scores = QButtonGroup(self)
        
        for score in ["2-0", "2-1", "1-0", "1-1", "0-1", "1-2", "0-2"]:
            btn = QRadioButton(score)
            btn.setStyleSheet("border: none; background: transparent;")
            self.group_scores.addButton(btn)
            layout_scores_btns.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            
        layout_scores_main.addLayout(layout_scores_btns)
        layout.addWidget(frame_scores, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(2)

        self.btn_valider_1v1 = QPushButton("VALIDER LE MATCH")
        self.btn_valider_1v1.setObjectName("btn_valider")
        self.btn_valider_1v1.clicked.connect(self._valider_1v1)
        layout.addWidget(self.btn_valider_1v1, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)

    def _setup_tab_2v2(self):
        layout = QVBoxLayout(self.tab_2v2)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addStretch(1)

        frame_jeu = QFrame()
        frame_jeu.setStyleSheet("background-color: rgba(20, 25, 40, 0.6); border: 1px solid rgba(0, 243, 255, 0.3); border-radius: 10px; padding: 15px;")
        layout_jeu = QVBoxLayout(frame_jeu)
        layout_jeu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.combo_jeu_2v2 = QComboBox()
        self.combo_jeu_2v2.setMinimumWidth(300)
        self.combo_jeu_2v2.currentIndexChanged.connect(self._on_jeu_2v2_changed)
        layout_jeu.addWidget(self.combo_jeu_2v2)
        layout.addWidget(frame_jeu, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)

        layout_vs_global = QHBoxLayout()
        layout_vs_global.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        frame_t1 = QFrame()
        frame_t1.setStyleSheet("background-color: rgba(20, 25, 40, 0.6); border: 1px solid rgba(0, 243, 255, 0.3); border-radius: 10px; padding: 20px;")
        layout_t1 = QVBoxLayout(frame_t1)
        lbl_eq1 = QLabel("ÉQUIPE 1")
        lbl_eq1.setStyleSheet("color: #00f3ff; font-family: 'Orbitron'; font-weight: bold; font-size: 20px; border: none; background: transparent;")
        self.combo_t1_p1 = QComboBox()
        self.combo_t1_p2 = QComboBox()
        layout_t1.addWidget(lbl_eq1, alignment=Qt.AlignmentFlag.AlignCenter)
        layout_t1.addSpacing(10)
        layout_t1.addWidget(self.combo_t1_p1)
        layout_t1.addWidget(self.combo_t1_p2)
        
        lbl_vs = QLabel("VS")
        lbl_vs.setObjectName("lbl_vs")
        lbl_vs.setStyleSheet("color: #ff0055; font-family: 'Orbitron'; font-size: 36px; font-weight: 900; margin: 0px 30px;")

        frame_t2 = QFrame()
        frame_t2.setStyleSheet("background-color: rgba(20, 25, 40, 0.6); border: 1px solid rgba(0, 243, 255, 0.3); border-radius: 10px; padding: 20px;")
        layout_t2 = QVBoxLayout(frame_t2)
        lbl_eq2 = QLabel("ÉQUIPE 2")
        lbl_eq2.setStyleSheet("color: #00f3ff; font-family: 'Orbitron'; font-weight: bold; font-size: 20px; border: none; background: transparent;")
        self.combo_t2_p1 = QComboBox()
        self.combo_t2_p2 = QComboBox()
        layout_t2.addWidget(lbl_eq2, alignment=Qt.AlignmentFlag.AlignCenter)
        layout_t2.addSpacing(10)
        layout_t2.addWidget(self.combo_t2_p1)
        layout_t2.addWidget(self.combo_t2_p2)
        
        layout_vs_global.addWidget(frame_t1)
        layout_vs_global.addWidget(lbl_vs)
        layout_vs_global.addWidget(frame_t2)
        layout.addLayout(layout_vs_global)
        layout.addStretch(1)

        frame_scores = QFrame()
        frame_scores.setStyleSheet("background-color: rgba(20, 25, 40, 0.6); border: 1px solid rgba(0, 243, 255, 0.3); border-radius: 10px; padding: 15px;")
        layout_scores_main = QVBoxLayout(frame_scores)
        
        lbl_score_titre = QLabel("RÉSULTAT DU MATCH")
        lbl_score_titre.setStyleSheet("color: #00f3ff; font-family: 'Orbitron'; font-weight: bold; font-size: 16px; border: none; background: transparent;")
        layout_scores_main.addWidget(lbl_score_titre, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout_scores_btns = QHBoxLayout()
        self.group_scores_2v2 = QButtonGroup(self)
        
        for score in ["2-0", "2-1", "1-0", "1-1", "0-1", "1-2", "0-2"]:
            btn = QRadioButton(score)
            btn.setStyleSheet("border: none; background: transparent;")
            self.group_scores_2v2.addButton(btn)
            layout_scores_btns.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            
        layout_scores_main.addLayout(layout_scores_btns)
        layout.addWidget(frame_scores, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(2)

        btn_valider = QPushButton("VALIDER LE MATCH 2 VS 2")
        btn_valider.setObjectName("btn_valider")
        btn_valider.clicked.connect(self._valider_2v2)
        layout.addWidget(btn_valider, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)

    def _setup_tab_multi(self):
        layout = QVBoxLayout(self.tab_multi)
        layout.setContentsMargins(20, 40, 20, 40)
        layout.addStretch(1)

        frame_multi = QFrame()
        frame_multi.setStyleSheet("background-color: rgba(20, 25, 40, 0.6); border: 1px solid rgba(0, 243, 255, 0.3); border-radius: 10px; padding: 20px;")
        frame_layout = QVBoxLayout(frame_multi)
        frame_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.combo_jeu_multi = QComboBox()
        self.combo_jeu_multi.currentIndexChanged.connect(self._on_jeu_multi_changed)
        frame_layout.addWidget(self.combo_jeu_multi, alignment=Qt.AlignmentFlag.AlignCenter)
        frame_layout.addSpacing(30)

        row_winner = QHBoxLayout()
        lbl_winner = QLabel("JOUEUR 1 (GAGNANT) :")
        lbl_winner.setStyleSheet("color: #00ff9d; font-family: 'Orbitron'; font-weight: bold; font-size: 22px; border: none; background: transparent;")
        self.combo_gagnant = QComboBox()
        row_winner.addWidget(lbl_winner)
        row_winner.addWidget(self.combo_gagnant)
        frame_layout.addLayout(row_winner)
        frame_layout.addSpacing(30)

        grid_others = QGridLayout()
        grid_others.setSpacing(15)
        self.combos_multi_others = []
        for i in range(5):
            layout_perdant = QVBoxLayout()
            lbl_perdant = QLabel(f"JOUEUR {i+2}")
            lbl_perdant.setStyleSheet("color: white; font-family: 'Orbitron'; font-weight: bold; border: none; background: transparent; font-size: 16px;")
            cb = QComboBox()
            layout_perdant.addWidget(lbl_perdant, alignment=Qt.AlignmentFlag.AlignCenter)
            layout_perdant.addWidget(cb)
            
            self.combos_multi_others.append(cb)
            grid_others.addLayout(layout_perdant, i // 3, i % 3)
        
        frame_layout.addLayout(grid_others)
        layout.addWidget(frame_multi)
        layout.addStretch(2)

        btn_valider = QPushButton("VALIDER LE MATCH MULTIJOUEUR")
        btn_valider.setObjectName("btn_valider")
        btn_valider.clicked.connect(self._valider_multi)
        layout.addWidget(btn_valider, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)

    def _check_events_1v1(self):
        p1 = self.combo_p1.currentText()
        p2 = self.combo_p2.currentText()
        jeu_nom = self.combo_jeu_1v1.currentText()
        
        self.lbl_event_alert.hide()
        self.current_boss_data = None
        self.btn_valider_1v1.setText("VALIDER LE MATCH")
        self.btn_valider_1v1.setStyleSheet("")

        if "Choisir" in p1 or "Choisir" in p2 or p1 == p2:
            return

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM joueurs WHERE surnom = ?", (p1,))
        p1_id = cursor.fetchone()['id']
        cursor.execute("SELECT id FROM joueurs WHERE surnom = ?", (p2,))
        p2_id = cursor.fetchone()['id']
        cursor.execute("SELECT id FROM jeux WHERE nom = ?", (jeu_nom,))
        jeu_row = cursor.fetchone()
        
        if not jeu_row:
            conn.close()
            return
        jeu_id = jeu_row['id']

        cursor.execute("SELECT * FROM event_tueurs WHERE chasseur_id = ? AND cible_id = ? AND jeu_id = ? AND statut = 'ACTIF'", (p1_id, p2_id, jeu_id))
        contrat_p1 = cursor.fetchone()
        cursor.execute("SELECT * FROM event_tueurs WHERE chasseur_id = ? AND cible_id = ? AND jeu_id = ? AND statut = 'ACTIF'", (p2_id, p1_id, jeu_id))
        contrat_p2 = cursor.fetchone()

        if contrat_p1 or contrat_p2:
            self.lbl_event_alert.setText("🎯 CONTRAT ACTIF : Si le chasseur gagne, le contrat est rempli !")
            self.lbl_event_alert.setStyleSheet("color: #ffea00; font-family: 'Orbitron'; font-size: 16px; font-weight: bold; background: rgba(255, 234, 0, 0.1); border: 1px solid #ffea00; padding: 10px; border-radius: 5px;")
            self.lbl_event_alert.show()
            conn.close()
            return

        cursor.execute("SELECT * FROM event_boss WHERE (joueur_id = ? OR joueur_id = ?) AND jeu_id = ? AND statut = 'ACTIF'", (p1_id, p2_id, jeu_id))
        boss = cursor.fetchone()
        
        if boss:
            boss_id_joueur = boss['joueur_id']
            challenger_id = p2_id if boss_id_joueur == p1_id else p1_id
            
            cursor.execute("SELECT * FROM event_boss_essais WHERE joueur_id = ? AND boss_id = ?", (challenger_id, boss['id']))
            if cursor.fetchone():
                self.lbl_event_alert.setText("⛔ LE CHALLENGER A DÉJÀ TENTÉ SA CHANCE CETTE SEMAINE !")
                self.lbl_event_alert.setStyleSheet("color: #ff0055; font-family: 'Orbitron'; font-size: 16px; font-weight: bold; background: rgba(255, 0, 85, 0.1); border: 1px solid #ff0055; padding: 10px; border-radius: 5px;")
                self.lbl_event_alert.show()
                self.btn_valider_1v1.setEnabled(False)
            else:
                self.current_boss_data = {'id': boss['id'], 'boss_joueur_id': boss_id_joueur, 'challenger_id': challenger_id}
                boss_pseudo = p1 if boss_id_joueur == p1_id else p2
                self.lbl_event_alert.setText(f"🐉 COMBAT DE BOSS : {boss_pseudo.upper()} DÉFEND SON TERRITOIRE !")
                self.lbl_event_alert.setStyleSheet("color: #ff0055; font-family: 'Orbitron'; font-size: 16px; font-weight: bold; background: rgba(255, 0, 85, 0.1); border: 1px solid #ff0055; padding: 10px; border-radius: 5px;")
                self.lbl_event_alert.show()
                self.btn_valider_1v1.setText("VALIDER LE COMBAT DE BOSS")
                self.btn_valider_1v1.setStyleSheet("background-color: rgba(255, 0, 85, 0.2); border: 2px solid #ff0055; color: white;")
                self.btn_valider_1v1.setEnabled(True)
        else:
            self.btn_valider_1v1.setEnabled(True)
            
        conn.close()

# <VALIDATED>
    def _valider_1v1(self):
        jeu_nom = self.combo_jeu_1v1.currentText()
        p1_nom = self.combo_p1.currentText()
        p2_nom = self.combo_p2.currentText()
        
        btn_score = self.group_scores.checkedButton()
        
        if not btn_score or "Choisir" in p1_nom or "Choisir" in p2_nom or "Choisir" in jeu_nom or p1_nom == p2_nom:
            return

        score = btn_score.text()
        s1, s2 = map(int, score.split('-'))
        res_p1 = f"Victoire {score}" if s1 > s2 else f"Égalité {score}" if s1 == s2 else f"Défaite {score}"
        res_p2 = f"Victoire {s2}-{s1}" if s2 > s1 else f"Égalité {s2}-{s1}" if s2 == s1 else f"Défaite {s2}-{s1}"

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, xp_total FROM joueurs WHERE surnom = ?", (p1_nom,))
        j1 = cursor.fetchone()
        cursor.execute("SELECT id, xp_total FROM joueurs WHERE surnom = ?", (p2_nom,))
        j2 = cursor.fetchone()
        cursor.execute("SELECT id FROM jeux WHERE nom = ?", (jeu_nom,))
        jeu_id = cursor.fetchone()['id']

        est_boss = (self.current_boss_data is not None)
        
        aujourdhui = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM matchs WHERE (joueur1_id = ? OR joueur2_id = ?) AND date >= ?", (j1['id'], j1['id'], aujourdhui))
        j1_premier_match = cursor.fetchone()[0] == 0
        cursor.execute("SELECT COUNT(*) FROM matchs WHERE (joueur1_id = ? OR joueur2_id = ?) AND date >= ?", (j2['id'], j2['id'], aujourdhui))
        j2_premier_match = cursor.fetchone()[0] == 0

        cursor.execute("SELECT COUNT(*) FROM matchs WHERE ((joueur1_id = ? AND joueur2_id = ?) OR (joueur1_id = ? AND joueur2_id = ?)) AND date >= ?", (j1['id'], j2['id'], j2['id'], j1['id'], aujourdhui))
        premiere_rencontre = cursor.fetchone()[0] == 0

        xp_j1 = self.mechanics.calculate_xp(s1, s2, j1['xp_total'], j2['xp_total'], est_boss and j1['id'] == self.current_boss_data['challenger_id'], False, j1_premier_match, premiere_rencontre)
        xp_j2 = self.mechanics.calculate_xp(s2, s1, j2['xp_total'], j1['xp_total'], est_boss and j2['id'] == self.current_boss_data['challenger_id'], False, j2_premier_match, premiere_rencontre)

        cursor.execute("""
            INSERT INTO matchs (joueur1_id, joueur2_id, jeu_id, resultat_j1, resultat_j2, xp_j1, xp_j2, est_boost) 
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (j1['id'], j2['id'], jeu_id, res_p1, res_p2, xp_j1, xp_j2))

        new_xp_j1 = j1['xp_total'] + xp_j1
        new_xp_j2 = j2['xp_total'] + xp_j2

        cursor.execute("UPDATE joueurs SET xp_total = ? WHERE id = ?", (new_xp_j1, j1['id']))
        cursor.execute("UPDATE joueurs SET xp_total = ? WHERE id = ?", (new_xp_j2, j2['id']))

        conn.commit()
        conn.close()

        self.mechanics.check_progression_rewards(j1['id'], j1['xp_total'], new_xp_j1)
        self.mechanics.check_progression_rewards(j2['id'], j2['xp_total'], new_xp_j2)
        self.mechanics.evaluer_etoiles_direct(j1['id'])
        self.mechanics.evaluer_etoiles_direct(j2['id'])

        if est_boss:
            vainqueur_id = j1['id'] if s1 > s2 else j2['id'] if s2 > s1 else None
            if vainqueur_id:
                victoire_joueur = (vainqueur_id == self.current_boss_data['challenger_id'])
                self.mechanics.executer_combat_boss(self.current_boss_data['challenger_id'], self.current_boss_data['id'], victoire_joueur)
        else:
            vainqueur_id = j1['id'] if s1 > s2 else j2['id'] if s2 > s1 else None
            perdant_id = j2['id'] if s1 > s2 else j1['id'] if s2 > s1 else None
            if vainqueur_id and perdant_id:
                self.mechanics.verifier_et_valider_contrat(vainqueur_id, perdant_id, jeu_id)

        # --- NOUVEAU MESSAGE FLOTTANT VERT ---
        self.msg_flottant_1v1 = QLabel(f"✅ MATCH VALIDÉ ! ({p1_nom} +{xp_j1} XP | {p2_nom} +{xp_j2} XP)", self)
        self.msg_flottant_1v1.setStyleSheet("background-color: rgba(0, 255, 157, 0.9); color: black; font-family: 'Orbitron'; font-size: 22px; font-weight: bold; padding: 20px; border-radius: 10px; border: 2px solid white;")
        self.msg_flottant_1v1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg_flottant_1v1.adjustSize()
        self.msg_flottant_1v1.move((self.width() - self.msg_flottant_1v1.width()) // 2, (self.height() - self.msg_flottant_1v1.height()) // 2)
        self.msg_flottant_1v1.show()
        
        QTimer.singleShot(2000, self.msg_flottant_1v1.deleteLater)

        self.group_scores.setExclusive(False)
        btn_score.setChecked(False)
        self.group_scores.setExclusive(True)
        self._check_events_1v1()

    def _valider_2v2(self):
        jeu_nom = self.combo_jeu_2v2.currentText()
        t1_p1 = self.combo_t1_p1.currentText()
        t1_p2 = self.combo_t1_p2.currentText()
        t2_p1 = self.combo_t2_p1.currentText()
        t2_p2 = self.combo_t2_p2.currentText()
        
        btn_score = self.group_scores_2v2.checkedButton()

        joueurs = [t1_p1, t1_p2, t2_p1, t2_p2]
        if not btn_score or "Choisir" in jeu_nom or any("Choisir" in j for j in joueurs) or len(set(joueurs)) != 4:
            return

        score = btn_score.text()
        s1, s2 = map(int, score.split('-'))

        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM jeux WHERE nom = ?", (jeu_nom,))
        jeu_id = cursor.fetchone()['id']

        ids = {}
        for nom in joueurs:
            cursor.execute("SELECT id, xp_total FROM joueurs WHERE surnom = ?", (nom,))
            ids[nom] = cursor.fetchone()

        aujourdhui = datetime.now().strftime('%Y-%m-%d')
        operations_joueurs = []

        for joueur_nom in joueurs:
            j_id = ids[joueur_nom]['id']
            j_xp_actuel = ids[joueur_nom]['xp_total']
            
            cursor.execute("SELECT COUNT(*) FROM matchs WHERE (joueur1_id = ? OR joueur2_id = ?) AND date >= ?", (j_id, j_id, aujourdhui))
            premier_match = cursor.fetchone()[0] == 0
            
            est_t1 = joueur_nom in [t1_p1, t1_p2]
            score_eq = s1 if est_t1 else s2
            score_adv = s2 if est_t1 else s1
            
            xp_gain = self.mechanics.calculate_xp_2v2(score_eq, score_adv, premier_match, False)
            new_xp = j_xp_actuel + xp_gain
            
            cursor.execute("UPDATE joueurs SET xp_total = ? WHERE id = ?", (new_xp, j_id))
            operations_joueurs.append({'id': j_id, 'old_xp': j_xp_actuel, 'new_xp': new_xp})

        res_t1 = f"Victoire {score}" if s1 > s2 else f"Égalité {score}" if s1 == s2 else f"Défaite {score}"
        res_t2 = f"Victoire {s2}-{s1}" if s2 > s1 else f"Égalité {s2}-{s1}" if s2 == s1 else f"Défaite {s2}-{s1}"

        cursor.execute("""
            INSERT INTO matchs (joueur1_id, joueur2_id, jeu_id, type_match, resultat_j1, resultat_j2) 
            VALUES (?, ?, ?, '2v2', ?, ?)
        """, (ids[t1_p1]['id'], ids[t2_p1]['id'], jeu_id, res_t1, res_t2))
        
        conn.commit()
        conn.close()

        for op in operations_joueurs:
            self.mechanics.check_progression_rewards(op['id'], op['old_xp'], op['new_xp'])
            self.mechanics.evaluer_etoiles_direct(op['id'])

        # --- NOUVEAU MESSAGE FLOTTANT VERT ---
        self.msg_flottant_2v2 = QLabel("✅ MATCH 2 VS 2 VALIDÉ !", self)
        self.msg_flottant_2v2.setStyleSheet("background-color: rgba(0, 255, 157, 0.9); color: black; font-family: 'Orbitron'; font-size: 22px; font-weight: bold; padding: 20px; border-radius: 10px; border: 2px solid white;")
        self.msg_flottant_2v2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg_flottant_2v2.adjustSize()
        self.msg_flottant_2v2.move((self.width() - self.msg_flottant_2v2.width()) // 2, (self.height() - self.msg_flottant_2v2.height()) // 2)
        self.msg_flottant_2v2.show()
        
        QTimer.singleShot(2000, self.msg_flottant_2v2.deleteLater)

        self.group_scores_2v2.setExclusive(False)
        btn_score.setChecked(False)
        self.group_scores_2v2.setExclusive(True)

    def _valider_multi(self):
        jeu_nom = self.combo_jeu_multi.currentText()
        gagnant = self.combo_gagnant.currentText()
        
        perdants = [cb.currentText() for cb in self.combos_multi_others if "Choisir" not in cb.currentText()]
        tous_joueurs = [gagnant] + perdants

        if "Choisir" in jeu_nom or "Choisir" in gagnant or not perdants or len(set(tous_joueurs)) != len(tous_joueurs):
            return

        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM jeux WHERE nom = ?", (jeu_nom,))
        jeu_id = cursor.fetchone()['id']

        aujourdhui = datetime.now().strftime('%Y-%m-%d')
        operations_joueurs = []
        
        for nom in tous_joueurs:
            cursor.execute("SELECT id, xp_total FROM joueurs WHERE surnom = ?", (nom,))
            j = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(*) FROM matchs WHERE (joueur1_id = ? OR joueur2_id = ?) AND date >= ?", (j['id'], j['id'], aujourdhui))
            premier_match = cursor.fetchone()[0] == 0
            
            est_gagnant = (nom == gagnant)
            xp_gain = self.mechanics.calculate_xp_multi(est_gagnant, len(perdants), premier_match, False)
            
            new_xp = j['xp_total'] + xp_gain
            cursor.execute("UPDATE joueurs SET xp_total = ? WHERE id = ?", (new_xp, j['id']))
            operations_joueurs.append({'id': j['id'], 'old_xp': j['xp_total'], 'new_xp': new_xp})

        cursor.execute("SELECT id FROM joueurs WHERE surnom = ?", (gagnant,))
        g_id = cursor.fetchone()['id']
        cursor.execute("SELECT id FROM joueurs WHERE surnom = ?", (perdants[0],))
        p_id = cursor.fetchone()['id']

        cursor.execute("""
            INSERT INTO matchs (joueur1_id, joueur2_id, jeu_id, type_match, resultat_j1, resultat_j2) 
            VALUES (?, ?, ?, 'Multi', 'Victoire Multi', 'Défaite Multi')
        """, (g_id, p_id, jeu_id))

        conn.commit()
        conn.close()

        for op in operations_joueurs:
            self.mechanics.check_progression_rewards(op['id'], op['old_xp'], op['new_xp'])
            self.mechanics.evaluer_etoiles_direct(op['id'])

        # --- NOUVEAU MESSAGE FLOTTANT VERT ---
        self.msg_flottant_multi = QLabel("✅ MATCH MULTIJOUEUR VALIDÉ !", self)
        self.msg_flottant_multi.setStyleSheet("background-color: rgba(0, 255, 157, 0.9); color: black; font-family: 'Orbitron'; font-size: 22px; font-weight: bold; padding: 20px; border-radius: 10px; border: 2px solid white;")
        self.msg_flottant_multi.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg_flottant_multi.adjustSize()
        self.msg_flottant_multi.move((self.width() - self.msg_flottant_multi.width()) // 2, (self.height() - self.msg_flottant_multi.height()) // 2)
        self.msg_flottant_multi.show()
        
        QTimer.singleShot(2000, self.msg_flottant_multi.deleteLater)
# </VALIDATED>
    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QComboBox { background-color: #141928; color: white; border: 1px solid #00f3ff; border-radius: 5px; padding: 12px; font-family: 'Rajdhani'; font-size: 20px; min-width: 350px; }
            
            QRadioButton { color: white; font-family: 'Orbitron'; font-size: 26px; font-weight: bold; margin: 10px; }
            QRadioButton:hover { color: #bc13fe; }
            QRadioButton::indicator { width: 28px; height: 28px; border-radius: 14px; border: 2px solid rgba(0, 243, 255, 0.4); }
            QRadioButton::indicator:checked { background-color: #bc13fe; border: 2px solid #bc13fe; }
            QRadioButton::indicator:hover { border: 2px solid #00f3ff; }
            
            #btn_valider { background-color: transparent; color: #00f3ff; font-family: 'Orbitron'; font-size: 26px; font-weight: bold; padding: 20px 80px; border: 2px solid #00f3ff; border-radius: 10px; margin-top: 10px;}
            #btn_valider:hover { background-color: rgba(0, 243, 255, 0.15); border: 2px solid #bc13fe; color: #bc13fe; }
            
            QTabWidget::pane { border: 1px solid rgba(0, 243, 255, 0.3); border-radius: 10px; background: rgba(10, 10, 26, 0.8); }
            QTabBar::tab { background: #141928; color: #aaa; padding: 15px 30px; font-family: 'Orbitron'; font-size: 16px; font-weight: bold; border-top-left-radius: 10px; border-top-right-radius: 10px; margin-right: 2px; border: 1px solid rgba(0, 243, 255, 0.3); border-bottom: none; }
            QTabBar::tab:selected { background: #00f3ff; color: #050505; border: 1px solid #00f3ff; }
            QTabBar::tab:hover:!selected { background: rgba(188, 19, 254, 0.3); color: white; }
        """)
# <VALIDATED>