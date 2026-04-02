import sys
from PyQt6.QtWidgets import QApplication
from models.database import DatabaseManager
from controllers.league_mechanics import LeagueMechanics
from views.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    db_manager = DatabaseManager()
    mechanics = LeagueMechanics(db_manager)
    
    # On passe la BDD à la fenêtre principale
    window = MainWindow(db_manager)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

def main():
    # 1. Initialisation de l'application graphique
    app = QApplication(sys.argv)
    
    # 2. Initialisation du cœur du programme (BDD + Logique)
    db_manager = DatabaseManager()
    mechanics = LeagueMechanics(db_manager)
    
    # 3. Lancement de l'interface principale
    window = MainWindow()
    window.show()
    
    # 4. Exécution de la boucle principale
    sys.exit(app.exec())

if __name__ == "__main__":
    main()