from libre_link_up import LibreLinkUpClient
import json

USERNAME = "katherinechabot@outlook.fr"
PASSWORD = "Monique1980!"

# Commence par cette URL. Si ça échoue, on essaiera une autre région.
URL = "https://api-ca.libreview.io"

client = LibreLinkUpClient(
    username=USERNAME,
    password=PASSWORD,
    url=URL,
    version="4.16.0",
)

print("Connexion en cours...")
client.login()
print("Connexion réussie.")

connections=client.get_connections()
print("Connections trouvées:", len(connections))
print(json.dumps(connections, indent=2,default=str))