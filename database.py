# <VALIDATED>
import sqlite3
from datetime import datetime

class DatabaseManager:
    """
    Gestionnaire de la base de données SQLite.
    Intègre le système de paliers, lots différenciés, tirages promos et événements RPG.
    """

    def __init__(self, db_name="ligue_data.db"):
        self.db_name = db_name
        self._create_tables()
        self._init_default_settings()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        # CRUCIAL : Activation des clés étrangères pour que le ON DELETE CASCADE fonctionne
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS systeme (
                cle TEXT PRIMARY KEY,
                valeur TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jeux (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                nom TEXT NOT NULL UNIQUE, 
                icone TEXT, 
                actif BOOLEAN DEFAULT 1,
                recompense_niveau TEXT DEFAULT 'Booster',
                recompense_palier TEXT DEFAULT 'Carte Promo',
                nb_cartes_promo INTEGER DEFAULT 20
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS joueurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                nom TEXT NOT NULL UNIQUE, 
                surnom TEXT, 
                avatar TEXT, 
                titre_rpg TEXT DEFAULT 'Novice', 
                xp_total REAL DEFAULT 0.0, 
                niveau INTEGER DEFAULT 0,
                etoiles_normales INTEGER DEFAULT 0,
                etoiles_pourpres INTEGER DEFAULT 0,
                couronne_max BOOLEAN DEFAULT 0
            )
        ''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS joueurs_jeux (joueur_id INTEGER, jeu_id INTEGER, PRIMARY KEY (joueur_id, jeu_id), FOREIGN KEY (joueur_id) REFERENCES joueurs(id) ON DELETE CASCADE, FOREIGN KEY (jeu_id) REFERENCES jeux(id) ON DELETE CASCADE)''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matchs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                joueur1_id INTEGER, 
                joueur2_id INTEGER, 
                jeu_id INTEGER, 
                type_match TEXT DEFAULT '1v1',
                resultat_j1 TEXT NOT NULL, 
                resultat_j2 TEXT NOT NULL, 
                xp_j1 REAL DEFAULT 0.0, 
                xp_j2 REAL DEFAULT 0.0, 
                est_boost BOOLEAN DEFAULT 0, 
                FOREIGN KEY (joueur1_id) REFERENCES joueurs(id) ON DELETE CASCADE, 
                FOREIGN KEY (joueur2_id) REFERENCES joueurs(id) ON DELETE CASCADE, 
                FOREIGN KEY (jeu_id) REFERENCES jeux(id) ON DELETE CASCADE
            )
        ''')
        
        # --- TABLES ÉVÉNEMENTS RPG ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_boss (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                joueur_id INTEGER NOT NULL,
                jeu_id INTEGER NOT NULL,
                pv_max INTEGER DEFAULT 10,
                pv_actuels INTEGER DEFAULT 10,
                victoires_requises INTEGER DEFAULT 5,
                victoires_actuelles INTEGER DEFAULT 0,
                date_fin TIMESTAMP,
                statut TEXT DEFAULT 'ACTIF',
                FOREIGN KEY (joueur_id) REFERENCES joueurs(id) ON DELETE CASCADE,
                FOREIGN KEY (jeu_id) REFERENCES jeux(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_boss_essais (
                joueur_id INTEGER,
                boss_id INTEGER,
                PRIMARY KEY (joueur_id, boss_id),
                FOREIGN KEY (joueur_id) REFERENCES joueurs(id) ON DELETE CASCADE,
                FOREIGN KEY (boss_id) REFERENCES event_boss(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_tueurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chasseur_id INTEGER NOT NULL,
                cible_id INTEGER NOT NULL,
                jeu_id INTEGER NOT NULL,
                statut TEXT DEFAULT 'ACTIF',
                FOREIGN KEY (chasseur_id) REFERENCES joueurs(id) ON DELETE CASCADE,
                FOREIGN KEY (cible_id) REFERENCES joueurs(id) ON DELETE CASCADE,
                FOREIGN KEY (jeu_id) REFERENCES jeux(id) ON DELETE CASCADE
            )
        ''')
        # ---------------------------------------

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lots (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                joueur_id INTEGER UNIQUE, 
                dus_niveau INTEGER DEFAULT 0, 
                donnes_niveau INTEGER DEFAULT 0, 
                dus_palier INTEGER DEFAULT 0,
                donnes_palier INTEGER DEFAULT 0,
                etat_cadeaux TEXT DEFAULT 'A_JOUR', 
                FOREIGN KEY (joueur_id) REFERENCES joueurs(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tirages_promos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                joueur_id INTEGER,
                jeu_id INTEGER,
                numero_tire INTEGER,
                FOREIGN KEY (joueur_id) REFERENCES joueurs(id) ON DELETE CASCADE,
                FOREIGN KEY (jeu_id) REFERENCES jeux(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS niveaux (id INTEGER PRIMARY KEY AUTOINCREMENT, ordre INTEGER UNIQUE, nom TEXT NOT NULL, icone TEXT NOT NULL, xp_min REAL NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS parametres_xp (cle TEXT PRIMARY KEY, valeur REAL NOT NULL)''')

        conn.commit()
        conn.close()

    def _init_default_settings(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        settings = [
            ('dernier_reset_mardi', '2000-01-01'),
            ('admin_pin', '23560552'),
            ('icon_star_normale', 'fa5s.star'),
            ('icon_star_pourpre', 'fa5s.star'),
            ('icon_star_couronne', 'fa5s.star')
        ]
        for cle, val in settings:
            cursor.execute("INSERT OR IGNORE INTO systeme (cle, valeur) VALUES (?, ?)", (cle, val))

        cursor.execute("SELECT COUNT(*) FROM jeux")
        if cursor.fetchone()[0] == 0:
            jeux_defaut = [
                ('Magic', 'fa5s.fire', 1, 'Booster Standard', 'Carte Promo', 20),
                ('Yu-Gi-Oh!', 'fa5s.bolt', 1, 'Booster Standard', 'Carte Promo', 20),
                ('Pokemon', 'fa5s.leaf', 1, 'Booster Standard', 'Carte Promo', 20),
                ('Lorcana', 'fa5s.magic', 1, 'Booster Standard', 'Carte Promo', 20),
                ('One Piece', 'fa5s.anchor', 1, 'Booster Standard', 'Carte Promo', 20),
                ('Riftbound', 'fa5s.shield-alt', 1, 'Booster Standard', 'Carte Promo', 20)
            ]
            cursor.executemany("INSERT INTO jeux (nom, icone, actif, recompense_niveau, recompense_palier, nb_cartes_promo) VALUES (?, ?, ?, ?, ?, ?)", jeux_defaut)

        cursor.execute("SELECT COUNT(*) FROM niveaux")
        if cursor.fetchone()[0] == 0:
            niveaux_defaut = [
                (0, 'Novice', 'fa5s.fire', 0.0), (1, 'Apprenti', 'fa5s.scroll', 10.0), 
                (2, 'Aventurier', 'fa5s.hiking', 25.0), (3, 'Combattant', 'fa5s.khanda', 45.0), 
                (4, 'Vétéran', 'fa5s.shield-alt', 70.0), (5, 'Maître', 'fa5s.medal', 100.0),
                (6, 'Héroïque', 'fa5s.dragon', 135.0), (7, 'Légende', 'fa5s.crown', 175.0), 
                (8, 'Arpenteur', 'fa5s.meteor', 220.0), (9, 'Divin', 'fa5s.star', 321.0)
            ]
            cursor.executemany("INSERT INTO niveaux (ordre, nom, icone, xp_min) VALUES (?, ?, ?, ?)", niveaux_defaut)

        cursor.execute("SELECT COUNT(*) FROM parametres_xp")
        if cursor.fetchone()[0] == 0:
            params = [
                ('victoire_2_0', 3.0), ('victoire_2_1', 2.0), ('victoire_autre', 1.5),
                ('egalite', 1.0), ('defaite', 1.0), ('bonus_premier_match', 1.0),
                ('bonus_premiere_rencontre', 1.0), ('bonus_underdog', 0.5),
                ('malus_surclassement', 0.5), ('multiplicateur_boost', 1.5),
                ('bonus_boss', 3.0)
            ]
            cursor.executemany("INSERT INTO parametres_xp (cle, valeur) VALUES (?, ?)", params)
        
        conn.commit()
        conn.close()

    def supprimer_boss(self, boss_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM event_boss_essais WHERE boss_id = ?", (boss_id,))
            cursor.execute("DELETE FROM event_boss WHERE id = ?", (boss_id,))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False

    def purger_contrats_actifs(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE event_tueurs SET statut = 'ANNULE' WHERE statut = 'ACTIF'")
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
# <VALIDATED>