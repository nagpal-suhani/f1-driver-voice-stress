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
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field, asdict
from typing import List, Optional

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WHISPER_MODEL_SIZE = "small"   # tiny/base/small/medium/large-v3
TARGET_SAMPLE_RATE = 16000     # expects 16kHz mono
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


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _load_via_ffmpeg(path: str) -> tuple[np.ndarray, int]:
    """Fallback decoder for formats soundfile/libsndfile can't read
    directly (older libsndfile builds don't support mp3, and some
    exotic containers never will). Shells out to ffmpeg to transcode
    to a temp WAV, then reads that with soundfile. Requires ffmpeg on
    PATH — raises a clear error if it isn't installed."""
    if not _ffmpeg_available():
        raise RuntimeError(
            f"Could not decode '{path}' with soundfile, and ffmpeg is not "
            "installed to fall back on. Install ffmpeg (e.g. `apt install "
            "ffmpeg` / `brew install ffmpeg`) to support mp3 and other "
            "compressed formats."
        )

    fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", path,
                "-ac", "1",                      # mono
                "-ar", str(TARGET_SAMPLE_RATE),  # resample while we're at it
                wav_path,
            ],
            check=True,
            capture_output=True,
            timeout=60,
        )
        audio, sr = sf.read(wav_path, always_2d=False)
        return audio, sr
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode(errors="ignore") if e.stderr else ""
        raise RuntimeError(f"ffmpeg failed to decode '{path}': {stderr}") from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"ffmpeg timed out decoding '{path}' (>60s)") from e
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)


def _load_audio(path: str) -> tuple[np.ndarray, int]:
    """Load an audio file into (samples, sample_rate). Tries soundfile
    first (fast, no subprocess); falls back to ffmpeg for formats
    soundfile can't handle — this is what makes mp3 reliable across
    machines with older libsndfile builds."""
    try:
        return sf.read(path, always_2d=False)
    except Exception as sf_error:
        try:
            return _load_via_ffmpeg(path)
        except Exception as ffmpeg_error:
            raise RuntimeError(
                f"Failed to decode audio file '{path}'. "
                f"soundfile error: {sf_error}. ffmpeg fallback error: {ffmpeg_error}"
            ) from ffmpeg_error


def _probe_duration_via_ffmpeg(path: str) -> float:
    """Best-effort duration lookup via ffprobe when soundfile can't read
    the file's metadata. Returns 0.0 if ffprobe is unavailable or fails —
    duration is informational only, so a failure here shouldn't block
    transcription."""
    if shutil.which("ffprobe") is None:
        return 0.0
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            capture_output=True, text=True, timeout=15, check=True,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def preprocess_audio(path: str) -> np.ndarray:
    """Load an audio file, downmix to mono, resample to 16kHz,
    bandpass filter, and normalize. Returns a float32 numpy array."""
    audio, sr = _load_audio(path)

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
        try:
            duration = sf.info(path).duration
        except Exception:
            # soundfile can't read this container's metadata (e.g. mp3 on
            # an older libsndfile) — fall back to ffprobe, or just leave
            # duration unset. faster-whisper itself decodes via PyAV
            # internally and handles mp3 fine regardless of this.
            duration = _probe_duration_via_ffmpeg(path)

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