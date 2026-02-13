import json
import re

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

SCAM_SCRIPTS = {
    "banque": {
        "stages": {
            "1": {
                "name": "approche",
                "signals": ["banque", "compte", "sécurité", "vérification", "service client"],
                "objective": "Répondre poliment mais lentement, poser des questions sur l'identité de l'appelant."
            },
            "2": {
                "name": "vérification identité",
                "signals": ["nom", "date de naissance", "adresse", "numéro client", "identifiant"],
                "objective": "Faire semblant de chercher ses papiers, donner de fausses informations partielles, gagner du temps."
            },
            "3": {
                "name": "demande code",
                "signals": ["code", "mot de passe", "SMS", "confirmation", "valider", "OTP"],
                "objective": "Prétendre ne pas comprendre ce qu'est un code, confondre avec le code de la porte d'entrée, digresser."
            },
            "4": {
                "name": "pression",
                "signals": ["urgent", "bloquer", "fraude", "immédiat", "vite", "danger", "suspendre"],
                "objective": "S'inquiéter bruyamment, appeler le chien, faire tomber le téléphone, demander à rappeler plus tard."
            }
        }
    },
    "support_technique": {
        "stages": {
            "1": {
                "name": "alerte virus",
                "signals": ["virus", "ordinateur", "infecté", "Microsoft", "Windows", "alerte", "erreur"],
                "objective": "Demander ce qu'est un virus, confondre avec la grippe, parler de son ancien Minitel."
            },
            "2": {
                "name": "installer logiciel",
                "signals": ["télécharger", "installer", "TeamViewer", "AnyDesk", "lien", "site web"],
                "objective": "Faire semblant de ne pas trouver le navigateur, décrire l'écran de façon absurde, confondre les touches."
            },
            "3": {
                "name": "accès PC",
                "signals": ["écran", "cliquer", "bureau", "icône", "partage", "contrôle", "accès à distance"],
                "objective": "Décrire un écran imaginaire, cliquer sur les mauvais boutons, prétendre que l'écran est noir."
            },
            "4": {
                "name": "paiement",
                "signals": ["payer", "carte", "abonnement", "renouveler", "licence", "frais"],
                "objective": "Dire que c'est son fils qui gère l'argent, qu'elle n'a pas de carte, proposer un chèque par courrier."
            }
        }
    },
    "colis": {
        "stages": {
            "1": {
                "name": "notification",
                "signals": ["colis", "livraison", "poste", "Colissimo", "attente", "paquet"],
                "objective": "S'enthousiasmer pour le colis, demander ce que c'est, raconter ses dernières commandes."
            },
            "2": {
                "name": "paiement frais",
                "signals": ["frais", "douane", "taxes", "payer", "débloquer", "affranchissement"],
                "objective": "S'étonner des frais, demander pourquoi, raconter que de son temps les colis arrivaient sans frais."
            },
            "3": {
                "name": "données bancaires",
                "signals": ["carte", "numéro", "CVV", "expiration", "bancaire", "IBAN"],
                "objective": "Prétendre chercher sa carte, lire un faux numéro très lentement, se tromper plusieurs fois."
            }
        }
    }
}

DIRECTOR_SYSTEM = """Tu es le Directeur de Scénario d'une simulation d'arnaque.
Tu ne parles jamais directement au scammer. Tu aides Jeanne Dubois à RESISTER.

Tu analyses le dernier message de l'arnaqueur et l'état de la discussion.
Tu compares avec les scripts d'arnaque de référence ci-dessous.
Tu dois produire un NOUVEL OBJECTIF COURT et ACTIONNABLE pour Jeanne,
afin de faire perdre du temps et éviter toute fuite d'information.

SCRIPTS D'ARNAQUE DE RÉFÉRENCE :
{scam_scripts}

Règles :
- L'objectif doit être une phrase courte, actionnable, en français.
- Ne jamais conseiller de donner des infos sensibles.
- Si l'arnaqueur insiste, augmenter la diversion (bruitages, fausses manipulations, confusion).
- Si l'arnaqueur tente de faire installer un logiciel ou accéder au PC, faire semblant de ne pas trouver les boutons.
- Identifie le type d'arnaque et le stade actuel en te basant sur les signaux de détection.

Format de sortie STRICT (JSON uniquement, sans texte autour) :
{{"scam_type": "banque|support_technique|colis|autre", "stage": "1-4", "stage_description": "description courte du stade", "new_objective": "objectif actionnable pour Jeanne"}}
"""

DEFAULT_RESULT = {
    "scam_type": "autre",
    "stage": "1",
    "stage_description": "Introduction — type d'arnaque non identifié",
    "new_objective": "Répondre lentement, poser des questions, gagner du temps sans donner d'information personnelle."
}


def _format_scam_scripts():
    """Format SCAM_SCRIPTS into a readable string for the prompt."""
    lines = []
    for script_type, script in SCAM_SCRIPTS.items():
        lines.append(f"\n{script_type.upper()} :")
        for stage_num, stage in script["stages"].items():
            signals = ", ".join(stage["signals"])
            lines.append(f"  Stade {stage_num} ({stage['name']}) — Signaux : {signals}")
            lines.append(f"    → Objectif Jeanne : {stage['objective']}")
    return "\n".join(lines)


class DirectorAgent:
    def __init__(self, api_key: str):
        self.llm = ChatGroq(
            api_key=api_key,
            model="llama-3.1-8b-instant",
            temperature=0.2,
            streaming=False
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", DIRECTOR_SYSTEM),
            ("human",
             "Historique (résumé): {history_summary}\n"
             "Dernier message arnaqueur: {last_scammer}\n"
             "Type de script actuel: {script_hint}\n")
        ])

        self.chain = self.prompt | self.llm

    def update_objective(self, last_scammer: str, history_summary: str = "", script_hint: str = "banque") -> dict:
        try:
            resp = self.chain.invoke({
                "last_scammer": last_scammer,
                "history_summary": history_summary,
                "script_hint": script_hint,
                "scam_scripts": _format_scam_scripts()
            })
            return self._parse_response(resp.content)
        except Exception:
            return dict(DEFAULT_RESULT)

    @staticmethod
    def _parse_response(content: str) -> dict:
        """Extract JSON from LLM response with fallback."""
        match = re.search(r'\{[^{}]*\}', content)
        if not match:
            return dict(DEFAULT_RESULT)

        try:
            data = json.loads(match.group())
        except (json.JSONDecodeError, ValueError):
            return dict(DEFAULT_RESULT)

        required_keys = {"scam_type", "new_objective"}
        if not required_keys.issubset(data.keys()):
            return dict(DEFAULT_RESULT)

        if "stage" not in data:
            data["stage"] = "1"
        if "stage_description" not in data:
            data["stage_description"] = f"Stade {data['stage']}"

        return data
