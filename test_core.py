import sqlite3
# Assure-toi que le nom de la BDD correspond au tien
conn = sqlite3.connect("ligue_data.db") 
cursor = conn.cursor()
cursor.execute("UPDATE systeme SET valeur = '2000-01-01' WHERE cle = 'dernier_reset_mardi'")
conn.commit()
conn.close()
print("Voyage dans le temps effectué ! Lance ton application.")