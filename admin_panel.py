# <VALIDATED>
import os
import shutil
from datetime import datetime
# <VALIDATED>
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QLabel, QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QCheckBox, QGridLayout, 
                             QFormLayout, QMessageBox, QGroupBox, QFileDialog,
                             QComboBox, QSpinBox, QDateEdit, QScrollArea)
# </VALIDATED>
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
import qtawesome as qta
from controllers.league_mechanics import LeagueMechanics

class AdminPanel(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.mechanics = LeagueMechanics(self.db)
        self.setObjectName("admin_panel")
        
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.icones_dir = os.path.join(self.base_dir, 'assets', 'icones')
        if not os.path.exists(self.icones_dir):
            os.makedirs(self.icones_dir)
            
        self.avatars_dir = os.path.join(self.base_dir, 'assets', 'avatars')
        if not os.path.exists(self.avatars_dir):
            os.makedirs(self.avatars_dir)

        self.current_joueur_id = None
        self.current_jeu_id = None
        self.current_avatar_file = "" 
        self.checkboxes_jeux = {}
        
        self._setup_ui()
        self._apply_stylesheet()
        
    def showEvent(self, event):
        self._load_jeux()
        self._load_joueurs()
        self._build_dynamic_checkboxes()
        self._load_parametres()
        self._load_niveaux()
        self._load_events_data()
        super().showEvent(event)

# <VALIDATED>
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("PANNEAU D'ADMINISTRATION")
        title.setObjectName("admin_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("admin_tabs")
        
        self.tab_joueurs = QWidget()
        self._setup_tab_joueurs()
        self.tabs.addTab(self.tab_joueurs, "Gestion des Joueurs")

        self.tab_jeux = QWidget()
        self._setup_tab_jeux()
        self.tabs.addTab(self.tab_jeux, "Jeux, Lots")

        self.tab_params = QWidget()
        self._setup_tab_parametres()
        self.tabs.addTab(self.tab_params, "Saison, Paramètres & Niveaux")

        self.tab_events = QWidget()
        self._setup_tab_events()
        self.tabs.addTab(self.tab_events, "Événements (RPG)")

        self.tab_settings = QWidget()
        self._setup_tab_settings()
        self.tabs.addTab(self.tab_settings, "Paramètres")

        # --- NOUVEL ONGLET AIDE ---
        self.tab_aide = QWidget()
        self._setup_tab_aide()
        self.tabs.addTab(self.tab_aide, "Aide & Règles")

        layout.addWidget(self.tabs)
# </VALIDATED>

    def _setup_tab_joueurs(self):
        layout = QHBoxLayout(self.tab_joueurs)
        
        left_panel = QVBoxLayout()
        
        self.input_recherche = QLineEdit()
        self.input_recherche.setPlaceholderText("Rechercher un joueur (Nom ou Pseudo)...")
        self.input_recherche.textChanged.connect(self._filter_joueurs)
        self.input_recherche.setStyleSheet("padding: 8px; border-radius: 5px; border: 1px solid #00f3ff; background-color: #141928; color: white;")
        left_panel.addWidget(self.input_recherche)
        
        self.table_joueurs = QTableWidget(0, 4)
        self.table_joueurs.setHorizontalHeaderLabels(["ID", "Nom", "Pseudo", "XP Totale"])
        self.table_joueurs.setColumnHidden(0, True)
        self.table_joueurs.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_joueurs.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_joueurs.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_joueurs.itemSelectionChanged.connect(self._on_joueur_selected)
        left_panel.addWidget(self.table_joueurs)

        right_panel = QVBoxLayout()
        self.lbl_mode_edition = QLabel("CRÉER / MODIFIER UN JOUEUR")
        self.lbl_mode_edition.setObjectName("mode_edition_label")
        right_panel.addWidget(self.lbl_mode_edition)
        
        form_layout = QFormLayout()
        self.input_nom = QLineEdit()
        self.input_surnom = QLineEdit()
        form_layout.addRow("Nom Complet :", self.input_nom)
        form_layout.addRow("Pseudo :", self.input_surnom)
        right_panel.addLayout(form_layout)

        row_avatar = QHBoxLayout()
        self.lbl_avatar_info = QLabel("Avatar : Aucun")
        self.btn_change_avatar = QPushButton(" Changer l'Avatar")
        self.btn_change_avatar.setIcon(qta.icon("fa5s.user-circle", color="white"))
        self.btn_change_avatar.clicked.connect(self._change_avatar_joueur)
        row_avatar.addWidget(self.lbl_avatar_info)
        row_avatar.addWidget(self.btn_change_avatar)
        right_panel.addLayout(row_avatar)

        self.group_jeux = QGroupBox("Jeux pratiqués")
        self.layout_jeux = QVBoxLayout(self.group_jeux)
        right_panel.addWidget(self.group_jeux)

        form_xp = QFormLayout()
        self.input_xp_ajustement = QLineEdit()
        self.input_xp_ajustement.setPlaceholderText("Ex: 5 ou -3")
        form_xp.addRow("Ajustement manuel d'XP :", self.input_xp_ajustement)
        right_panel.addLayout(form_xp)

        row_btns = QHBoxLayout()
        
        # --- NOUVEAU BOUTON : Vider les champs ---
        self.btn_new_joueur = QPushButton("  Nouveau Joueur")
        self.btn_new_joueur.setIcon(qta.icon("fa5s.user-plus", color="white"))
        self.btn_new_joueur.clicked.connect(self._reset_joueur_form)
        self.btn_new_joueur.setStyleSheet("background-color: rgba(0, 243, 255, 0.1); border: 1px solid #00f3ff;")
        
        self.btn_save_joueur = QPushButton("  Mettre à jour / Créer")
        self.btn_save_joueur.setIcon(qta.icon("fa5s.save", color="white"))
        self.btn_save_joueur.clicked.connect(self._save_joueur)
        
        row_btns.addWidget(self.btn_new_joueur)
        row_btns.addWidget(self.btn_save_joueur)
        
        right_panel.addLayout(row_btns)
        right_panel.addStretch()

        layout.addLayout(left_panel, 2)
        layout.addLayout(right_panel, 1)

    def _build_dynamic_checkboxes(self):
        for i in reversed(range(self.layout_jeux.count())): 
            widget = self.layout_jeux.itemAt(i).widget()
            if widget is not None: widget.setParent(None)
        
        self.checkboxes_jeux.clear()
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom FROM jeux WHERE actif = 1 ORDER BY nom ASC")
        jeux = cursor.fetchall()
        conn.close()

        for jeu in jeux:
            cb = QCheckBox(jeu["nom"])
            self.checkboxes_jeux[jeu["id"]] = cb
            self.layout_jeux.addWidget(cb)

    def _filter_joueurs(self, text):
        search_text = text.lower()
        for row in range(self.table_joueurs.rowCount()):
            item_nom = self.table_joueurs.item(row, 1)
            item_pseudo = self.table_joueurs.item(row, 2)
            
            nom = item_nom.text().lower() if item_nom else ""
            pseudo = item_pseudo.text().lower() if item_pseudo else ""
            
            if search_text in nom or search_text in pseudo:
                self.table_joueurs.setRowHidden(row, False)
            else:
                self.table_joueurs.setRowHidden(row, True)

    def _load_joueurs(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, surnom, xp_total FROM joueurs ORDER BY nom ASC")
        joueurs = cursor.fetchall()
        conn.close()

        self.table_joueurs.setRowCount(0)
        for row_idx, joueur in enumerate(joueurs):
            self.table_joueurs.insertRow(row_idx)
            self.table_joueurs.setItem(row_idx, 0, QTableWidgetItem(str(joueur["id"])))
            self.table_joueurs.setItem(row_idx, 1, QTableWidgetItem(joueur["nom"]))
            self.table_joueurs.setItem(row_idx, 2, QTableWidgetItem(joueur["surnom"] if joueur["surnom"] else ""))
            self.table_joueurs.setItem(row_idx, 3, QTableWidgetItem(f"{joueur['xp_total']:.1f}"))

    def _delete_boss(self):
        if not hasattr(self, 'table_boss') or self.table_boss.currentRow() < 0:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un Boss dans le tableau.")
            return
            
        row = self.table_boss.currentRow()
        boss_id_item = self.table_boss.item(row, 0)
        
        if not boss_id_item:
            return
            
        boss_id = int(boss_id_item.text())
        boss_name = self.table_boss.item(row, 2).text()
        
        reply = QMessageBox.question(self, "Confirmation", 
                                     f"Voulez-vous vraiment supprimer definitivement le Boss '{boss_name}' ?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                                     
        if reply == QMessageBox.StandardButton.Yes:
            success = self.db.supprimer_boss(boss_id)
            if success:
                QMessageBox.information(self, "Succes", "Le Boss a ete supprime avec succes.")
                if hasattr(self, '_load_events_data'):
                    self._load_events_data()
            else:
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue lors de la suppression.")

    def _purge_contrats(self):
        reply = QMessageBox.question(self, "Confirmation", 
                                     "Voulez-vous vraiment annuler tous les contrats actifs en cours ?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                                     
        if reply == QMessageBox.StandardButton.Yes:
            success = self.db.purger_contrats_actifs()
            if success:
                QMessageBox.information(self, "Succes", "Tous les contrats actifs ont ete annules.")
                if hasattr(self, '_load_events_data'):
                    self._load_events_data()
            else:
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue lors de l'annulation.")

    def _on_joueur_selected(self):
        selected_row = self.table_joueurs.currentRow()
        if selected_row < 0: return

        self.current_joueur_id = int(self.table_joueurs.item(selected_row, 0).text())
        self.input_nom.setText(self.table_joueurs.item(selected_row, 1).text())
        self.input_surnom.setText(self.table_joueurs.item(selected_row, 2).text())
        self.input_xp_ajustement.clear()
        
        self.lbl_mode_edition.setText("MODIFIER LE JOUEUR")
        self.lbl_mode_edition.setStyleSheet("color: #bc13fe;")
        
        for cb in self.checkboxes_jeux.values(): cb.setChecked(False)

        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT avatar FROM joueurs WHERE id = ?", (self.current_joueur_id,))
        avatar_data = cursor.fetchone()
        if avatar_data and avatar_data["avatar"]:
            self.current_avatar_file = avatar_data["avatar"]
            self.lbl_avatar_info.setText(f"Avatar : {self.current_avatar_file}")
        else:
            self.current_avatar_file = ""
            self.lbl_avatar_info.setText("Avatar : Aucun")

        cursor.execute("SELECT jeu_id FROM joueurs_jeux WHERE joueur_id = ?", (self.current_joueur_id,))
        jeux_joues = [row["jeu_id"] for row in cursor.fetchall()]
        conn.close()

        for jeu_id in jeux_joues:
            if jeu_id in self.checkboxes_jeux:
                self.checkboxes_jeux[jeu_id].setChecked(True)

    def _reset_joueur_form(self):
        self.current_joueur_id = None
        self.current_avatar_file = ""
        self.lbl_avatar_info.setText("Avatar : Aucun")
        self.input_nom.clear()
        self.input_surnom.clear()
        self.input_xp_ajustement.clear()
        for cb in self.checkboxes_jeux.values(): cb.setChecked(False)
        self.lbl_mode_edition.setText("CRÉER / MODIFIER UN JOUEUR")
        self.lbl_mode_edition.setStyleSheet("color: #00f3ff;")
        self.table_joueurs.clearSelection()

    def _change_avatar_joueur(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Choisir un Avatar", "", "Images (*.png *.jpg *.jpeg *.svg)")
        if file_path:
            nom_fichier = os.path.basename(file_path)
            
            # --- CORRECTION DU BUG DOSSIER OCCUPÉ ---
            # normpath et abspath permettent de s'assurer que Windows comprend
            # exactement le chemin pour la comparaison
            dest_path = os.path.normpath(os.path.abspath(os.path.join(self.avatars_dir, nom_fichier)))
            source_path = os.path.normpath(os.path.abspath(file_path))

            if source_path != dest_path:
                try:
                    shutil.copy2(source_path, dest_path)
                except Exception as e:
                    QMessageBox.warning(self, "Erreur de copie", f"Impossible de copier l'image : {str(e)}")
                    return
            
            self.current_avatar_file = nom_fichier
            self.lbl_avatar_info.setText(f"Avatar : {nom_fichier}")

    def _save_joueur(self):
        nom = self.input_nom.text().strip()
        surnom = self.input_surnom.text().strip()
        ajustement_xp = self.input_xp_ajustement.text().strip()

        if not nom:
            QMessageBox.warning(self, "Erreur", "Le nom du joueur est obligatoire.")
            return

        xp_bonus = 0.0
        if ajustement_xp:
            try: xp_bonus = float(ajustement_xp)
            except ValueError:
                QMessageBox.warning(self, "Erreur", "L'ajustement d'XP doit être un nombre.")
                return

        conn = self.db.get_connection()
        cursor = conn.cursor()
        old_xp = 0.0
        joueur_id = self.current_joueur_id

        if not joueur_id:
            cursor.execute("SELECT id FROM joueurs WHERE nom = ? OR surnom = ?", (nom, surnom))
            existing_joueur = cursor.fetchone()
            if existing_joueur:
                joueur_id = existing_joueur["id"]

        try:
            if joueur_id:
                cursor.execute("SELECT xp_total FROM joueurs WHERE id=?", (joueur_id,))
                result = cursor.fetchone()
                old_xp = result['xp_total'] if result else 0.0
                
                cursor.execute("UPDATE joueurs SET nom=?, surnom=?, xp_total=xp_total+?, avatar=? WHERE id=?", 
                               (nom, surnom, xp_bonus, self.current_avatar_file, joueur_id))
                cursor.execute("DELETE FROM joueurs_jeux WHERE joueur_id=?", (joueur_id,))
                
            else:
                cursor.execute("INSERT INTO joueurs (nom, surnom, xp_total, niveau, avatar) VALUES (?, ?, ?, 0, ?)", 
                               (nom, surnom, xp_bonus, self.current_avatar_file))
                joueur_id = cursor.lastrowid
                cursor.execute("INSERT INTO lots (joueur_id, dus_niveau, donnes_niveau, dus_palier, donnes_palier) VALUES (?, 0, 0, 0, 0)", (joueur_id,))

            for jeu_id, cb in self.checkboxes_jeux.items():
                if cb.isChecked():
                    cursor.execute("INSERT INTO joueurs_jeux (joueur_id, jeu_id) VALUES (?, ?)", (joueur_id, jeu_id))

            conn.commit()
            
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Erreur Base de données", str(e))
            return
        finally:
            conn.close()

        if xp_bonus > 0 and old_xp > 0:
            try:
                self.mechanics.check_progression_rewards(joueur_id, old_xp, old_xp + xp_bonus)
            except Exception as e:
                QMessageBox.warning(self, "Avertissement", f"Erreur lors de la vérification des récompenses : {e}")
                
        self._reset_joueur_form()
        self._load_joueurs()
        self._build_dynamic_checkboxes()
        
        QMessageBox.information(self, "Succès", "Profil joueur sauvegardé.")

    def _setup_tab_jeux(self):
        layout = QHBoxLayout(self.tab_jeux)
        
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("LISTE DES JEUX ENREGISTRÉS"))
        self.table_jeux = QTableWidget(0, 5)
        self.table_jeux.setHorizontalHeaderLabels(["ID", "Jeu", "Statut", "Lot niveau", "Nb Cartes Promo"])
        self.table_jeux.setColumnHidden(0, True)
        self.table_jeux.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_jeux.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_jeux.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_jeux.itemSelectionChanged.connect(self._on_jeu_selected)
        left_panel.addWidget(self.table_jeux)

        self.btn_toggle_jeu = QPushButton("Activer / Désactiver le jeu sélectionné")
        self.btn_toggle_jeu.clicked.connect(self._toggle_jeu)
        left_panel.addWidget(self.btn_toggle_jeu)

        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("AJOUTER / MODIFIER UN JEU"))
        
        form_layout = QFormLayout()
        self.input_jeu_nom = QLineEdit()
        self.input_jeu_rec_niv = QLineEdit()
        self.input_jeu_rec_pal = QLineEdit()
        self.input_jeu_cartes = QLineEdit()
        self.input_jeu_cartes.setPlaceholderText("Ex: 20")
        
        form_layout.addRow("Nom du Jeu :", self.input_jeu_nom)
        form_layout.addRow("Récompense (Lot niveau) :", self.input_jeu_rec_niv)
        form_layout.addRow("Récompense Palier (Petit lot) :", self.input_jeu_rec_pal)
        form_layout.addRow("Nombre de Cartes Promos (Roue) :", self.input_jeu_cartes)
        right_panel.addLayout(form_layout)

        self.btn_save_jeu = QPushButton("  Sauvegarder le Jeu")
        self.btn_save_jeu.setIcon(qta.icon("fa5s.save", color="white"))
        self.btn_save_jeu.clicked.connect(self._save_jeu)
        right_panel.addWidget(self.btn_save_jeu)
        
        self.btn_reset_jeu = QPushButton("  Nouveau Jeu")
        self.btn_reset_jeu.setIcon(qta.icon("fa5s.plus", color="white"))
        self.btn_reset_jeu.clicked.connect(self._reset_jeu_form)
        right_panel.addWidget(self.btn_reset_jeu)
        
        right_panel.addSpacing(40)
        right_panel.addStretch()

        layout.addLayout(left_panel, 2)
        layout.addLayout(right_panel, 1)

    def _load_jeux(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, actif, recompense_niveau, nb_cartes_promo FROM jeux ORDER BY nom ASC")
        jeux = cursor.fetchall()
        conn.close()

        self.table_jeux.setRowCount(0)
        for row_idx, jeu in enumerate(jeux):
            self.table_jeux.insertRow(row_idx)
            self.table_jeux.setItem(row_idx, 0, QTableWidgetItem(str(jeu["id"])))
            self.table_jeux.setItem(row_idx, 1, QTableWidgetItem(jeu["nom"]))
            
            statut_text = "Actif" if jeu["actif"] else "Inactif"
            statut_item = QTableWidgetItem(statut_text)
            if not jeu["actif"]: statut_item.setForeground(Qt.GlobalColor.red)
            
            self.table_jeux.setItem(row_idx, 2, statut_item)
            self.table_jeux.setItem(row_idx, 3, QTableWidgetItem(jeu["recompense_niveau"]))
            self.table_jeux.setItem(row_idx, 4, QTableWidgetItem(str(jeu["nb_cartes_promo"])))

    def _on_jeu_selected(self):
        selected_row = self.table_jeux.currentRow()
        if selected_row < 0: return

        self.current_jeu_id = int(self.table_jeux.item(selected_row, 0).text())
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nom, recompense_niveau, recompense_palier, nb_cartes_promo FROM jeux WHERE id = ?", (self.current_jeu_id,))
        jeu = cursor.fetchone()
        conn.close()

        if jeu:
            self.input_jeu_nom.setText(jeu["nom"])
            self.input_jeu_rec_niv.setText(jeu["recompense_niveau"])
            self.input_jeu_rec_pal.setText(jeu["recompense_palier"])
            self.input_jeu_cartes.setText(str(jeu["nb_cartes_promo"]))

    def _reset_jeu_form(self):
        self.current_jeu_id = None
        self.input_jeu_nom.clear()
        self.input_jeu_rec_niv.clear()
        self.input_jeu_rec_pal.clear()
        self.input_jeu_cartes.clear()
        self.table_jeux.clearSelection()

    def _save_jeu(self):
        nom = self.input_jeu_nom.text().strip()
        rec_niv = self.input_jeu_rec_niv.text().strip() or "Booster"
        rec_pal = self.input_jeu_rec_pal.text().strip() or "Carte Promo"
        
        try:
            nb_cartes = int(self.input_jeu_cartes.text().strip())
        except ValueError:
            nb_cartes = 20

        if not nom: return
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            if self.current_jeu_id:
                cursor.execute("""
                    UPDATE jeux 
                    SET nom = ?, recompense_niveau = ?, recompense_palier = ?, nb_cartes_promo = ? 
                    WHERE id = ?
                """, (nom, rec_niv, rec_pal, nb_cartes, self.current_jeu_id))
            else:
                cursor.execute("""
                    INSERT INTO jeux (nom, icone, actif, recompense_niveau, recompense_palier, nb_cartes_promo) 
                    VALUES (?, ?, 1, ?, ?, ?)
                """, (nom, 'fa5s.layer-group', rec_niv, rec_pal, nb_cartes))
            
            conn.commit()
            self._reset_jeu_form()
            self._load_jeux()
            self._build_dynamic_checkboxes()
            QMessageBox.information(self, "Succès", "Jeu sauvegardé avec succès.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur Base de données", str(e))
        finally: 
            conn.close()

    def _toggle_jeu(self):
        selected_row = self.table_jeux.currentRow()
        if selected_row < 0: return
        
        jeu_id = int(self.table_jeux.item(selected_row, 0).text())
        statut_actuel = self.table_jeux.item(selected_row, 2).text()
        nouveau_statut = 0 if statut_actuel == "Actif" else 1

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE jeux SET actif = ? WHERE id = ?", (nouveau_statut, jeu_id))
        conn.commit()
        conn.close()
        self._load_jeux()
        self._build_dynamic_checkboxes()

    def _setup_tab_parametres(self):
        layout = QHBoxLayout(self.tab_params)

        left_panel = QVBoxLayout()
        
        reset_box = QGroupBox("GESTION DE LA SAISON")
        reset_layout = QVBoxLayout(reset_box)
        self.btn_reset_saison = QPushButton("!!! DÉMARRER UNE NOUVELLE SAISON (RESET) !!!")
        self.btn_reset_saison.setStyleSheet("background-color: #ff0055; color: white; font-weight: bold; border: 2px solid #ff0000;")
        self.btn_reset_saison.clicked.connect(self._reset_saison)
        reset_layout.addWidget(self.btn_reset_saison)
        left_panel.addWidget(reset_box)

        backup_box = QGroupBox("SÉCURITÉ & SAUVEGARDES")
        backup_layout = QVBoxLayout(backup_box)
        
        btn_backup = QPushButton("  Créer une Sauvegarde (Backup)")
        btn_backup.setIcon(qta.icon("fa5s.download", color="white"))
        btn_backup.clicked.connect(self._create_backup)
        
        btn_restore = QPushButton("  Restaurer une Sauvegarde")
        btn_restore.setIcon(qta.icon("fa5s.upload", color="white"))
        btn_restore.clicked.connect(self._restore_backup)
        btn_restore.setStyleSheet("background-color: rgba(255, 165, 0, 0.2); border: 1px solid orange;")
        
        backup_layout.addWidget(btn_backup)
        backup_layout.addWidget(btn_restore)
        left_panel.addWidget(backup_box)
        
        left_panel.addSpacing(20)
        left_panel.addWidget(QLabel("MODIFICATEURS D'EXPÉRIENCE"))
        
        self.table_params = QTableWidget(0, 2)
        self.table_params.setHorizontalHeaderLabels(["Action / Règle", "Points XP"])
        self.table_params.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        left_panel.addWidget(self.table_params)

        btn_save_params = QPushButton("Sauvegarder les Modificateurs")
        btn_save_params.clicked.connect(self._save_parametres)
        left_panel.addWidget(btn_save_params)

        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("GESTION DES NIVEAUX ET ICÔNES"))
        
        self.table_niveaux = QTableWidget(0, 5)
        self.table_niveaux.setHorizontalHeaderLabels(["ID", "Ordre", "Nom du Titre", "XP Requise", "Icône Actuelle"])
        self.table_niveaux.setColumnHidden(0, True)
        self.table_niveaux.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_niveaux.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        right_panel.addWidget(self.table_niveaux)

        row_btns_niv = QHBoxLayout()
        
        btn_change_icon = QPushButton("  Changer l'icône (Image)")
        btn_change_icon.setIcon(qta.icon("fa5s.image", color="white"))
        btn_change_icon.clicked.connect(self._change_icon_niveau)
        
        btn_save_niveaux = QPushButton("  Sauvegarder les Niveaux")
        btn_save_niveaux.setIcon(qta.icon("fa5s.save", color="white"))
        btn_save_niveaux.clicked.connect(self._save_niveaux)

        row_btns_niv.addWidget(btn_change_icon)
        row_btns_niv.addWidget(btn_save_niveaux)
        right_panel.addLayout(row_btns_niv)

        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 2)

    def _setup_tab_events(self):
        layout = QHBoxLayout(self.tab_events)

        # --- GAUCHE : GESTION DES BOSS ---
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("GESTION DES BOSS DE LIGUE"))

        self.table_boss = QTableWidget(0, 5)
        self.table_boss.setHorizontalHeaderLabels(["ID", "Boss", "Jeu", "PV", "Statut"])
        self.table_boss.setColumnHidden(0, True)
        self.table_boss.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_boss.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        left_panel.addWidget(self.table_boss)

        self.btn_delete_boss = QPushButton("  Supprimer le Boss selectionne")
        self.btn_delete_boss.setIcon(qta.icon("fa5s.trash-alt", color="white"))
        self.btn_delete_boss.setStyleSheet("background-color: rgba(255, 0, 0, 0.2); border: 1px solid red;")
        self.btn_delete_boss.clicked.connect(self._delete_boss)
        left_panel.addWidget(self.btn_delete_boss)

        form_boss = QGroupBox("Invoquer un nouveau Boss")
        form_layout = QFormLayout(form_boss)

        self.combo_boss_joueur = QComboBox()
        self.combo_boss_jeu = QComboBox()
        
        self.spin_boss_pv = QSpinBox()
        self.spin_boss_pv.setRange(1, 100)
        self.spin_boss_pv.setValue(10)
        
        self.spin_boss_coupes = QSpinBox()
        self.spin_boss_coupes.setRange(1, 100)
        self.spin_boss_coupes.setValue(5)

        self.date_boss_fin = QDateEdit()
        self.date_boss_fin.setDate(QDate.currentDate().addDays(7))
        self.date_boss_fin.setCalendarPopup(True)

        form_layout.addRow("Joueur (Le Boss) :", self.combo_boss_joueur)
        form_layout.addRow("Jeu affilie :", self.combo_boss_jeu)
        form_layout.addRow("Points de Vie (Max) :", self.spin_boss_pv)
        form_layout.addRow("Victoires (Coupes) Requises :", self.spin_boss_coupes)
        form_layout.addRow("Date de Fin :", self.date_boss_fin)

        self.btn_save_boss = QPushButton("  Invoquer le Boss")
        self.btn_save_boss.setIcon(qta.icon("fa5s.dragon", color="white"))
        self.btn_save_boss.clicked.connect(self._save_boss)
        form_layout.addRow(self.btn_save_boss)

        left_panel.addWidget(form_boss)

        # --- DROITE : TUEURS A GAGES ---
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("CONTRATS (TUEURS A GAGES)"))

        contrats_box = QGroupBox("Le Destin (Generateur)")
        contrats_layout = QVBoxLayout(contrats_box)

        contrats_layout.addWidget(QLabel("Selectionnez le jeu pour lequel generer les contrats :"))
        self.combo_tueur_jeu = QComboBox()
        contrats_layout.addWidget(self.combo_tueur_jeu)

        self.btn_generate_tueurs = QPushButton("  Generer les Contrats")
        self.btn_generate_tueurs.setIcon(qta.icon("fa5s.crosshairs", color="white"))
        self.btn_generate_tueurs.setStyleSheet("background-color: rgba(255, 0, 0, 0.2); border: 1px solid red;")
        self.btn_generate_tueurs.clicked.connect(self._generate_contrats)
        contrats_layout.addWidget(self.btn_generate_tueurs)

        self.btn_purge_contrats = QPushButton("  Purger tous les contrats actifs")
        self.btn_purge_contrats.setIcon(qta.icon("fa5s.ban", color="white"))
        self.btn_purge_contrats.setStyleSheet("background-color: rgba(255, 0, 0, 0.2); border: 1px solid red;")
        self.btn_purge_contrats.clicked.connect(self._purge_contrats)
        contrats_layout.addWidget(self.btn_purge_contrats)

        right_panel.addWidget(contrats_box)

        right_panel.addWidget(QLabel("Contrats Actifs (En Cours) :"))
        self.table_contrats = QTableWidget(0, 3)
        self.table_contrats.setHorizontalHeaderLabels(["Jeu", "Chasseur", "Cible"])
        self.table_contrats.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        right_panel.addWidget(self.table_contrats)

        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 1)

    # --- NOUVEL ONGLET : PARAMÈTRES (Sécurité et Visuels) ---
    def _setup_tab_settings(self):
        layout = QVBoxLayout(self.tab_settings)

        group_secu = QGroupBox("SÉCURITÉ (ACCÈS ADMIN)")
        layout_secu = QFormLayout(group_secu)
        self.edit_new_pin = QLineEdit()
        self.edit_new_pin.setPlaceholderText("Nouveau code PIN...")
        self.btn_save_pin = QPushButton(" Changer le code PIN")
        self.btn_save_pin.setIcon(qta.icon("fa5s.lock", color="white"))
        self.btn_save_pin.clicked.connect(self._change_admin_pin)
        layout_secu.addRow("Nouveau PIN :", self.edit_new_pin)
        layout_secu.addRow(self.btn_save_pin)
        layout.addWidget(group_secu)

        group_stars = QGroupBox("PERSONNALISATION DES ÉTOILES GLOBALES")
        layout_stars = QFormLayout(group_stars)
        
        self.combo_star_n = QComboBox()
        self.combo_star_p = QComboBox()
        self.combo_star_c = QComboBox()
        
        files = ["fa5s.star", "fa5s.certificate", "fa5s.gem", "fa5s.crown", "fa5s.sun", "fa5s.moon"]
        if os.path.exists(self.icones_dir):
            files += [f for f in os.listdir(self.icones_dir) if f.endswith(('.png', '.jpg'))]
            
        for cb in [self.combo_star_n, self.combo_star_p, self.combo_star_c]:
            cb.addItems(files)

        self.btn_save_stars = QPushButton(" Appliquer les nouveaux visuels")
        self.btn_save_stars.setIcon(qta.icon("fa5s.palette", color="white"))
        self.btn_save_stars.clicked.connect(self._save_star_settings)
        
        layout_stars.addRow("Étoile Normale :", self.combo_star_n)
        layout_stars.addRow("Étoile Pourpre :", self.combo_star_p)
        layout_stars.addRow("Couronne/Prestige :", self.combo_star_c)
        layout_stars.addRow(self.btn_save_stars)
        layout.addWidget(group_stars)
        
        layout.addStretch()
