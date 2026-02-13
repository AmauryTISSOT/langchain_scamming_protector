import os
import re
import base64

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq


SCAMMER_SYSTEM_PROMPT = """Tu es un arnaqueur professionnel au téléphone. Tu parles UNIQUEMENT en français.

Tu te fais passer pour le service sécurité de la banque de ta victime.

PROGRESSION EN 4 PHASES :
1. APPROCHE : Te présenter comme le service sécurité de la banque. Être poli et professionnel.
2. URGENCE : Signaler une transaction suspecte détectée sur le compte. Créer un sentiment d'urgence.
3. VÉRIFICATION : Demander des informations de vérification : nom complet, date de naissance, adresse.
4. EXTRACTION : Demander le numéro de carte bancaire, la date d'expiration et le code CVV.

RÈGLES IMPORTANTES :
- Réponds en 2-3 phrases maximum, pas plus.
- Parle en français naturel et professionnel.
- Ne révèle JAMAIS que tu es un arnaqueur.
- Augmente progressivement la pression si la victime hésite.
- Si la victime change de sujet, ramène-la poliment vers le sujet bancaire.
- Utilise des termes techniques bancaires pour paraître crédible.
- Si la victime résiste, insiste sur l'urgence (compte bientôt bloqué, transaction en cours).

Tu es en appel téléphonique avec la victime. Commence par te présenter si c'est le début de la conversation.
"""


class ScammerAgent:
    def __init__(self, api_key: str):
        self.tts_client = None
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            try:
                from google.cloud import texttospeech
                from langchain_google_community._utils import get_client_info
                self.tts_client = texttospeech.TextToSpeechClient(
                    client_info=get_client_info(module="text-to-speech")
                )
            except Exception:
                pass

        self.llm = ChatGroq(
            api_key=api_key,
            model="llama-3.1-8b-instant",
            temperature=0.8,
            streaming=False,
        )

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            input_key="input",
            return_messages=True,
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", SCAMMER_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])

        self.chain = prompt | self.llm

    def respond_web(self, last_victim_response: str):
        """Generate scammer response. Returns (segments, clean_text)."""
        # Save victim message to memory and invoke
        result = self.chain.invoke({
            "input": last_victim_response,
            "chat_history": self.memory.chat_memory.messages,
        })
        output = result.content

        # Update memory
        self.memory.chat_memory.add_user_message(last_victim_response)
        self.memory.chat_memory.add_ai_message(output)

        clean_text = self._clean_for_tts(output)

        seg = {"type": "text", "content": clean_text}
        if self.tts_client and clean_text:
            try:
                audio_bytes = self._synthesize_bytes(clean_text)
                if audio_bytes:
                    seg["tts_audio"] = base64.b64encode(audio_bytes).decode("ascii")
            except Exception:
                pass

        return [seg], clean_text

    def generate_opening(self):
        """Generate the scammer's opening message (no prior victim input)."""
        opening_input = "[Début de l'appel téléphonique. La personne décroche.]"
        result = self.chain.invoke({
            "input": opening_input,
            "chat_history": [],
        })
        output = result.content

        # Save to memory
        self.memory.chat_memory.add_user_message(opening_input)
        self.memory.chat_memory.add_ai_message(output)

        clean_text = self._clean_for_tts(output)

        seg = {"type": "text", "content": clean_text}
        if self.tts_client and clean_text:
            try:
                audio_bytes = self._synthesize_bytes(clean_text)
                if audio_bytes:
                    seg["tts_audio"] = base64.b64encode(audio_bytes).decode("ascii")
            except Exception:
                pass

        return [seg], clean_text

    def _synthesize_bytes(self, text):
        """Synthesize text to MP3 bytes with masculine voice."""
        from google.cloud import texttospeech

        if not text:
            return None

        escaped = (text.replace("&", "&amp;").replace("<", "&lt;")
                       .replace(">", "&gt;").replace('"', "&quot;"))
        ssml = f'<speak><prosody pitch="0st" rate="100%">{escaped}</prosody></speak>'

        response = self.tts_client.synthesize_speech(
            input=texttospeech.SynthesisInput(ssml=ssml),
            voice=texttospeech.VoiceSelectionParams(
                language_code="fr-FR",
                name="fr-FR-Neural2-D",
                ssml_gender=texttospeech.SsmlVoiceGender.MALE,
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            ),
        )
        return response.audio_content

    @staticmethod
    def _clean_for_tts(text):
        """Remove stage directions like (pause), *tousse* before TTS."""
        text = re.sub(r"\(.*?\)", "", text)
        text = re.sub(r"\*.*?\*", "", text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        return text
