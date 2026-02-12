import os
from app.agents.victim_agent import VictimAgent
from dotenv import load_dotenv



load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY manquante dans le fichier .env")

victim = VictimAgent(api_key)
print(victim.respond("Hello Jeanne, this is your bank calling. We need to verify your account information."))
print("Simulation started. Type 'exit' to stop.\n")

while True:
    user_input = input("Scammer: ")
    if user_input.lower() == "exit":
        break

    response = victim.respond(
        user_input=user_input,
        objective="Confuse the scammer and avoid giving any information.",
        constraint="None"
    )

    print(f"Jeanne: {response}\n")
