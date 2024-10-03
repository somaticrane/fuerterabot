import os
import psycopg2
from urllib.parse import urlparse

# Ottieni la variabile d'ambiente DATABASE_URL da Heroku
DATABASE_URL = os.getenv('DATABASE_URL')

# Crea la connessione al database PostgreSQL
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

# Esegui una query per selezionare tutti i dati dalla tabella
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()

# Stampa i risultati
if rows:
    for row in rows:
        print(row)
else:
    print("Nessun dato trovato nel database.")

# Chiudi la connessione
cursor.close()
conn.close()

# Attendi che l'utente prema Enter prima di chiudere
input("Premi Enter per chiudere...")
