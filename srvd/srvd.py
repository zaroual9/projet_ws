from fastapi import FastAPI, HTTPException
import psycopg2
from math import radians, sin, cos, sqrt, atan2
import requests

app = FastAPI()

# Connexion à la base de données PostgreSQL
conn = psycopg2.connect(
    dbname="srvdb",
    user="postgres",
    password="12345",
    host="localhost"
)

cursor = conn.cursor()


def get_location_from_ip(ip):
    response = requests.get(f"")

    if response.status_code == 200:
        location_data = response.json()
        loc = location_data.get('loc')
        if loc:
            latitude, longitude = loc.split(',')
            return {
                "latitude": float(latitude),
                "longitude": float(longitude)
            }
        else:
            return None  # Gérer les erreurs de données ici
    else:
        return None  # Gérer les erreurs de requête ici


# Calcul de la distance entre deux coordonnées géographiques (lat/lon) avec la formule de Haversine
def calculate_distance(lat1, lon1, lat2, lon2):
    # Convertir les degrés en radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Calcul de la différence de latitude et de longitude
    d_lat = lat2 - lat1
    d_lon = lon2 - lon1

    # Calcul de la distance en utilisant la formule de Haversine
    a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    radius_of_earth = 6371  # Rayon moyen de la Terre en kilomètres
    distance = radius_of_earth * c

    return distance




@app.post("/choisir_serveur/")
async def choisir_serveur(file_name: str, ip_client: str):
    try:
        # Utilisation de requêtes préparées pour éviter l'injection SQL
        cursor.execute(
            "SELECT serveurs.*, serveurs.ip as server_ip FROM serveurs "
            "INNER JOIN files ON serveurs.id = files.serveur_id "
            "WHERE files.name = %s "
            "ORDER BY serveurs.vitesse DESC, serveurs.nbrq ASC",
            (file_name,)
        )
        serveurs_disponibles = cursor.fetchall()

        if len(serveurs_disponibles) >= 2:
            XYC = get_location_from_ip(ip_client)
            serveur = serveurs_disponibles[0]
            XYS = get_location_from_ip(serveur[2])
            j = 0
            min_dist = calculate_distance(XYC["latitude"], XYC["longitude"], XYS["latitude"], XYS["longitude"])

            for i in range(1, len(serveurs_disponibles)):
                serveur = serveurs_disponibles[i]
                XYS = get_location_from_ip(serveur[2])
                dist = calculate_distance(XYC["latitude"], XYC["longitude"], XYS["latitude"], XYS["longitude"])
                if dist < min_dist:
                    min_dist = dist
                    j = i

            return {"serveur": serveurs_disponibles[j][1]}  # Retourne le port du serveur le plus proche
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/serveurs/")
async def get_serveurs():
    try:
        cursor.execute("SELECT * FROM serveurs")
        serveurs = cursor.fetchall()
        return [{"id": row[0], "serveur_port": row[1], "ip": row[2], "vitesse": row[3], "nbrq": row[4]} for row in serveurs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
