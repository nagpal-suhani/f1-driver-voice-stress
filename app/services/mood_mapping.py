"""
Maps continuous arousal / valence / dominance scores onto the three
labels the frontend needs: Calm, Stressed, Tired.

Thresholds are starting points based on how these dimensions are
usually interpreted (high arousal + low valence = distress/stress;
low arousal = low energy/tired). TUNE these against your real demo
clips once you have the model running -- the "right" numbers depend
on how this particular model scores your specific audio.
"""

from typing import Literal

MoodLabel = Literal["Calm", "Stressed", "Tired"]

# --- tunable thresholds ---
AROUSAL_HIGH = 0.6   # above this = energetic/activated voice
AROUSAL_LOW = 0.35   # below this = flat/low-energy voice
VALENCE_LOW = 0.45   # below this = negative-sounding tone


def map_to_mood(arousal: float, valence: float, dominance: float) -> MoodLabel:
    """
    Simple rule-based mapping. Order matters: check Stressed before Tired
    since a driver can sound both intense AND still not literally "tired".
    """
    if arousal >= AROUSAL_HIGH and valence <= VALENCE_LOW:
        return "Stressed"
    if arousal <= AROUSAL_LOW:
        return "Tired"
    return "Calm"


def mood_explanation(arousal: float, valence: float, dominance: float, mood: MoodLabel) -> str:
    """Optional: a short human-readable reason, handy for the frontend/demo."""
    if mood == "Stressed":
        return f"High energy ({arousal:.2f}) with negative tone ({valence:.2f})"
    if mood == "Tired":
        return f"Low energy in voice ({arousal:.2f})"
    return f"Balanced tone (arousal {arousal:.2f}, valence {valence:.2f})"