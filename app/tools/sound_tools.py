from langchain.tools import tool

@tool
def dog_bark():
    """Play a dog barking sound. Use when the scammer becomes impatient or aggressive."""
    return "[SOUND_EFFECT: DOG_BARKING]"

@tool
def doorbell():
    """Play a doorbell sound. Use when there is an interruption at the door (e.g., delivery)."""
    return "[SOUND_EFFECT: DOORBELL]"

@tool
def coughing_fit():
    """Simulate a 10-second coughing fit. Use to interrupt or buy time."""
    return "[SOUND_EFFECT: COUGHING_FIT]"

@tool
def tv_background():
    """Increase TV volume in the background. Use to create noise and confusion."""
    return "[SOUND_EFFECT: TV_BACKGROUND]"
