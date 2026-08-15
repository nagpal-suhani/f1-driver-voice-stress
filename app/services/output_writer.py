"""
Single place that decides WHERE result JSON files go, so the stress
endpoint, the transcription endpoint, and the combined endpoint all
write into the same output_data/ folder with a consistent naming
scheme: {request_id}_{kind}.json

"""

import json
import os

# output_data/ lives at the project root, one level above app/
_THIS_FILE = os.path.abspath(__file__)
_APP_DIR = os.path.dirname(os.path.dirname(_THIS_FILE))       # .../app
_PROJECT_ROOT = os.path.dirname(_APP_DIR)                     # project root
OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "output_data")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_json(data: dict, request_id: str, kind: str) -> str:
    """
    Saves `data` as pretty-printed JSON to
    output_data/{request_id}_{kind}.json and returns the full path.

    kind should be short and consistent, e.g. "stress" or "transcript".
    """
    filename = f"{request_id}_{kind}.json"
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path