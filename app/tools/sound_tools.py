# app/tools/sound_tools.py

import os
import random
from langchain.tools import tool

# Initialize pygame mixer (optional — not needed for web/server mode)
try:
    import pygame
    pygame.mixer.init()
    _PYGAME_AVAILABLE = True
except (ImportError, Exception):
    _PYGAME_AVAILABLE = False

# Path to sounds directory
_SOUNDS_DIR = os.path.join(os.path.dirname(__file__), "sounds")


def _play_sound(filename):
    """Play an MP3 file from the sounds directory."""
    if not _PYGAME_AVAILABLE:
        return
    filepath = os.path.join(_SOUNDS_DIR, filename)
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
    except Exception as e:
        print(f"Warning: Could not play sound {filename}: {e}")


@tool
def dog_bark():
    """Use when scammer becomes impatient or aggressive."""
    print("[SOUND_EFFECT: DOG_BARKING - Poupoune barking loudly]")
    _play_sound("dog-barking.mp3")
    return "[SOUND_EFFECT: DOG_BARKING - Poupoune barking loudly]"


@tool
def doorbell():
    """Use when interruption at the door."""
    print("[SOUND_EFFECT: DOORBELL - Amazon delivery arrives]")
    _play_sound("doorbell.mp3")
    return "[SOUND_EFFECT: DOORBELL - Amazon delivery arrives]"


@tool
def coughing_fit():
    """Simulate a 10 second coughing fit."""
    print("[SOUND_EFFECT: COUGHING_FIT - Jeanne coughing intensely]")
    _play_sound("coughing.mp3")
    return "[SOUND_EFFECT: COUGHING_FIT - Jeanne coughing intensely]"




def _dog_bark():
    print("[SOUND_EFFECT: DOG_BARKING - Poupoune barking loudly]")
    _play_sound("dog-barking.mp3")


def _doorbell():
    print("[SOUND_EFFECT: DOORBELL - Amazon delivery arrives]")
    _play_sound("doorbell.mp3")


def _coughing_fit():
    print("[SOUND_EFFECT: COUGHING_FIT - Jeanne coughing intensely]")
    _play_sound("coughing.mp3")


_ALL_SOUNDS = [_dog_bark, _doorbell, _coughing_fit]

# Mapping from tag names to sound files
SOUND_TAGS = {
    "DOG_BARK": "dog-barking.mp3",
    "DOORBELL": "doorbell.mp3",
    "COUGHING_FIT": "coughing.mp3",
}


def play_sound_by_name(tag_name):
    """Play a sound effect by its tag name."""
    filename = SOUND_TAGS.get(tag_name)
    if filename:
        _play_sound(filename)


def play_random_sound():
    """Play a random sound effect."""
    sound = random.choice(_ALL_SOUNDS)
    sound()
