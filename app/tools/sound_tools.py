# app/tools/sound_tools.py

from langchain.tools import tool


@tool
def dog_bark():
    """Use when scammer becomes impatient or aggressive."""
    return "[SOUND_EFFECT: DOG_BARKING - Poupoune barking loudly]"


@tool
def doorbell():
    """Use when interruption at the door."""
    return "[SOUND_EFFECT: DOORBELL - Amazon delivery arrives]"


@tool
def coughing_fit():
    """Simulate a 10 second coughing fit."""
    return "[SOUND_EFFECT: COUGHING_FIT - Jeanne coughing intensely]"


@tool
def tv_background():
    """Increase TV volume in the background."""
    return "[SOUND_EFFECT: TV_BACKGROUND - Les Feux de l'Amour playing loudly]"
