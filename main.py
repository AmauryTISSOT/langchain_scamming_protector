import json
import os
import tempfile
from app.agents.victim_agent import VictimAgent
from app.agents.director_agent import DirectorAgent
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
director = DirectorAgent(api_key)

# Director state
current_scam_type = "inconnu"
current_stage = "1"
current_objective = "Répondre lentement et gagner du temps."
conversation_log = []
script_hint = "banque"

# Initial greeting
victim.respond(
    "Bonjour Jeanne, ici votre banque. Nous devons vérifier vos informations de compte.",
    objective=current_objective
)
conversation_log.append({
    "role": "arnaqueur",
    "message": "Bonjour Jeanne, ici votre banque. Nous devons vérifier vos informations de compte."
})

print("\nSimulation started. Type 'exit' to stop, 'info' for Director state.\n")

while True:
    user_input = input("Arnaqueur: ")
    if user_input.lower() == "exit":
        break
    if user_input.lower() == "info":
        print(f"\n--- État du Directeur ---")
        print(f"  Type d'arnaque : {current_scam_type}")
        print(f"  Stade          : {current_stage}")
        print(f"  Objectif Jeanne: {current_objective}")
        print(f"  Tours          : {len(conversation_log)}")
        print()
        continue

    # Build history summary from victim's memory
    history_summary = victim.get_history_summary(max_turns=5)

    # Director analyzes and generates new objective
    director_result = director.update_objective(
        last_scammer=user_input,
        history_summary=history_summary,
        script_hint=script_hint
    )

    current_scam_type = director_result.get("scam_type", "autre")
    current_stage = director_result.get("stage", "?")
    stage_desc = director_result.get("stage_description", "")
    current_objective = director_result.get("new_objective", current_objective)

    print(f"\n  [Director] {current_scam_type} — stade {current_stage} ({stage_desc})")
    print(f"  [Objectif] {current_objective}\n")

    # Victim responds with Director's objective
    victim.respond(
        user_input=user_input,
        objective=current_objective,
        constraint="Aucune"
    )

    conversation_log.append({"role": "arnaqueur", "message": user_input})
    print()
