from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

DIRECTOR_SYSTEM = """
Tu es le Directeur de Scénario d'une simulation d'arnaque.
Tu ne parles jamais directement au scammer. Tu aides Jeanne Dubois à RESISTER.

Tu analyses le dernier message de l'arnaqueur et l'état de la discussion.
Tu compares avec un script d'arnaque type (banque / support technique / colis).
Tu dois produire un NOUVEL OBJECTIF COURT et ACTIONNABLE pour Jeanne,
afin de faire perdre du temps et éviter toute fuite d'information.

Règles :
- L'objectif doit être une phrase courte, actionnable, en français.
- Ne jamais conseiller de donner des infos sensibles.
- Si l'arnaqueur insiste, augmenter la diversion (bruitages, fausses manipulations, confusion).
- Si l'arnaqueur tente de faire installer un logiciel ou accéder au PC, faire semblant de ne pas trouver les boutons.

Format de sortie STRICT (JSON, sans texte autour) :
{{
  "scam_type": "...",
  "stage": "...",
  "new_objective": "..."
}}
"""


class DirectorAgent:
    def __init__(self, api_key: str):
        self.llm = ChatGroq(
            api_key=api_key,
            model="llama-3.1-8b-instant",
            temperature=0.2,      # plus “froid” = plus structuré
            streaming=False
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", DIRECTOR_SYSTEM),
            ("human", "Historique (résumé): {history_summary}\nDernier message arnaqueur: {last_scammer}\nType de script actuel: {script_hint}\n")
        ])

        self.chain = self.prompt | self.llm

    def update_objective(self, last_scammer: str, history_summary: str = "", script_hint: str = "banque"):
        resp = self.chain.invoke({
            "last_scammer": last_scammer,
            "history_summary": history_summary,
            "script_hint": script_hint
        })
        # resp.content contient le JSON
        return resp.content
