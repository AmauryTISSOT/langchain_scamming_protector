import json
import os
import tempfile
from app.agents.victim_agent import VictimAgent
from dotenv import load_dotenv


load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY manquante dans le fichier .env")

# Setup Google TTS credentials from .env JSON string
google_credentials = os.getenv("GOOGLE_CREDENTIALS")
if google_credentials and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    try:
        creds_dict = json.loads(google_credentials)
        creds_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        json.dump(creds_dict, creds_file)
        creds_file.close()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_file.name
        print("✓ Google TTS credentials configured")
    except Exception as e:
        print(f"⚠ Could not configure Google TTS credentials: {e}")
        print("  Continuing without audio...\n")

victim = VictimAgent(api_key)
victim.respond("Bonjour Jeanne, ici votre banque. Nous devons vérifier vos informations de compte.")
print("\nSimulation started. Type 'exit' to stop.\n")

history_summary = ""      # simple au début (tu pourras faire un vrai résumé plus tard)
script_hint = "banque"
audience_constraint = "Aucune"
turn = 0

while True:
    user_input = input("Arnaqueur: ")
    if user_input.lower() == "exit":
        break

    victim.respond(
        user_input=user_input,
        objective="Embrouiller l'arnaqueur et ne donner aucune information personnelle.",
        constraint="Aucune"
    )
    print()
