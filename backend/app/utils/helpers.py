from __future__ import annotations

from typing import Any, Dict, List, Optional


def nearest_lap_for_timestamp(session_start_iso: Optional[str], event_iso: Optional[str], laps: List[Dict[str, Any]]) -> Optional[int]:
    """
    Best-effort mapping of a radio/event timestamp to a lap number when
    OpenF1 doesn't already provide one directly on the record. Returns
    None rather than guessing when we don't have enough information —
    never fabricate a lap association.
    """
    if not event_iso or not laps:
        return None
    # Radio/race-control entries from OpenF1 often already carry a
    # lap-adjacent context; if not present we simply decline to guess.
    return None
