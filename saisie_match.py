# <VALIDATED>
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
                             QComboBox, QPushButton, QFrame, QRadioButton, QButtonGroup, 
                             QGridLayout, QMessageBox, QDialog)
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
        
        cursor.execute("SELECT surnom FROM joueurs WHERE surnom IS NOT NULL AND surnom != '' ORDER BY surnom ASC")
        pseudos = [row["surnom"] for row in cursor.fetchall()]
        
        cursor.execute("SELECT nom FROM jeux WHERE actif = 1 ORDER BY nom ASC")
        jeux = [row["nom"] for row in cursor.fetchall()]
        conn.close()

        for combo in [self.combo_p1, self.combo_p2, self.combo_t1_p1, self.combo_t1_p2, self.combo_t2_p1, self.combo_t2_p2]:
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Choisir un joueur...")
            combo.addItems(pseudos)
            combo.blockSignals(False)

        for combo in [self.combo_jeu_1v1, self.combo_jeu_2v2, self.combo_jeu_multi]:
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Choisir le jeu...")
            combo.addItems(jeux)
            combo.blockSignals(False)

        self.combo_gagnant.clear()
        self.combo_gagnant.addItem("Choisir le gagnant...")
        self.combo_gagnant.addItems(pseudos)
        
        for cb in self.combos_multi_others:
            cb.clear()
            cb.addItem("Choisir un joueur...")
            cb.addItems(pseudos)
                
        self._check_events_1v1()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(20)

        title = QLabel("ENREGISTRER UN MATCH")
        title.setObjectName("page_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.tabs = QTabWidget()
        
        self.tab_1v1 = QWidget()
        self._setup_tab_1v1()
        self.tabs.addTab(self.tab_1v1, "Match 1 VS 1")

        self.tab_2v2 = QWidget()
        self._setup_tab_2v2()
        self.tabs.addTab(self.tab_2v2, "Match 2 VS 2")

        self.tab_multi = QWidget()
        self._setup_tab_multi()
        self.tabs.addTab(self.tab_multi, "Match Multijoueur")
        
        layout.addWidget(self.tabs)

        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setObjectName("lbl_feedback")
        self.lbl_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_feedback.hide()
        layout.addWidget(self.lbl_feedback)

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
        self.combo_jeu_1v1.currentIndexChanged.connect(self._check_events_1v1)
        layout_jeu.addWidget(self.combo_jeu_1v1)
        
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
        
        for score in ["2-0", "2-1", "1-1", "1-2", "0-2"]:
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
        
        for score in ["2-0", "2-1", "1-1", "1-2", "0-2"]:
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
        """Vérifie en direct si le match sélectionné est un combat de Boss valide."""
        p1_name = self.combo_p1.currentText()
        p2_name = self.combo_p2.currentText()
        jeu_name = self.combo_jeu_1v1.currentText()

        self.btn_valider_1v1.setText("VALIDER LE MATCH")
        self.btn_valider_1v1.setIcon(QIcon())
        self.btn_valider_1v1.setStyleSheet("")
        self.current_boss_data = None

        if "Choisir" in p1_name or "Choisir" in p2_name or "Choisir" in jeu_name or p1_name == p2_name:
            return

        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id FROM joueurs WHERE surnom = ?", (p1_name,))
            j1 = cursor.fetchone()
            cursor.execute("SELECT id FROM joueurs WHERE surnom = ?", (p2_name,))
            j2 = cursor.fetchone()
            cursor.execute("SELECT id FROM jeux WHERE nom = ?", (jeu_name,))
            jeu = cursor.fetchone()
            
            if not j1 or not j2 or not jeu:
                return

            cursor.execute("""
                SELECT id, joueur_id FROM event_boss 
                WHERE jeu_id = ? AND statut = 'ACTIF' AND (joueur_id = ? OR joueur_id = ?)
            """, (jeu['id'], j1['id'], j2['id']))
            boss_event = cursor.fetchone()
            
            if boss_event:
                boss_id = boss_event['joueur_id']
                challenger_id = j2['id'] if boss_id == j1['id'] else j1['id']
                
                # Vérifie si le challenger a déjà tenté sa chance
                cursor.execute("SELECT 1 FROM event_boss_essais WHERE joueur_id = ? AND boss_id = ?", (challenger_id, boss_event['id']))
                if not cursor.fetchone():
                    self.current_boss_data = {
                        'event_id': boss_event['id'],
                        'boss_id': boss_id,
                        'challenger_id': challenger_id
                    }
                    self.btn_valider_1v1.setText("  COMBAT DE BOSS")
                    self.btn_valider_1v1.setIcon(qta.icon("fa5s.dragon", color="#ff0055"))
                    self.btn_valider_1v1.setStyleSheet("background-color: rgba(255, 0, 85, 0.15); color: #ff0055; border: 2px solid #ff0055;")
        finally:
            conn.close()

    def _valider_1v1(self):
        p1_name = self.combo_p1.currentText()
        p2_name = self.combo_p2.currentText()
        jeu_name = self.combo_jeu_1v1.currentText()
        selected_button = self.group_scores.checkedButton()
        
        if "Choisir" in p1_name or "Choisir" in p2_name or p1_name == p2_name or "Choisir" in jeu_name or not selected_button:
            QMessageBox.warning(self, "Erreur", "Saisie incomplète ou joueurs identiques.")
            return

        score = selected_button.text()
        s_j1, s_j2 = map(int, score.split('-'))

        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id, xp_total FROM joueurs WHERE surnom = ?", (p1_name,))
            j1 = cursor.fetchone()
            cursor.execute("SELECT id, xp_total FROM joueurs WHERE surnom = ?", (p2_name,))
            j2 = cursor.fetchone()
            cursor.execute("SELECT id FROM jeux WHERE nom = ?", (jeu_name,))
            jeu_id = cursor.fetchone()['id']

            today = datetime.now().strftime("%Y-%m-%d")
            
            # --- 1. CALCUL DE BASE NORMAL POUR TOUS ---
            cursor.execute("SELECT COUNT(*) FROM matchs WHERE (joueur1_id = ? OR joueur2_id = ?) AND date LIKE ?", (j1['id'], j1['id'], f"{today}%"))
            is_first_match_j1 = cursor.fetchone()[0] == 0
            
            cursor.execute("SELECT COUNT(*) FROM matchs WHERE (joueur1_id = ? OR joueur2_id = ?) AND date LIKE ?", (j2['id'], j2['id'], f"{today}%"))
            is_first_match_j2 = cursor.fetchone()[0] == 0
            
            cursor.execute("SELECT COUNT(*) FROM matchs WHERE ((joueur1_id = ? AND joueur2_id = ?) OR (joueur1_id = ? AND joueur2_id = ?)) AND date LIKE ?", 
                           (j1['id'], j2['id'], j2['id'], j1['id'], f"{today}%"))
            is_first_encounter = cursor.fetchone()[0] == 0

            # Calcul 100% normal (le paramètre Boss est à False pour qu'on le gère à la main ensuite)
            xp_gain_j1 = self.mechanics.calculate_xp(s_j1, s_j2, j1['xp_total'], j2['xp_total'], False, False, is_first_match_j1, is_first_encounter)
            xp_gain_j2 = self.mechanics.calculate_xp(s_j2, s_j1, j2['xp_total'], j1['xp_total'], False, False, is_first_match_j2, is_first_encounter)

            vainqueur_id = j1['id'] if s_j1 > s_j2 else (j2['id'] if s_j2 > s_j1 else None)
            perdant_id = j2['id'] if s_j1 > s_j2 else (j1['id'] if s_j2 > s_j1 else None)
            perdant_name = p2_name if s_j1 > s_j2 else (p1_name if s_j2 > s_j1 else None)

            msg_extra = ""
            type_match_db = "1v1"
            
            # --- 2. RÉSOLUTION DES ÉVÉNEMENTS (MIEUX ISOLÉE) ---
            
            # A) Bonus Némésis Global (Si on bat sa Némésis, c'est toujours +1)
            if vainqueur_id:
                stats_vainqueur = self.mechanics.get_player_stats(vainqueur_id)
                if stats_vainqueur['nemesis'] != "---" and perdant_name.upper() in stats_vainqueur['nemesis'].upper():
                    if vainqueur_id == j1['id']:
                        xp_gain_j1 += 1.0
                    else:
                        xp_gain_j2 += 1.0
                    msg_extra += f"\n💀 RIVALITÉ : Némésis {perdant_name} vaincue ! (+1 XP)"

            # B) Si c'est un match de Boss
            is_boss_match = self.current_boss_data is not None
            if is_boss_match:
                type_match_db = "Boss"
                challenger_id = self.current_boss_data['challenger_id']
                event_id = self.current_boss_data['event_id']
                
                # Tous les participants au Raid gagnent +1
                xp_gain_j1 += 1.0
                xp_gain_j2 += 1.0
                msg_extra += "\n🐉 ÉVÉNEMENT BOSS : +1 XP de participation !"
                
                challenger_won = (vainqueur_id == challenger_id)
                res_combat = self.mechanics.executer_combat_boss(challenger_id, event_id, challenger_won)
                msg_extra += "\n" + res_combat['message']

            # C) Si un Contrat de Tueur à gages est accompli
            if vainqueur_id:
                if self.mechanics.verifier_et_valider_contrat(vainqueur_id, perdant_id, jeu_id):
                    if vainqueur_id == j1['id']:
                        xp_gain_j1 += 1.0
                    else:
                        xp_gain_j2 += 1.0
                    msg_extra += f"\n🎯 CONTRAT REMPLI : {perdant_name} éliminé(e) ! (+1 XP)"

            # --- 3. FORMATAGE DES NOMS ET INSERTION ---
            
            res_j1 = f"Victoire {s_j1}-{s_j2}" if s_j1 > s_j2 else (f"Défaite {s_j1}-{s_j2}" if s_j2 > s_j1 else "Egalité")
            res_j2 = f"Victoire {s_j2}-{s_j1}" if s_j2 > s_j1 else (f"Défaite {s_j2}-{s_j1}" if s_j1 > s_j2 else "Egalité")

            if is_boss_match:
                res_j1 += " (Boss)"
                res_j2 += " (Boss)"

            cursor.execute("INSERT INTO matchs (joueur1_id, joueur2_id, jeu_id, resultat_j1, resultat_j2, xp_j1, xp_j2, type_match) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (j1['id'], j2['id'], jeu_id, res_j1, res_j2, xp_gain_j1, xp_gain_j2, type_match_db))
            
            cursor.execute("UPDATE joueurs SET xp_total = xp_total + ? WHERE id = ?", (xp_gain_j1, j1['id']))
            cursor.execute("UPDATE joueurs SET xp_total = xp_total + ? WHERE id = ?", (xp_gain_j2, j2['id']))
            conn.commit()

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Erreur Base de données", f"Impossible d'enregistrer : {str(e)}")
            conn.close()
            return
            
        conn.close()

        # --- 4. ÉVALUATION DES NIVEAUX ET ÉTOILES ---
        self.mechanics.check_progression_rewards(j1['id'], j1['xp_total'], j1['xp_total'] + xp_gain_j1)
        self.mechanics.check_progression_rewards(j2['id'], j2['xp_total'], j2['xp_total'] + xp_gain_j2)
        self.mechanics.evaluer_etoiles_direct(j1['id'])
        self.mechanics.evaluer_etoiles_direct(j2['id'])

        self._afficher_gains([(p1_name, xp_gain_j1), (p2_name, xp_gain_j2)], msg_extra)
        
        self.combo_p1.setCurrentIndex(0)
        self.combo_p2.setCurrentIndex(0)
        self.group_scores.setExclusive(False)
        selected_button.setChecked(False)
        self.group_scores.setExclusive(True)
        self._check_events_1v1()

    def _valider_2v2(self):
        t1_p1 = self.combo_t1_p1.currentText()
        t1_p2 = self.combo_t1_p2.currentText()
        t2_p1 = self.combo_t2_p1.currentText()
        t2_p2 = self.combo_t2_p2.currentText()
        jeu_name = self.combo_jeu_2v2.currentText()
        selected_button = self.group_scores_2v2.checkedButton()
        
        joueurs = [t1_p1, t1_p2, t2_p1, t2_p2]
        
        if any("Choisir" in j for j in joueurs) or len(set(joueurs)) != 4 or "Choisir" in jeu_name or not selected_button:
            QMessageBox.warning(self, "Erreur", "Saisie incomplète ou joueurs en doublon.")
            return

        score = selected_button.text()
        s_t1, s_t2 = map(int, score.split('-'))
        
        res_t1 = f"Victoire 2v2 ({score})" if s_t1 > s_t2 else (f"Défaite 2v2 ({score})" if s_t2 > s_t1 else "Egalité 2v2")
        res_t2 = f"Victoire 2v2 ({s_t2}-{s_t1})" if s_t2 > s_t1 else (f"Défaite 2v2 ({s_t2}-{s_t1})" if s_t1 > s_t2 else "Egalité 2v2")

        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id, xp_total FROM joueurs WHERE surnom IN (?, ?, ?, ?)", (t1_p1, t1_p2, t2_p1, t2_p2))
            db_joueurs = {row['id']: row['xp_total'] for row in cursor.fetchall()}
            
            cursor.execute("SELECT id FROM joueurs WHERE surnom = ?", (t1_p1,))
            id_t1_p1 = cursor.fetchone()['id']
            cursor.execute("SELECT id FROM joueurs WHERE surnom = ?", (t1_p2,))
            id_t1_p2 = cursor.fetchone()['id']
            cursor.execute("SELECT id FROM joueurs WHERE surnom = ?", (t2_p1,))
            id_t2_p1 = cursor.fetchone()['id']
            cursor.execute("SELECT id FROM joueurs WHERE surnom = ?", (t2_p2,))
            id_t2_p2 = cursor.fetchone()['id']
            
            cursor.execute("SELECT id FROM jeux WHERE nom = ?", (jeu_name,))
            jeu_id = cursor.fetchone()['id']

            today = datetime.now().strftime("%Y-%m-%d")
            xp_gains = {}
            
            for pid in [id_t1_p1, id_t1_p2, id_t2_p1, id_t2_p2]:
                cursor.execute("SELECT COUNT(*) FROM matchs WHERE (joueur1_id = ? OR joueur2_id = ?) AND date LIKE ?", (pid, pid, f"{today}%"))
                is_first = cursor.fetchone()[0] == 0
                
                is_t1 = pid in [id_t1_p1, id_t1_p2]
                score_team = s_t1 if is_t1 else s_t2
                score_adv = s_t2 if is_t1 else s_t1
                
                gain = self.mechanics.calculate_xp_2v2(score_team, score_adv, is_first, False)
                xp_gains[pid] = gain

            cursor.execute("INSERT INTO matchs (joueur1_id, joueur2_id, jeu_id, resultat_j1, resultat_j2, xp_j1, xp_j2, type_match) VALUES (?, ?, ?, ?, ?, ?, ?, '2v2')",
                           (id_t1_p1, id_t2_p1, jeu_id, res_t1, res_t2, xp_gains[id_t1_p1], xp_gains[id_t2_p1]))
            cursor.execute("INSERT INTO matchs (joueur1_id, joueur2_id, jeu_id, resultat_j1, resultat_j2, xp_j1, xp_j2, type_match) VALUES (?, ?, ?, ?, ?, ?, ?, '2v2')",
                           (id_t1_p2, id_t2_p2, jeu_id, res_t1, res_t2, xp_gains[id_t1_p2], xp_gains[id_t2_p2]))

            for pid, gain in xp_gains.items():
                cursor.execute("UPDATE joueurs SET xp_total = xp_total + ? WHERE id = ?", (gain, pid))

            conn.commit()

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Erreur Base de données", f"Impossible d'enregistrer : {str(e)}")
            conn.close()
            return
            
        conn.close()

        for pid, gain in xp_gains.items():
            self.mechanics.check_progression_rewards(pid, db_joueurs[pid], db_joueurs[pid] + gain)
            self.mechanics.evaluer_etoiles_direct(pid)
            
        self._afficher_gains([(t1_p1, xp_gains[id_t1_p1]), (t1_p2, xp_gains[id_t1_p2]), 
                              (t2_p1, xp_gains[id_t2_p1]), (t2_p2, xp_gains[id_t2_p2])])

        for combo in [self.combo_t1_p1, self.combo_t1_p2, self.combo_t2_p1, self.combo_t2_p2]:
            combo.setCurrentIndex(0)
        self.group_scores_2v2.setExclusive(False)
        selected_button.setChecked(False)
        self.group_scores_2v2.setExclusive(True)

    def _valider_multi(self):
        jeu = self.combo_jeu_multi.currentText()
        gagnant = self.combo_gagnant.currentText()
        
        autres_joueurs = [cb.currentText() for cb in self.combos_multi_others if "Choisir" not in cb.currentText()]

        if "Choisir" in jeu or "Choisir" in gagnant:
            QMessageBox.warning(self, "Erreur", "Veuillez choisir un jeu et un gagnant.")
            return
            
        if len(autres_joueurs) < 1:
            QMessageBox.warning(self, "Erreur", "Il faut au moins 1 perdant.")
            return

        tous_les_joueurs = [gagnant] + autres_joueurs
        if len(tous_les_joueurs) != len(set(tous_les_joueurs)):
            QMessageBox.warning(self, "Erreur", "Un joueur ne peut pas être sélectionné plusieurs fois.")
            return

        nb_adversaires = len(autres_joueurs)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id FROM jeux WHERE nom = ?", (jeu,))
            jeu_id = cursor.fetchone()['id']

            today = datetime.now().strftime("%Y-%m-%d")
            liste_gains = []
            joueurs_a_evaluer = []

            cursor.execute("SELECT id, xp_total FROM joueurs WHERE surnom = ?", (gagnant,))
            j_gagnant = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(*) FROM matchs WHERE (joueur1_id = ? OR joueur2_id = ?) AND date LIKE ?", (j_gagnant['id'], j_gagnant['id'], f"{today}%"))
            is_first_match_g = cursor.fetchone()[0] == 0
            
            xp_gagnant = self.mechanics.calculate_xp_multi(True, nb_adversaires, is_first_match_g, False)
            cursor.execute("UPDATE joueurs SET xp_total = xp_total + ? WHERE id = ?", (xp_gagnant, j_gagnant['id']))
            
            joueurs_a_evaluer.append((j_gagnant['id'], j_gagnant['xp_total'], j_gagnant['xp_total'] + xp_gagnant))
            liste_gains.append((gagnant, xp_gagnant))

            for perdant_nom in autres_joueurs:
                cursor.execute("SELECT id, xp_total FROM joueurs WHERE surnom = ?", (perdant_nom,))
                j_perdant = cursor.fetchone()
                
                cursor.execute("SELECT COUNT(*) FROM matchs WHERE (joueur1_id = ? OR joueur2_id = ?) AND date LIKE ?", (j_perdant['id'], j_perdant['id'], f"{today}%"))
                is_first_match_p = cursor.fetchone()[0] == 0
                
                xp_perdant = self.mechanics.calculate_xp_multi(False, nb_adversaires, is_first_match_p, False)
                
                cursor.execute("INSERT INTO matchs (joueur1_id, joueur2_id, jeu_id, resultat_j1, resultat_j2, xp_j1, xp_j2, type_match) VALUES (?, ?, ?, ?, ?, ?, ?, 'Multi')",
                               (j_gagnant['id'], j_perdant['id'], jeu_id, "Victoire (Multi)", "Défaite (Multi)", xp_gagnant, xp_perdant))
                
                cursor.execute("UPDATE joueurs SET xp_total = xp_total + ? WHERE id = ?", (xp_perdant, j_perdant['id']))
                
                joueurs_a_evaluer.append((j_perdant['id'], j_perdant['xp_total'], j_perdant['xp_total'] + xp_perdant))
                liste_gains.append((perdant_nom, xp_perdant))

            conn.commit()

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Erreur Base de données", f"Impossible d'enregistrer : {str(e)}")
            conn.close()
            return
            
        conn.close()

        for pid, old_xp, new_xp in joueurs_a_evaluer:
            self.mechanics.check_progression_rewards(pid, old_xp, new_xp)
            self.mechanics.evaluer_etoiles_direct(pid)

        self._afficher_gains(liste_gains)

        self.combo_jeu_multi.setCurrentIndex(0)
        self.combo_gagnant.setCurrentIndex(0)
        for cb in self.combos_multi_others: cb.setCurrentIndex(0)

    def _afficher_gains(self, gains, msg_extra=""):
        lignes = [f"{nom} : +{xp:.1f} XP" for nom, xp in gains]
        texte = " MATCH ENREGISTRÉ !\n" + "\n".join(lignes)
        if msg_extra:
            texte += f"\n{msg_extra}"
        self.lbl_feedback.setText(texte)
        self.lbl_feedback.show()
        QTimer.singleShot(5000, self.lbl_feedback.hide)

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            #page_title { color: #bc13fe; font-family: 'Orbitron'; font-size: 30px; font-weight: bold; }
            #lbl_vs { color: #ff0055; font-family: 'Orbitron'; font-size: 36px; font-weight: 900; margin: 0px 20px;}
            #lbl_feedback { color: #00ff9d; font-family: 'Orbitron'; font-size: 16px; font-weight: bold; background-color: rgba(0, 255, 157, 0.1); border: 1px solid #00ff9d; border-radius: 10px; padding: 15px;}
            
            QComboBox { background-color: #050505; color: white; border: 1px solid rgba(0, 243, 255, 0.4); border-radius: 8px; padding: 12px; font-family: 'Rajdhani'; font-size: 20px; min-width: 350px; }
            
            QRadioButton { color: white; font-family: 'Orbitron'; font-size: 26px; font-weight: bold; margin: 10px; }
            QRadioButton:hover { color: #bc13fe; }
            QRadioButton::indicator { width: 28px; height: 28px; border-radius: 14px; border: 2px solid rgba(0, 243, 255, 0.4); }
            QRadioButton::indicator:checked { background-color: #bc13fe; border: 2px solid #bc13fe; }
            QRadioButton::indicator:hover { border: 2px solid #00f3ff; }
            
            #btn_valider { background-color: transparent; color: #00f3ff; font-family: 'Orbitron'; font-size: 26px; font-weight: bold; padding: 20px 80px; border: 2px solid #00f3ff; border-radius: 10px; margin-top: 10px;}
            #btn_valider:hover { background-color: rgba(0, 243, 255, 0.15); border: 2px solid #bc13fe; color: #bc13fe; }
            
            QTabWidget::pane { border: 1px solid rgba(0, 243, 255, 0.2); background-color: transparent; border-radius: 10px; }
            QTabBar::tab { background-color: #050505; color: #e0f7fa; font-family: 'Rajdhani'; font-size: 20px; padding: 12px 24px; border: 1px solid rgba(0, 243, 255, 0.2); border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; }
            QTabBar::tab:selected { background-color: rgba(0, 243, 255, 0.1); color: #00f3ff; border: 1px solid #00f3ff; border-bottom: none; }
        """)
# <VALIDATED>