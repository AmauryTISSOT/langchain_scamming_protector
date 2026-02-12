import os
from app.agents.victim_agent import VictimAgent
from dotenv import load_dotenv



load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY manquante dans le fichier .env")

victim = VictimAgent(api_key)
# Message de démarrage (en français)
intro = "Bonjour madame Dubois, je suis du service sécurité de votre banque. Nous devons vérifier votre compte."
first_response = victim.respond(
    user_input=intro,
    objective="Gagner du temps, rester polie, faire semblant d'être confuse, et ne donner aucune information.",
    constraint="Aucune"
)

print(intro)
print(first_response+"\n")

while True:
    user_input = input("Scammer: ")
    if user_input.lower() == "exit":
        break

    response = victim.respond(
        user_input=user_input,
        objective="Confuse the scammer and avoid giving any information.",
        constraint="None"
    )

