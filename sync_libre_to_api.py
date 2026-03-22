from libre_link_up import LibreLinkUpClient
import requests
from datetime import datetime
import time
import os
from dotenv import load_dotenv

USERNAME = os.getenv("LIBRELINKUP_USERNAME")
PASSWORD = os.getenv("LIBRELINKUP_PASSWORD")
URL = os.getenv("LIBRELINKUP_URL")

API_URL = os.getenv("API_URL")
HEALTH_URL = os.getenv("HEALTH_URL")

if not USERNAME or not PASSWORD or not API_URL or not HEALTH_URL:
    raise ValueError("Variables d'environnement manquantes. Veuillez vérifier votre fichier .env")


def map_trend_arrow(trend_arrow: int) -> str:
    mapping = {
        1: "rising_quickly",
        2: "rising",
        3: "stable",
        4: "falling",
        5: "falling_quickly"
    }
    return mapping.get(trend_arrow, "unknown")


def convert_timestamp(raw_timestamp: str) -> str:
    dt = datetime.strptime(raw_timestamp, "%m/%d/%Y %I:%M:%S %p")
    return dt.isoformat()


while True:
    try:
        print("Lecture LibreLinkUp...")

        client = LibreLinkUpClient(
            username=USERNAME,
            password=PASSWORD,
            url=URL,
            version="4.16.0",
        )

        client.login()
        time.sleep(1)

        connections = client.get_connections()
        patient = connections["data"][0]
        gm = patient["glucoseMeasurement"]

        value = gm["Value"]
        timestamp = convert_timestamp(gm["Timestamp"])
        trend = map_trend_arrow(gm["TrendArrow"])

        payload = {
            "value": value,
            "timestamp": timestamp,
            "trend": trend,
            "source": "librelinkup"
        }

        print("Payload :", payload)

        health = requests.get(HEALTH_URL, timeout=60)
        print("Health status :", health.status_code)

        response = requests.post(API_URL, params=payload, timeout=60)
        print("Status :", response.status_code)
        print("Réponse :", response.text)

    except Exception as e:
        print("Erreur :", e)

    print("Prochaine lecture dans 5 minutes")
    time.sleep(300)

print("USERNAME", USERNAME)
print("PASSWORD", PASSWORD)
print("URL", URL)