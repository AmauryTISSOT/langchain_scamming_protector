"""
Test script to find the best French voice for elderly Jeanne Dubois.

Usage:
    python test_voices.py

This script will:
1. Test all available French Neural2 voices
2. Generate a sample sentence for each
3. Display voice characteristics
"""

import os
import json
from google.cloud import texttospeech
from google.oauth2 import service_account
from dotenv import load_dotenv


def test_french_voices():
    """Test available French TTS voices."""

    load_dotenv()
    google_credentials = os.getenv("GOOGLE_CREDENTIALS")

    if not google_credentials:
        print("❌ GOOGLE_CREDENTIALS not found in .env")
        return

    try:
        credentials_dict = json.loads(google_credentials)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict
        )
        client = texttospeech.TextToSpeechClient(credentials=credentials)
    except Exception as e:
        print(f"❌ Failed to initialize TTS client: {e}")
        return

    # French voices to test
    voices_to_test = [
        ("fr-FR-Neural2-A", "French Female Neural2 A"),
        ("fr-FR-Neural2-B", "French Male Neural2 B"),
        ("fr-FR-Neural2-C", "French Female Neural2 C"),
        ("fr-FR-Neural2-D", "French Male Neural2 D"),
        ("fr-FR-Neural2-E", "French Female Neural2 E"),
        ("fr-FR-Wavenet-A", "French Female Wavenet A"),
        ("fr-FR-Wavenet-B", "French Male Wavenet B"),
        ("fr-FR-Wavenet-C", "French Female Wavenet C"),
        ("fr-FR-Wavenet-D", "French Male Wavenet D"),
    ]

    test_text = "Bonjour, je suis Jeanne Dubois. J'ai 78 ans et je ne comprends pas ces choses de technologie."
    print(f"\nTesting voices with text: \"{test_text}\"\n")
    print("=" * 70)

    for voice_name, voice_label in voices_to_test:
        try:
            synthesis_input = texttospeech.SynthesisInput(text=test_text)

            voice = texttospeech.VoiceSelectionParams(
                language_code="fr-FR",
                name=voice_name,
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
                if "A" in voice_name or "C" in voice_name or "E" in voice_name
                else texttospeech.SsmlVoiceGender.MALE,
            )

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )

            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            print(f"✓ {voice_name:20} | {voice_label}")
            print(f"  Audio size: {len(response.audio_content)} bytes")

        except Exception as e:
            print(f"✗ {voice_name:20} | ERROR: {str(e)[:50]}")

    print("\n" + "=" * 70)
    print("\n📝 RECOMMENDATION:")
    print(
        "- For elderly woman: Try fr-FR-Neural2-A, Neural2-C, or Wavenet-A"
    )
    print("- Update voice_name in GoogleTTSService.__init__() accordingly")
    print("- Test with main.py to verify immersion")


if __name__ == "__main__":
    test_french_voices()
