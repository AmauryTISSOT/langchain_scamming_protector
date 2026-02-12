import os, json
from dotenv import load_dotenv

from app.agents.victim_agent import VictimAgent
from app.agents.director_agent import DirectorAgent
from app.agents.audience_moderator_agent import AudienceModeratorAgent

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY manquante dans le fichier .env")

victim = VictimAgent(api_key)
director = DirectorAgent(api_key)
moderator = AudienceModeratorAgent(api_key)

print("Simulation started. Type 'exit' to stop.\n")

history_summary = ""      # simple au début (tu pourras faire un vrai résumé plus tard)
script_hint = "banque"
audience_constraint = "Aucune"
turn = 0

while True:
    user_input = input("Arnaqueur: ")
    if user_input.lower() == "exit":
        break

    # 1) Directeur met à jour l'objectif
    director_json = director.update_objective(
        last_scammer=user_input,
        history_summary=history_summary,
        script_hint=script_hint
    )
    try:
        director_data = json.loads(director_json)
        current_objective = director_data["new_objective"]
        script_hint = director_data.get("scam_type", script_hint)
    except Exception:
        # fallback si le JSON est mal formé
        current_objective = "Rester confuse, faire perdre du temps, ne rien révéler."

    # 2) Audience (tous les 3 tours par exemple)
    turn += 1
    if turn % 3 == 0:
        print("\n--- Audience: proposez des événements (ligne vide pour finir) ---")
        ideas = []
        while True:
            idea = input("> ")
            if idea.strip() == "":
                break
            ideas.append(idea)

        if ideas:
            mod_json = moderator.pick_three(
                context=f"Scam type: {script_hint}. Dernier message: {user_input}.",
                ideas=ideas
            )
            try:
                mod_data = json.loads(mod_json)
                choices = mod_data["choices"]

                print("\nVote (choisissez 1, 2 ou 3):")
                for i, c in enumerate(choices, 1):
                    print(f"{i}) {c['title']} — {c['effect']}")

                vote = input("Votre choix: ").strip()
                idx = int(vote) - 1 if vote in ["1","2","3"] else 0
                audience_constraint = choices[idx]["effect"]
            except Exception:
                audience_constraint = "Aucune"

    # 3) Victime répond
    response = victim.respond(
        user_input=user_input,
        objective=current_objective,
        constraint=audience_constraint
    )

    print(f"\n[Directeur] Objectif: {current_objective}")
    print(f"[Audience] Contrainte: {audience_constraint}")
    print(f"Jeanne: {response}\n")

    # 4) (Optionnel) reset contrainte après 1 tour
    audience_constraint = "Aucune"