# <VALIDATED>
    def _setup_tab_aide(self):
        layout = QVBoxLayout(self.tab_aide)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(container)
        
        aide_text = """
        <h2 style='color: #bc13fe; font-family: Orbitron;'>📖 GUIDE MÉMOIRE DE LA LIGUE</h2>
        
        <h3 style='color: #00f3ff; font-family: Orbitron;'>⚔️ NÉMÉSIS ET PROIE</h3>
        <p>Les rivalités s'affichent sur le profil joueur uniquement après un certain nombre de matchs :</p>
        <ul>
            <li><b>Némésis :</b> Le joueur contre qui le participant a <b>perdu au moins 5 fois</b>.</li>
            <li><b>Proie :</b> Le joueur contre qui le participant a <b>gagné au moins 5 fois</b>.</li>
        </ul>

        <h3 style='color: #00f3ff; font-family: Orbitron;'>🐉 LES BOSS DE LIGUE</h3>
        <p>Invoquer un Boss permet de créer un événement communautaire autour d'un joueur ciblé.</p>
        <ul>
            <li><b>Points de Vie (PV) :</b> Chaque défaite du Boss lui fait perdre 1 PV. À 0 PV, il est vaincu.</li>
            <li><b>Victoires (Coupes) :</b> Le Boss gagne 1 coupe par victoire. S'il atteint l'objectif, il gagne son défi.</li>
            <li><b>Règle d'or :</b> Un joueur ne peut tenter sa chance contre le Boss qu'<b>une seule fois par semaine</b>.</li>
            <li><b>Récompense :</b> Si le Boss survit jusqu'au Reset du mardi, ou s'il remplit son objectif de coupes, il gagne +3.0 XP.</li>
        </ul>

        <h3 style='color: #00f3ff; font-family: Orbitron;'>🎯 LES CONTRATS (TUEURS À GAGES)</h3>
        <p>Le générateur crée une boucle d'assassinats sur un jeu spécifique (ex: A traque B, B traque C, C traque A).</p>
        <ul>
            <li>La cible du joueur s'affiche sur son profil. S'il est l'heureux chasseur et qu'il bat sa cible, <b>le contrat est rempli !</b></li>
            <li>La cible vaincue est éliminée du jeu des tueurs à gages.</li>
            <li>Le vainqueur hérite de la cible de sa victime (Si A bat B, A doit maintenant traquer C).</li>
        </ul>

        <h3 style='color: #00f3ff; font-family: Orbitron;'>📈 POINTS D'EXPÉRIENCE (XP) ET BONUS</h3>
        <p>L'XP de base (modifiable dans l'onglet "Saison, Paramètres & Niveaux") s'enrichit automatiquement de bonus cachés :</p>
        <ul>
            <li><b>Bonus de Premier Match :</b> Accordé pour le tout premier match de la journée.</li>
            <li><b>Bonus de Première Rencontre :</b> Accordé la première fois qu'un joueur en affronte un autre dans la journée.</li>
            <li><b>Bonus Underdog :</b> +0.5 XP si l'on bat un joueur mieux classé (Niveau supérieur).</li>
            <li><b>Malus Surclassement :</b> -0.5 XP si l'on s'acharne sur un joueur beaucoup plus faible (-2 niveaux ou pire).</li>
        </ul>
        """
        
        lbl_aide = QLabel(aide_text)
        lbl_aide.setWordWrap(True)
        lbl_aide.setStyleSheet("color: #e0f7fa; font-family: 'Rajdhani'; font-size: 16px; line-height: 1.5;")
        lbl_aide.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        lay.addWidget(lbl_aide)
        lay.addStretch()
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
# </VALIDATED>
    def _change_admin_pin(self):
        new_pin = self.edit_new_pin.text().strip()
        if not new_pin:
            QMessageBox.warning(self, "Erreur", "Le code PIN ne peut pas être vide.")
            return
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE systeme SET valeur = ? WHERE cle = 'admin_pin'", (new_pin,))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Sécurité", "Code PIN mis à jour avec succès.")
        self.edit_new_pin.clear()

    def _save_star_settings(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE systeme SET valeur = ? WHERE cle = 'icon_star_normale'", (self.combo_star_n.currentText(),))
        cursor.execute("UPDATE systeme SET valeur = ? WHERE cle = 'icon_star_pourpre'", (self.combo_star_p.currentText(),))
        cursor.execute("UPDATE systeme SET valeur = ? WHERE cle = 'icon_star_couronne'", (self.combo_star_c.currentText(),))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Visuels", "Paramètres des étoiles enregistrés avec succès.")

    def _load_events_data(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()

        self.combo_boss_joueur.clear()
        self.combo_boss_jeu.clear()
        self.combo_tueur_jeu.clear()

        cursor.execute("SELECT id, surnom, nom FROM joueurs ORDER BY surnom ASC")
        for row in cursor.fetchall():
            nom_aff = row['surnom'] if row['surnom'] else row['nom']
            self.combo_boss_joueur.addItem(nom_aff, row['id'])

        cursor.execute("SELECT id, nom FROM jeux WHERE actif = 1 ORDER BY nom ASC")
        for row in cursor.fetchall():
            self.combo_boss_jeu.addItem(row['nom'], row['id'])
            self.combo_tueur_jeu.addItem(row['nom'], row['id'])

        cursor.execute('''
            SELECT b.id, j.surnom, j.nom as j_nom, jx.nom as jeu_nom, b.pv_actuels, b.pv_max, b.statut 
            FROM event_boss b
            JOIN joueurs j ON b.joueur_id = j.id
            JOIN jeux jx ON b.jeu_id = jx.id
            ORDER BY b.id DESC
        ''')
        bosses = cursor.fetchall()
        self.table_boss.setRowCount(0)
        for row_idx, b in enumerate(bosses):
            self.table_boss.insertRow(row_idx)
            self.table_boss.setItem(row_idx, 0, QTableWidgetItem(str(b['id'])))
            surnom = b['surnom'] if b['surnom'] else b['j_nom']
            self.table_boss.setItem(row_idx, 1, QTableWidgetItem(surnom))
            self.table_boss.setItem(row_idx, 2, QTableWidgetItem(b['jeu_nom']))
            self.table_boss.setItem(row_idx, 3, QTableWidgetItem(f"{b['pv_actuels']}/{b['pv_max']}"))
            self.table_boss.setItem(row_idx, 4, QTableWidgetItem(b['statut']))

        cursor.execute('''
            SELECT jx.nom as jeu_nom, 
                   (SELECT COALESCE(surnom, nom) FROM joueurs WHERE id = t.chasseur_id) as chasseur,
                   (SELECT COALESCE(surnom, nom) FROM joueurs WHERE id = t.cible_id) as cible
            FROM event_tueurs t
            JOIN jeux jx ON t.jeu_id = jx.id
            WHERE t.statut = 'ACTIF'
        ''')
        contrats = cursor.fetchall()
        self.table_contrats.setRowCount(0)
        for row_idx, c in enumerate(contrats):
            self.table_contrats.insertRow(row_idx)
            self.table_contrats.setItem(row_idx, 0, QTableWidgetItem(c['jeu_nom']))
            self.table_contrats.setItem(row_idx, 1, QTableWidgetItem(c['chasseur']))
            self.table_contrats.setItem(row_idx, 2, QTableWidgetItem(c['cible']))

        conn.close()

    def _save_boss(self):
        joueur_id = self.combo_boss_joueur.currentData()
        jeu_id = self.combo_boss_jeu.currentData()
        pv = self.spin_boss_pv.value()
        coupes = self.spin_boss_coupes.value()
        date_fin = self.date_boss_fin.date().toString("yyyy-MM-dd")

        if not joueur_id or not jeu_id:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un joueur et un jeu.")
            return

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO event_boss (joueur_id, jeu_id, pv_max, pv_actuels, victoires_requises, victoires_actuelles, date_fin, statut)
                VALUES (?, ?, ?, ?, ?, 0, ?, 'ACTIF')
            ''', (joueur_id, jeu_id, pv, pv, coupes, date_fin))
            conn.commit()
            QMessageBox.information(self, "Succès", "Nouveau Boss invoqué avec succès !")
            self._load_events_data()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'invoquer le Boss : {e}")
        finally:
            conn.close()

    def _generate_contrats(self):
        jeu_id = self.combo_tueur_jeu.currentData()
        if not jeu_id:
            return

        msg = "Attention, générer de nouveaux contrats annulera tous les contrats actifs pour ce jeu.\nContinuer ?"
        box = QMessageBox.question(self, "Le Destin", msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if box == QMessageBox.StandardButton.Yes:
            self.mechanics.generer_contrats_tueurs(jeu_id)
            QMessageBox.information(self, "Succès", "Les contrats ont été distribués !")
            self._load_events_data()

    def _reset_saison(self):
        box = QMessageBox.question(self, "RESET TOTAL DE LA SAISON", 
                                   "ATTENTION\n\nVoulez-vous vraiment remettre toute la ligue à zéro ?\n\n"
                                   "• Ce qui sera GARDÉ : Les noms des joueurs, les avatars, et la liste des jeux.\n"
                                   "• Ce qui sera EFFACÉ : Tous les matchs, l'XP, les niveaux, les étoiles, et les lots en attente.\n\n"
                                   "Cette action est irréversible !", 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if box == QMessageBox.StandardButton.Yes:
            success = self.mechanics.reset_season()
            if success:
                QMessageBox.information(self, "Nouvelle Saison", "La ligue a été remise à zéro avec succès ! Bonne nouvelle saison !")
                self._load_joueurs()
            else:
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue lors du Reset de la base de données.")

    def _load_parametres(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT cle, valeur FROM parametres_xp")
        params = cursor.fetchall()
        conn.close()

        self.table_params.setRowCount(0)
        for row_idx, param in enumerate(params):
            self.table_params.insertRow(row_idx)
            item_cle = QTableWidgetItem(param["cle"])
            item_cle.setFlags(item_cle.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_params.setItem(row_idx, 0, item_cle)
            self.table_params.setItem(row_idx, 1, QTableWidgetItem(str(param["valeur"])))

    def _save_parametres(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            for row in range(self.table_params.rowCount()):
                cle = self.table_params.item(row, 0).text()
                valeur = float(self.table_params.item(row, 1).text())
                cursor.execute("UPDATE parametres_xp SET valeur = ? WHERE cle = ?", (valeur, cle))
            conn.commit()
            QMessageBox.information(self, "Succès", "Modificateurs d'XP mis à jour.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Valeur invalide (utilisez des points pour les décimales) : {str(e)}")
        finally:
            conn.close()

    def _load_niveaux(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, ordre, nom, xp_min, icone FROM niveaux ORDER BY ordre ASC")
        niveaux = cursor.fetchall()
        conn.close()

        self.table_niveaux.setRowCount(0)
        for row_idx, niv in enumerate(niveaux):
            self.table_niveaux.insertRow(row_idx)
            self.table_niveaux.setItem(row_idx, 0, QTableWidgetItem(str(niv["id"])))
            
            item_ordre = QTableWidgetItem(str(niv["ordre"]))
            item_ordre.setFlags(item_ordre.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_niveaux.setItem(row_idx, 1, item_ordre)
            
            self.table_niveaux.setItem(row_idx, 2, QTableWidgetItem(niv["nom"]))
            self.table_niveaux.setItem(row_idx, 3, QTableWidgetItem(str(niv["xp_min"])))
            
            item_icone = QTableWidgetItem(niv["icone"])
            item_icone.setFlags(item_icone.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_niveaux.setItem(row_idx, 4, item_icone)

    def _save_niveaux(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            for row in range(self.table_niveaux.rowCount()):
                niv_id = int(self.table_niveaux.item(row, 0).text())
                nom = self.table_niveaux.item(row, 2).text()
                xp_min = float(self.table_niveaux.item(row, 3).text())
                cursor.execute("UPDATE niveaux SET nom = ?, xp_min = ? WHERE id = ?", (nom, xp_min, niv_id))
            conn.commit()
            QMessageBox.information(self, "Succès", "Niveaux mis à jour avec succès.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {str(e)}")
        finally:
            conn.close()

    def _change_icon_niveau(self):
        selected_row = self.table_niveaux.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Sélection requise", "Veuillez sélectionner un niveau dans le tableau.")
            return

        niv_id = int(self.table_niveaux.item(selected_row, 0).text())
        file_path, _ = QFileDialog.getOpenFileName(self, "Choisir une Icône de Niveau", "", "Images (*.png *.svg)")
        
        if file_path:
            nom_fichier = os.path.basename(file_path)
            dest_path = os.path.join(self.icones_dir, nom_fichier)
            if file_path != dest_path:
                try:
                    shutil.copy2(file_path, dest_path)
                except Exception as e:
                    QMessageBox.warning(self, "Erreur", f"Impossible de copier l'image : {str(e)}")
                    return

            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE niveaux SET icone = ? WHERE id = ?", (nom_fichier, niv_id))
            conn.commit()
            conn.close()

            self._load_niveaux()
            QMessageBox.information(self, "Succès", f"Nouvelle icône assignée : {nom_fichier}")

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            #admin_panel { background-color: #050505; }
            #admin_title { color: #bc13fe; font-family: 'Orbitron'; font-size: 32px; font-weight: 900; letter-spacing: 2px; }
            #mode_edition_label { color: #00f3ff; font-family: 'Orbitron'; font-size: 20px; font-weight: bold; margin-bottom: 10px; }
            QLabel { color: #e0f7fa; font-family: 'Rajdhani'; font-size: 16px; font-weight: bold; }
            QLineEdit, QSpinBox, QDateEdit, QComboBox { background-color: #141928; color: white; border: 1px solid rgba(0, 243, 255, 0.3); border-radius: 5px; padding: 8px; font-family: 'Rajdhani'; font-size: 16px; }
            QCheckBox { color: white; font-family: 'Rajdhani'; font-size: 16px; padding: 5px;}
            QGroupBox { color: #00f3ff; font-family: 'Orbitron'; font-weight: bold; border: 1px solid rgba(0, 243, 255, 0.3); border-radius: 5px; margin-top: 15px; padding-top: 15px;}
            QPushButton { background-color: rgba(188, 19, 254, 0.2); color: white; border: 1px solid #bc13fe; padding: 10px; border-radius: 5px; font-family: 'Rajdhani'; font-size: 16px; font-weight: bold; margin-top: 15px;}
            QPushButton:hover { background-color: #bc13fe; }
            QTableWidget { background-color: #050505; color: white; gridline-color: rgba(0, 243, 255, 0.3); font-family: 'Rajdhani'; font-size: 14px; }
            QHeaderView::section { background-color: rgba(20, 25, 40, 0.9); color: #00f3ff; font-weight: bold; border: 1px solid rgba(0, 243, 255, 0.3); }
            QTabWidget::pane { border: 1px solid rgba(0, 243, 255, 0.3); background-color: rgba(20, 25, 40, 0.6); border-radius: 5px; }
            QTabBar::tab { background-color: #050505; color: #e0f7fa; font-family: 'Rajdhani'; font-size: 16px; padding: 10px 20px; border: 1px solid rgba(0, 243, 255, 0.3); border-bottom: none; border-top-left-radius: 5px; border-top-right-radius: 5px; margin-right: 2px;}
            QTabBar::tab:selected { background-color: rgba(0, 243, 255, 0.1); color: #00f3ff; border: 1px solid #00f3ff; border-bottom: none; }
        """)

    def _create_backup(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%M")
        default_name = f"backup_ligue_{timestamp}.db"
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer la sauvegarde", 
                                                   default_name, "SQLite DB (*.db)")
        if file_path:
            try:
                shutil.copy2(self.db.db_name, file_path)
                QMessageBox.information(self, "Sauvegarde Réussie", f"La base de données a été sauvegardée :\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de créer la sauvegarde : {e}")

    def _restore_backup(self):
        msg = "ATTENTION\n\nRestaurer une sauvegarde va écraser TOUTES les données actuelles.\n\nContinuer ?"
        box = QMessageBox.question(self, "Confirmation de Restauration", msg, 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if box == QMessageBox.StandardButton.Yes:
            file_path, _ = QFileDialog.getOpenFileName(self, "Choisir la sauvegarde à restaurer", 
                                                       "", "SQLite DB (*.db)")
            if file_path:
                try:
                    shutil.copy2(file_path, self.db.db_name)
                    QMessageBox.information(self, "Restauration Réussie", 
                                            "La base de données a été restaurée.\nL'application va se fermer. Relance-la pour appliquer les changements.")
                    import sys
                    sys.exit()
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Échec de la restauration : {e}")
# <VALIDATED>