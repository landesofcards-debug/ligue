# <VALIDATED>
import random
from datetime import datetime, timedelta

class LeagueMechanics:
    """
    Contrôleur gérant la logique mathématique de la ligue.
    Intègre les Paliers, le 1v1, le 2v2, le Multijoueur, le Shuffle Bag et le Reset Hebdomadaire.
    """

    def __init__(self, db_manager):
        self.db = db_manager
        self._init_hebdo_system()

    def _init_hebdo_system(self):
        """Initialise la table de suivi hebdomadaire et déclenche le reset du mardi si nécessaire."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suivi_etoiles_hebdo (
                joueur_id INTEGER PRIMARY KEY,
                presence_donnee BOOLEAN DEFAULT 0,
                diversite_donnee BOOLEAN DEFAULT 0,
                serie_donnee BOOLEAN DEFAULT 0,
                FOREIGN KEY (joueur_id) REFERENCES joueurs(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("SELECT valeur FROM systeme WHERE cle = 'dernier_reset_mardi'")
        row = cursor.fetchone()
        
        maintenant = datetime.now()
        
        if not row:
            cursor.execute("INSERT INTO systeme (cle, valeur) VALUES ('dernier_reset_mardi', ?)", (maintenant.strftime("%Y-%m-%d"),))
        else:
            dernier_reset = datetime.strptime(row['valeur'], "%Y-%m-%d")
            
            jours_depuis_mardi = (maintenant.weekday() - 1) % 7
            dernier_mardi_passe = maintenant - timedelta(days=jours_depuis_mardi)
            dernier_mardi_passe = dernier_mardi_passe.replace(hour=0, minute=0, second=0, microsecond=0)
            
            if dernier_reset < dernier_mardi_passe:
                self._executer_reset_hebdomadaire(cursor, maintenant.strftime("%Y-%m-%d"))
                
        conn.commit()
        conn.close()

    def _executer_reset_hebdomadaire(self, cursor, nouvelle_date: str):
        """Exécute les calculs de fin de semaine (Ratio Positif) puis remet à zéro le suivi."""
        cursor.execute("SELECT valeur FROM systeme WHERE cle = 'dernier_reset_mardi'")
        old_reset = cursor.fetchone()['valeur']
        
        cursor.execute("SELECT id, surnom FROM joueurs")
        joueurs = cursor.fetchall()
        
        rapport_lignes = []
        
        for j in joueurs:
            joueur_id = j['id']
            pseudo = j['surnom']
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN (joueur1_id = ? AND resultat_j1 LIKE '%Victoire%') OR (joueur2_id = ? AND resultat_j2 LIKE '%Victoire%') THEN 1 ELSE 0 END) as victoires,
                    SUM(CASE WHEN (joueur1_id = ? AND resultat_j1 LIKE '%Défaite%') OR (joueur2_id = ? AND resultat_j2 LIKE '%Défaite%') THEN 1 ELSE 0 END) as defaites
                FROM matchs 
                WHERE (joueur1_id = ? OR joueur2_id = ?) AND date >= ?
            """, (joueur_id, joueur_id, joueur_id, joueur_id, joueur_id, joueur_id, old_reset))
            
            stats = cursor.fetchone()
            v = stats['victoires'] if stats['victoires'] else 0
            d = stats['defaites'] if stats['defaites'] else 0
            
            if v > d:
                self._ajouter_etoiles(cursor, joueur_id, 1)
                rapport_lignes.append(f"⭐ {pseudo.upper()} gagne 1 Étoile (Ratio positif: {v}V - {d}D)")
        
        cursor.execute("DELETE FROM suivi_etoiles_hebdo")
        cursor.execute("UPDATE systeme SET valeur = ? WHERE cle = 'dernier_reset_mardi'", (nouvelle_date,))
        
        cursor.execute("DELETE FROM event_boss_essais")
        
        cursor.execute("SELECT id, joueur_id FROM event_boss WHERE statut = 'ACTIF' AND date_fin < ?", (nouvelle_date,))
        bosses_expires = cursor.fetchall()
        for b in bosses_expires:
            cursor.execute("SELECT surnom FROM joueurs WHERE id = ?", (b['joueur_id'],))
            boss_pseudo = cursor.fetchone()['surnom']
            cursor.execute("UPDATE joueurs SET xp_total = xp_total + 3.0 WHERE id = ?", (b['joueur_id'],))
            cursor.execute("UPDATE event_boss SET statut = 'TERMINE' WHERE id = ?", (b['id'],))
            rapport_lignes.append(f"🐉 Le Boss {boss_pseudo.upper()} a survécu à la semaine ! (+3.0 XP)")

        if not rapport_lignes:
            rapport_lignes.append("Aucun joueur n'a eu un ratio positif et aucun Boss n'a survécu cette semaine.")

        texte_final = "\n".join(rapport_lignes)
        cursor.execute("INSERT OR REPLACE INTO systeme (cle, valeur) VALUES ('alerte_hebdo', '1')")
        cursor.execute("INSERT OR REPLACE INTO systeme (cle, valeur) VALUES ('rapport_hebdo', ?)", (texte_final,))

    def _ajouter_etoiles(self, cursor, joueur_id: int, nb_etoiles: int):
        cursor.execute("SELECT etoiles_normales, etoiles_pourpres, couronne_max FROM joueurs WHERE id = ?", (joueur_id,))
        j = cursor.fetchone()
        if not j: return
        
        normales = j['etoiles_normales'] + nb_etoiles
        pourpres = j['etoiles_pourpres']
        couronne = j['couronne_max']
        
        if normales >= 6:
            pourpres += normales // 6
            normales = normales % 6
            
        if pourpres >= 6:
            couronne += pourpres // 6 
            pourpres = pourpres % 6
            
        cursor.execute("""
            UPDATE joueurs 
            SET etoiles_normales = ?, etoiles_pourpres = ?, couronne_max = ? 
            WHERE id = ?
        """, (normales, pourpres, couronne, joueur_id))

    def evaluer_etoiles_direct(self, joueur_id: int):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("INSERT OR IGNORE INTO suivi_etoiles_hebdo (joueur_id) VALUES (?)", (joueur_id,))
        cursor.execute("SELECT presence_donnee, diversite_donnee, serie_donnee FROM suivi_etoiles_hebdo WHERE joueur_id = ?", (joueur_id,))
        suivi = cursor.fetchone()
        
        cursor.execute("SELECT valeur FROM systeme WHERE cle = 'dernier_reset_mardi'")
        debut_semaine = cursor.fetchone()['valeur']
        
        etoiles_a_ajouter = 0
        
        if not suivi['presence_donnee']:
            cursor.execute("SELECT COUNT(*) FROM matchs WHERE (joueur1_id = ? OR joueur2_id = ?) AND date >= ?", (joueur_id, joueur_id, debut_semaine))
            if cursor.fetchone()[0] >= 1:
                etoiles_a_ajouter += 1
                cursor.execute("UPDATE suivi_etoiles_hebdo SET presence_donnee = 1 WHERE joueur_id = ?", (joueur_id,))
                
        if not suivi['diversite_donnee']:
            cursor.execute("""
                SELECT COUNT(DISTINCT adv) FROM (
                    SELECT joueur2_id as adv FROM matchs WHERE joueur1_id = ? AND date >= ?
                    UNION
                    SELECT joueur1_id as adv FROM matchs WHERE joueur2_id = ? AND date >= ?
                )
            """, (joueur_id, debut_semaine, joueur_id, debut_semaine))
            if cursor.fetchone()[0] >= 3:
                etoiles_a_ajouter += 1
                cursor.execute("UPDATE suivi_etoiles_hebdo SET diversite_donnee = 1 WHERE joueur_id = ?", (joueur_id,))
                
        if not suivi['serie_donnee']:
            cursor.execute("""
                SELECT resultat_j1 as res, date FROM matchs WHERE joueur1_id = ? AND date >= ?
                UNION ALL
                SELECT resultat_j2 as res, date FROM matchs WHERE joueur2_id = ? AND date >= ?
                ORDER BY date DESC LIMIT 3
            """, (joueur_id, debut_semaine, joueur_id, debut_semaine))
            
            resultats = cursor.fetchall()
            if len(resultats) >= 3 and all('Victoire' in r['res'] for r in resultats):
                etoiles_a_ajouter += 1
                cursor.execute("UPDATE suivi_etoiles_hebdo SET serie_donnee = 1 WHERE joueur_id = ?", (joueur_id,))
                
        if etoiles_a_ajouter > 0:
            self._ajouter_etoiles(cursor, joueur_id, etoiles_a_ajouter)
            
        conn.commit()
        conn.close()

    def get_all_levels(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM niveaux ORDER BY xp_min ASC")
        niveaux = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return niveaux

    def get_level_info(self, current_xp: float) -> dict:
        niveaux = self.get_all_levels()
        if not niveaux:
            return {"ordre": 0, "nom": "Inconnu", "icone": "fa5s.question", "xp_min": 0}
        current_lvl = niveaux[0]
        for lvl in niveaux:
            if current_xp >= lvl["xp_min"]:
                current_lvl = lvl
            else:
                break
        return current_lvl
    
    def get_xp_progress(self, current_xp: float) -> dict:
        niveaux = self.get_all_levels()
        if not niveaux: return {"percent": 100, "min": 0, "max": 0}
        current_lvl_idx = 0
        for i, lvl in enumerate(niveaux):
            if current_xp >= lvl["xp_min"]:
                current_lvl_idx = i
            else:
                break
        if current_lvl_idx == len(niveaux) - 1:
            return {"percent": 100, "min": niveaux[current_lvl_idx]["xp_min"], "max": niveaux[current_lvl_idx]["xp_min"]}
        xp_min = niveaux[current_lvl_idx]["xp_min"]
        xp_max = niveaux[current_lvl_idx + 1]["xp_min"]
        range_xp = xp_max - xp_min
        percent = ((current_xp - xp_min) / range_xp) * 100 if range_xp > 0 else 100
        return {"percent": min(100, max(0, int(percent))), "min": xp_min, "max": xp_max}

    def _get_xp_params(self) -> dict:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT cle, valeur FROM parametres_xp")
        params = {row['cle']: row['valeur'] for row in cursor.fetchall()}
        conn.close()
        return params

    def calculate_xp(self, score_joueur: int, score_adversaire: int, 
                     xp_actuel_joueur: float, xp_actuel_adversaire: float,
                     est_boss: bool, est_boost: bool,
                     est_premier_match_jour: bool, est_premiere_rencontre_jour: bool) -> float:
        params = self._get_xp_params()
        pts = 0.0
        
        if score_joueur > score_adversaire:
            if score_joueur == 2 and score_adversaire == 0: pts = params.get('victoire_2_0', 3.0)
            elif score_joueur == 2 and score_adversaire == 1: pts = params.get('victoire_2_1', 2.0)
            else: pts = params.get('victoire_autre', 1.5)
            if est_boss: pts += params.get('bonus_boss', 3.0)
        elif score_joueur == score_adversaire: pts = params.get('egalite', 1.0)
        else: pts = params.get('defaite', 1.0)

        if est_premier_match_jour: pts += params.get('bonus_premier_match', 1.0)
        if est_premiere_rencontre_jour: pts += params.get('bonus_premiere_rencontre', 1.0)

        lvl_j = self.get_level_info(xp_actuel_joueur)["ordre"]
        lvl_a = self.get_level_info(xp_actuel_adversaire)["ordre"]
        if lvl_a > lvl_j: pts += params.get('bonus_underdog', 0.5)
        if lvl_j >= (lvl_a + 2): pts -= params.get('malus_surclassement', 0.5)
        
        if est_boost: pts *= params.get('multiplicateur_boost', 1.5)
        
        return max(0.0, pts)

    def calculate_xp_2v2(self, score_equipe_joueur: int, score_equipe_adverse: int, 
                         est_premier_match_jour: bool, est_premiere_rencontre_jour: bool) -> float:
        params = self._get_xp_params()
        pts = 0.0
        
        if score_equipe_joueur > score_equipe_adverse:
            if score_equipe_joueur == 2 and score_equipe_adverse == 0: pts = params.get('victoire_2_0', 3.0)
            elif score_equipe_joueur == 2 and score_equipe_adverse == 1: pts = params.get('victoire_2_1', 2.0)
            else: pts = params.get('victoire_autre', 1.5)
        elif score_equipe_joueur == score_equipe_adverse: pts = params.get('egalite', 1.0)
        else: pts = params.get('defaite', 1.0)

        if est_premier_match_jour: pts += params.get('bonus_premier_match', 1.0)
        if est_premiere_rencontre_jour: pts += params.get('bonus_premiere_rencontre', 1.0)
        
        pts += 1.0 
        
        return max(0.0, pts)
    
    def calculate_xp_multi(self, est_gagnant: bool, nb_adversaires: int, 
                           est_premier_match_jour: bool, est_premiere_rencontre_jour: bool) -> float:
        params = self._get_xp_params()
        pts = 0.0
        
        if est_gagnant:
            pts = 2.0 + (1.0 * nb_adversaires)
        else:
            pts = 0.5 + (0.5 * nb_adversaires)

        if est_premier_match_jour: pts += params.get('bonus_premier_match', 1.0)
        if est_premiere_rencontre_jour: pts += params.get('bonus_premiere_rencontre', 1.0)
        
        return max(0.0, pts)

    def get_player_stats(self, player_id: int):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT opponent_id, COUNT(*) as count FROM (
                SELECT joueur2_id as opponent_id FROM matchs WHERE joueur1_id = ? AND resultat_j1 LIKE 'Défaite%'
                UNION ALL
                SELECT joueur1_id as opponent_id FROM matchs WHERE joueur2_id = ? AND resultat_j2 LIKE 'Défaite%'
            ) GROUP BY opponent_id HAVING count >= 5 ORDER BY count DESC LIMIT 1
        """, (player_id, player_id))
        res_nem = cursor.fetchone()
        nemesis = "---"
        if res_nem:
            cursor.execute("SELECT surnom FROM joueurs WHERE id = ?", (res_nem['opponent_id'],))
            row = cursor.fetchone()
            if row: nemesis = f"{row['surnom']} ({res_nem['count']} déf.)"

        cursor.execute("""
            SELECT opponent_id, COUNT(*) as count FROM (
                SELECT joueur2_id as opponent_id FROM matchs WHERE joueur1_id = ? AND resultat_j1 LIKE 'Victoire%'
                UNION ALL
                SELECT joueur1_id as opponent_id FROM matchs WHERE joueur2_id = ? AND resultat_j2 LIKE 'Victoire%'
            ) GROUP BY opponent_id HAVING count >= 5 ORDER BY count DESC LIMIT 1
        """, (player_id, player_id))
        res_vic = cursor.fetchone()
        victime = "---"
        if res_vic:
            cursor.execute("SELECT surnom FROM joueurs WHERE id = ?", (res_vic['opponent_id'],))
            row = cursor.fetchone()
            if row: victime = f"{row['surnom']} ({res_vic['count']} vict.)"

        cursor.execute("SELECT id, nom FROM jeux")
        jeux = cursor.fetchall()
        ratios = []
        for j in jeux:
            cursor.execute("""
                SELECT resultat FROM (
                    SELECT resultat_j1 as resultat, date FROM matchs WHERE (joueur1_id = ? AND jeu_id = ?)
                    UNION ALL
                    SELECT resultat_j2 as resultat, date FROM matchs WHERE (joueur2_id = ? AND jeu_id = ?)
                )
                ORDER BY date DESC LIMIT 10
            """, (player_id, j['id'], player_id, j['id']))
            results = cursor.fetchall()
            if len(results) >= 3:
                wins = sum(1 for r in results if 'Victoire' in r['resultat'])
                pct = int((wins / len(results)) * 100)
                ratios.append(f"{j['nom']} : {pct}% ({wins}V/{len(results)}M)")

        conn.close()
        return {"nemesis": nemesis, "victime": victime, "ratios": "\n".join(ratios) if ratios else "Aucun ratio (min 3 matchs)"}

    def check_progression_rewards(self, player_id: int, old_xp: float, new_xp: float):
        niveaux = self.get_all_levels()
        paliers_gagnes = 0
        niveaux_gagnes = 0

        for i in range(len(niveaux) - 1):
            lvl_start_xp = niveaux[i]['xp_min']
            lvl_next_xp = niveaux[i+1]['xp_min']
            
            mid_xp = lvl_start_xp + ((lvl_next_xp - lvl_start_xp) / 2.0)

            if old_xp < mid_xp and new_xp >= mid_xp:
                paliers_gagnes += 1
                
            if old_xp < lvl_next_xp and new_xp >= lvl_next_xp:
                niveaux_gagnes += 1

        if paliers_gagnes > 0 or niveaux_gagnes > 0:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM lots WHERE joueur_id = ?", (player_id,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO lots (joueur_id) VALUES (?)", (player_id,))
                
            cursor.execute("""
                UPDATE lots 
                SET dus_niveau = dus_niveau + ?, dus_palier = dus_palier + ? 
                WHERE joueur_id = ?
            """, (niveaux_gagnes, paliers_gagnes, player_id))
            conn.commit()
            conn.close()
            return True
        return False

    def get_rewards_status(self, player_id: int) -> dict:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lots WHERE joueur_id = ?", (player_id,))
        lot = cursor.fetchone()
        
        if not lot:
            conn.close()
            return {"attente_niveaux": 0, "attente_paliers": 0, "jeux": []}
            
        attente_niveaux = lot['dus_niveau'] - lot['donnes_niveau']
        attente_paliers = lot['dus_palier'] - lot['donnes_palier']
        
        cursor.execute("""
            SELECT j.id, j.nom, j.recompense_niveau, j.recompense_palier, j.nb_cartes_promo 
            FROM jeux j
            JOIN joueurs_jeux jj ON j.id = jj.jeu_id
            WHERE jj.joueur_id = ? AND j.actif = 1
        """, (player_id,))
        jeux = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return {
            "attente_niveaux": max(0, attente_niveaux), 
            "attente_paliers": max(0, attente_paliers), 
            "jeux": jeux
        }

# <VALIDATED>
    def generate_rewards_preview(self, player_id: int) -> dict:
        status = self.get_rewards_status(player_id)
        niv_dus = status['attente_niveaux']
        pal_dus = status['attente_paliers']
        jeux = status['jeux']
        
        if niv_dus == 0 and pal_dus == 0:
            return {}

        conn = self.db.get_connection()
        cursor = conn.cursor()
        rapport = []
        drawn_cards_to_save = []

        if niv_dus > 0:
            recs = [f"{j['recompense_niveau']} ({j['nom']})" for j in jeux]
            if not recs: recs = ["Booster Standard"]
            rapport.append({"type": "NIVEAU", "titre": f"⭐ {niv_dus}x LOT(S) DE NIVEAU", "options": recs})

        if pal_dus > 0:
            for _ in range(pal_dus):
                if not jeux:
                    rapport.append({"type": "PALIER", "titre": "🎁 1x LOT DE PALIER", "options": ["Aucun jeu affilié"]})
                    continue
                
                options_tirage = []
                for j in jeux:
                    jeu_id = j['id']
                    nb_max = j['nb_cartes_promo']
                    
                    # --- FIX : Gestion des jeux sans cartes promos (ex: Naruto) ---
                    if nb_max <= 0:
                        recompense_fixe = j['recompense_palier'] if j['recompense_palier'] else "Lot de Palier"
                        options_tirage.append(f"{recompense_fixe} ({j['nom']})")
                        continue
                    # --------------------------------------------------------------
                    
                    cursor.execute("SELECT numero_tire FROM tirages_promos WHERE joueur_id = ? AND jeu_id = ?", (player_id, jeu_id))
                    deja_tires = set(row['numero_tire'] for row in cursor.fetchall())
                    
                    for dc in drawn_cards_to_save:
                        if dc['jeu_id'] == jeu_id and dc['type'] == 'DRAW':
                            deja_tires.add(dc['carte'])
                    
                    disponibles = set(range(1, nb_max + 1)) - deja_tires
                    
                    if not disponibles:
                        deja_tires = set([dc['carte'] for dc in drawn_cards_to_save if dc['jeu_id'] == jeu_id and dc['type'] == 'DRAW'])
                        disponibles = set(range(1, nb_max + 1)) - deja_tires
                        drawn_cards_to_save.append({"type": "RESET", "jeu_id": jeu_id})
                        
                    carte_gagnee = random.choice(list(disponibles))
                    drawn_cards_to_save.append({"type": "DRAW", "jeu_id": jeu_id, "carte": carte_gagnee})
                    options_tirage.append(f"Carte N°{carte_gagnee} ({j['nom']})")
                
                rapport.append({"type": "PALIER", "titre": "🎫 1x LOT DE PALIER", "options": options_tirage})

        conn.close()
        return {
            "rapport": rapport,
            "niv_dus": niv_dus,
            "pal_dus": pal_dus,
            "draws": drawn_cards_to_save
        }
# <VALIDATED>

    def confirm_rewards_claim(self, player_id: int, preview_data: dict):
        conn = self.db.get_connection()
        cursor = conn.cursor()

        for action in preview_data['draws']:
            if action['type'] == 'RESET':
                cursor.execute("DELETE FROM tirages_promos WHERE joueur_id = ? AND jeu_id = ?", (player_id, action['jeu_id']))
            elif action['type'] == 'DRAW':
                cursor.execute("INSERT INTO tirages_promos (joueur_id, jeu_id, numero_tire) VALUES (?, ?, ?)", (player_id, action['jeu_id'], action['carte']))

        cursor.execute("""
            UPDATE lots 
            SET donnes_niveau = donnes_niveau + ?, donnes_palier = donnes_palier + ? 
            WHERE joueur_id = ?
        """, (preview_data['niv_dus'], preview_data['pal_dus'], player_id))
        
        conn.commit()
        conn.close()

    def reset_season(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM matchs")
            cursor.execute("DELETE FROM tirages_promos")
            cursor.execute("DELETE FROM suivi_etoiles_hebdo")
            cursor.execute("DELETE FROM event_boss_essais")
            cursor.execute("DELETE FROM event_tueurs")
            cursor.execute("DELETE FROM event_boss")
            # Ajout de la remise à zéro de titre_rpg pour une propreté absolue
            cursor.execute("UPDATE joueurs SET xp_total = 0.0, niveau = 0, etoiles_normales = 0, etoiles_pourpres = 0, couronne_max = 0, titre_rpg = 'Novice'")
            cursor.execute("UPDATE lots SET dus_niveau = 0, donnes_niveau = 0, dus_palier = 0, donnes_palier = 0")
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def generer_contrats_tueurs(self, jeu_id: int):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM event_tueurs WHERE jeu_id = ? AND statut = 'ACTIF'", (jeu_id,))
        
        cursor.execute("SELECT joueur_id FROM joueurs_jeux WHERE jeu_id = ?", (jeu_id,))
        joueurs = [row['joueur_id'] for row in cursor.fetchall()]
        
        if len(joueurs) > 1:
            random.shuffle(joueurs)
            for i in range(len(joueurs)):
                chasseur = joueurs[i]
                cible = joueurs[(i + 1) % len(joueurs)]
                cursor.execute("INSERT INTO event_tueurs (chasseur_id, cible_id, jeu_id) VALUES (?, ?, ?)", 
                               (chasseur, cible, jeu_id))
        conn.commit()
        conn.close()

    def verifier_et_valider_contrat(self, vainqueur_id: int, perdant_id: int, jeu_id: int) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM event_tueurs WHERE chasseur_id = ? AND cible_id = ? AND jeu_id = ? AND statut = 'ACTIF'", 
                       (vainqueur_id, perdant_id, jeu_id))
        contrat = cursor.fetchone()
        
        if contrat:
            contrat_id = contrat['id']
            cursor.execute("UPDATE event_tueurs SET statut = 'TERMINE' WHERE id = ?", (contrat_id,))
            
            cursor.execute("SELECT id, cible_id FROM event_tueurs WHERE chasseur_id = ? AND jeu_id = ? AND statut = 'ACTIF'",
                           (perdant_id, jeu_id))
            contrat_perdant = cursor.fetchone()
            
            nouvelle_cible_id = None
            if contrat_perdant:
                nouvelle_cible_id = contrat_perdant['cible_id']
                cursor.execute("UPDATE event_tueurs SET statut = 'ANNULE' WHERE id = ?", (contrat_perdant['id'],))
            else:
                cursor.execute("SELECT joueur_id FROM joueurs_jeux WHERE jeu_id = ? AND joueur_id != ?", (jeu_id, vainqueur_id))
                cibles_potentielles = [row['joueur_id'] for row in cursor.fetchall()]
                if cibles_potentielles:
                    nouvelle_cible_id = random.choice(cibles_potentielles)

            if nouvelle_cible_id and nouvelle_cible_id != vainqueur_id:
                cursor.execute("INSERT INTO event_tueurs (chasseur_id, cible_id, jeu_id) VALUES (?, ?, ?)", 
                               (vainqueur_id, nouvelle_cible_id, jeu_id))
            
            conn.commit()
            conn.close()
            return True 
            
        conn.close()
        return False

    def executer_combat_boss(self, joueur_id: int, boss_id: int, victoire_joueur: bool) -> dict:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM event_boss WHERE id = ?", (boss_id,))
        boss = dict(cursor.fetchone())
        
        msg = ""
        
        cursor.execute("INSERT OR IGNORE INTO event_boss_essais (joueur_id, boss_id) VALUES (?, ?)", (joueur_id, boss_id))
        
        if victoire_joueur:
            nouveaux_pv = boss['pv_actuels'] - 1
            if nouveaux_pv <= 0:
                cursor.execute("UPDATE event_boss SET pv_actuels = 0, statut = 'VAINCU' WHERE id = ?", (boss_id,))
                msg = "LE BOSS EST VAINCU !"
            else:
                cursor.execute("UPDATE event_boss SET pv_actuels = ? WHERE id = ?", (nouveaux_pv, boss_id))
                msg = f"Le Boss perd 1 PV ! (Reste {nouveaux_pv} PV)"
        else:
            nouvelles_victoires = boss['victoires_actuelles'] + 1
            if nouvelles_victoires >= boss['victoires_requises']:
                cursor.execute("UPDATE event_boss SET victoires_actuelles = ?, statut = 'TERMINE' WHERE id = ?", (nouvelles_victoires, boss_id))
                cursor.execute("UPDATE joueurs SET xp_total = xp_total + 3.0 WHERE id = ?", (boss['joueur_id'],))
                msg = "LE BOSS ATTEINT SON OBJECTIF ET REMPORTE 3 XP !"
            else:
                cursor.execute("UPDATE event_boss SET victoires_actuelles = ? WHERE id = ?", (nouvelles_victoires, boss_id))
                msg = f"Le Boss gagne 1 Coupe ! ({nouvelles_victoires}/{boss['victoires_requises']})"
                
        conn.commit()
        conn.close()
        return {"succes": True, "message": msg, "vaincu": (victoire_joueur and nouveaux_pv <= 0)}
# <VALIDATED>