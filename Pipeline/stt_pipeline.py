"""
The Silent Co-Driver — Speech-to-Text Pipeline
------------------------------------------------
Converts driver radio audio into a structured, timestamped transcript
that downstream teammates (mood/stress detection, lap-time correlation)
can consume.

Usage as a library:
    from stt_pipeline import transcribe_audio
    result = transcribe_audio("radio_clip.wav")

Usage as a CLI:
    python stt_pipeline.py radio_clip.wav

Output schema (JSON-serializable dict):
{
    "audio_file": "radio_clip.wav",
    "duration_sec": 12.4,
    "full_text": "Box this lap, box this lap, tyres are gone.",
    "language": "en",
    "segments": [
        {
            "id": 0,
            "start": 0.0,
            "end": 2.3,
            "text": "Box this lap, box this lap,",
            "avg_confidence": 0.94,
            "words": [
                {"word": "Box", "start": 0.0, "end": 0.3, "confidence": 0.98},
                ...
            ]
        },
        ...
    ]
}
"""

import argparse
import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WHISPER_MODEL_SIZE = "small"   # tiny/base/small/medium/large-v3. small = good accuracy/speed tradeoff for a hackathon
TARGET_SAMPLE_RATE = 16000     # Whisper expects 16kHz mono
RADIO_BANDPASS = (300, 3400)   # Hz — typical radio comms voice band; strips hiss/static outside speech range
LOW_CONFIDENCE_THRESHOLD = 0.55  # words below this get flagged for review


# ---------------------------------------------------------------------------
# Data classes for structured output
# ---------------------------------------------------------------------------

@dataclass
class WordResult:
    word: str
    start: float
    end: float
    confidence: float


@dataclass
class SegmentResult:
    id: int
    start: float
    end: float
    text: str
    avg_confidence: float
    words: List[WordResult] = field(default_factory=list)


@dataclass
class TranscriptionResult:
    audio_file: str
    duration_sec: float
    full_text: str
    language: str
    segments: List[SegmentResult]
    low_confidence_words: List[str]

    def to_dict(self):
        return {
            "audio_file": self.audio_file,
            "duration_sec": round(self.duration_sec, 2),
            "full_text": self.full_text,
            "language": self.language,
            "segments": [
                {
                    "id": s.id,
                    "start": round(s.start, 2),
                    "end": round(s.end, 2),
                    "text": s.text,
                    "avg_confidence": round(s.avg_confidence, 3),
                    "words": [
                        {
                            "word": w.word,
                            "start": round(w.start, 2),
                            "end": round(w.end, 2),
                            "confidence": round(w.confidence, 3),
                        }
                        for w in s.words
                    ],
                }
                for s in self.segments
            ],
            "low_confidence_words": self.low_confidence_words,
        }


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------

def _bandpass_filter(audio: np.ndarray, sr: int, low: float, high: float) -> np.ndarray:
    """Keep only the voice-relevant frequency band. Radio audio is often
    full of static/hiss outside human speech range — this cuts a lot of
    that noise before it ever reaches the model."""
    nyquist = sr / 2
    # guard against invalid cutoffs if sr is unexpectedly low
    high = min(high, nyquist - 1)
    sos = butter(4, [low / nyquist, high / nyquist], btype="band", output="sos")
    return sosfilt(sos, audio)


def _normalize(audio: np.ndarray) -> np.ndarray:
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.95
    return audio


def preprocess_audio(path: str) -> np.ndarray:
    """Load an audio file, downmix to mono, resample to 16kHz,
    bandpass filter, and normalize. Returns a float32 numpy array."""
    audio, sr = sf.read(path, always_2d=False)

    # downmix to mono if stereo
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    audio = audio.astype(np.float32)

    # resample to target rate
    if sr != TARGET_SAMPLE_RATE:
        gcd = np.gcd(sr, TARGET_SAMPLE_RATE)
        up, down = TARGET_SAMPLE_RATE // gcd, sr // gcd
        audio = resample_poly(audio, up, down)
        sr = TARGET_SAMPLE_RATE

    audio = _bandpass_filter(audio, sr, *RADIO_BANDPASS)
    audio = _normalize(audio)
    return audio.astype(np.float32)


# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

_model_cache = {}


def _get_model():
    """Lazily load the whisper model once and reuse it across calls —
    loading is the slow part, so don't repeat it per-clip in a batch."""
    from faster_whisper import WhisperModel

    if "model" not in _model_cache:
        _model_cache["model"] = WhisperModel(
            WHISPER_MODEL_SIZE, device="cpu", compute_type="int8"
        )
    return _model_cache["model"]


def transcribe_audio(path: str, apply_preprocessing: bool = True) -> dict:
    """
    Main entry point. Takes a path to an audio clip, returns a
    JSON-serializable dict with the transcript, timestamps, and
    per-word confidence scores.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Audio file not found: {path}")

    model = _get_model()

    if apply_preprocessing:
        audio_array = preprocess_audio(path)
        audio_input = audio_array
        duration = len(audio_array) / TARGET_SAMPLE_RATE
    else:
        audio_input = path
        info = sf.info(path)
        duration = info.duration

    segments_iter, info = model.transcribe(
        audio_input,
        word_timestamps=True,
        vad_filter=True,          # skip dead air / silence between radio calls
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    segments: List[SegmentResult] = []
    full_text_parts = []
    low_confidence_words = []

    for i, seg in enumerate(segments_iter):
        words = []
        word_confidences = []
        if seg.words:
            for w in seg.words:
                conf = float(np.exp(w.probability)) if hasattr(w, "probability") else 1.0
                # faster-whisper gives log-prob-derived probability directly; use as-is
                conf = float(w.probability)
                words.append(WordResult(
                    word=w.word.strip(),
                    start=w.start,
                    end=w.end,
                    confidence=conf,
                ))
                word_confidences.append(conf)
                if conf < LOW_CONFIDENCE_THRESHOLD:
                    low_confidence_words.append(w.word.strip())

        avg_conf = float(np.mean(word_confidences)) if word_confidences else 1.0

        segments.append(SegmentResult(
            id=i,
            start=seg.start,
            end=seg.end,
            text=seg.text.strip(),
            avg_confidence=avg_conf,
            words=words,
        ))
        full_text_parts.append(seg.text.strip())

    result = TranscriptionResult(
        audio_file=os.path.basename(path),
        duration_sec=duration,
        full_text=" ".join(full_text_parts),
        language=info.language,
        segments=segments,
        low_confidence_words=low_confidence_words,
    )

    return result.to_dict()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Transcribe driver radio audio.")
    parser.add_argument("audio_path", help="Path to the audio clip (wav/mp3/etc.)")
    parser.add_argument("--raw", action="store_true", help="Skip preprocessing (bandpass/normalize)")
    parser.add_argument("-o", "--output", help="Path to write JSON output (default: stdout)")
    args = parser.parse_args()

    result = transcribe_audio(args.audio_path, apply_preprocessing=not args.raw)
    output_json = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output_json)
        print(f"Wrote transcript to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
