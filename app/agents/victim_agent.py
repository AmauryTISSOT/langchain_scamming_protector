import os
import re
import time

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq
from app.tools.sound_tools import play_sound_by_name, SOUND_TAGS


class VictimAgent:
    def __init__(self, api_key):
        self.tts_client = None
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            try:
                from google.cloud import texttospeech
                from langchain_google_community._utils import get_client_info
                self.tts_client = texttospeech.TextToSpeechClient(
                    client_info=get_client_info(module="text-to-speech")
                )
                print("✓ Google TTS client initialized")
            except Exception as e:
                print(f"⚠ TTS client initialization failed: {e}")

        self.llm = ChatGroq(
            api_key=api_key,
            model="llama-3.1-8b-instant",
            temperature=0.7,
            streaming=False
        )

        self.tools = []

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            input_key="input",
            return_messages=True
        )

        sound_tags_list = ", ".join(SOUND_TAGS.keys())
        system_prompt = """
Tu es Jeanne Dubois, 78 ans, en conversation téléphonique. Tu parles UNIQUEMENT en français.

RÈGLES IMPORTANTES :
- Réponds toujours avec un dialogue naturel parlé
- Tu es légèrement confuse et un peu oublieuse
- Ne donne JAMAIS de mots de passe, d'informations bancaires ou de codes de vérification
- Tu ne comprends pas les termes techniques
- Si on te met la pression, change de sujet ou demande de l'aide
- Garde tes réponses conversationnelles et réalistes

EFFETS SONORES :
Tu peux insérer ces marqueurs DIRECTEMENT dans ton dialogue :
Sons : SOUND_TAGS_PLACEHOLDER
Silence : [PAUSE] (moment de silence, hésitation, réflexion)

Utilise-les naturellement au milieu de tes phrases pour simuler la vie réelle. Par exemple :
- "Ah oui, mon compte... [COUGHING_FIT] ...excusez-moi, où en étais-je ?"
- "Attendez, je cherche mon... [DOG_BARK] Oh Poupoune, tais-toi ! Pardon, vous disiez ?"
- "Mon numéro de... [DOORBELL] Oh, on sonne à la porte ! [PAUSE] Attendez une seconde..."
- "Je crois que c'était... [PAUSE] ...non, je ne me souviens plus."

RÈGLES POUR LES MARQUEURS :
- Insère au moins 1 marqueur de son par réponse
- Utilise [PAUSE] pour les hésitations et moments de réflexion
- Place-les au MILIEU de tes phrases, pas au début ni à la fin
- Après un son, réagis naturellement (excuse-toi, commente, perds le fil)
- N'utilise PAS d'autres descriptions d'actions (*tousse*, *aboie*, etc.), UNIQUEMENT les marqueurs entre crochets

Objectif : {objective}
Contrainte : {constraint}

Rappel : Parle naturellement comme Jeanne le ferait ! Uniquement du dialogue en français avec des marqueurs sonores.
            """.replace("SOUND_TAGS_PLACEHOLDER", sound_tags_list)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )

    # All special tags: sound effects + PAUSE
    _ALL_TAGS = list(SOUND_TAGS.keys()) + ["PAUSE"]
    _TAG_PATTERN = re.compile(r"(\[(?:" + "|".join(_ALL_TAGS) + r")\])", re.IGNORECASE)

    PAUSE_DURATION = 1.5  # seconds

    def respond(self, user_input, objective="Respond slowly.", constraint="None"):
        result = self.executor.invoke({
            "input": user_input,
            "objective": objective,
            "constraint": constraint
        })

        output = result["output"]

        # Split response into text segments and tags
        segments = self._TAG_PATTERN.split(output)

        for segment in segments:
            tag = segment.strip("[]").upper()
            if tag in SOUND_TAGS:
                # Play the sound effect
                print(f"  {segment}")
                play_sound_by_name(tag)
            elif tag == "PAUSE":
                # Silent pause
                print("  ...")
                time.sleep(self.PAUSE_DURATION)
            else:
                text = segment.strip()
                if not text:
                    continue
                # Print the text segment
                print(f"Jeanne: {text}")
                # Play TTS for this segment if available
                if self.tts_client:
                    try:
                        audio_path = self._synthesize(text)
                        if audio_path:
                            self._play_audio(audio_path)
                    except Exception as e:
                        print(f"TTS error: {e}")

        # Return clean text (without tags) for logging
        return self._TAG_PATTERN.sub("", output).strip()

    @staticmethod
    def _clean_for_tts(text):
        """Remove stage directions like (pause), (rire), *tousse* before TTS."""
        text = re.sub(r"\(.*?\)", "", text)
        text = re.sub(r"\*.*?\*", "", text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        return text

    def _synthesize(self, text):
        """Synthesize text to a temporary MP3 file using Google TTS."""
        import tempfile
        from google.cloud import texttospeech

        text = self._clean_for_tts(text)
        if not text:
            return None

        # SSML: lower pitch + slower rate to simulate an elderly voice
        escaped = (text.replace("&", "&amp;").replace("<", "&lt;")
                       .replace(">", "&gt;").replace('"', "&quot;"))
        ssml = (f'<speak><prosody pitch="-8st" rate="70%">'
                f'{escaped}</prosody></speak>')

        response = self.tts_client.synthesize_speech(
            input=texttospeech.SynthesisInput(ssml=ssml),
            voice=texttospeech.VoiceSelectionParams(
                language_code="fr-FR",
                name="fr-FR-Neural2-E",
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            ),
        )
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(response.audio_content)
            return f.name

    def _play_audio(self, audio_path):
        """Play an audio file using pygame and clean up afterwards."""
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.quit()
        except Exception as e:
            print(f"Warning: Could not play audio: {e}")
        finally:
            try:
                time.sleep(0.2)
                os.unlink(audio_path)
            except OSError:
                pass
