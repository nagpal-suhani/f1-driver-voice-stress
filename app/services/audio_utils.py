"""Shared audio loading/resampling so both your part and any future
endpoints handle uploaded files the same way.

Accepts mp3, wav, flac, m4a, ogg -- basically anything ffmpeg can read.
`soundfile` handles wav/flac natively; mp3/m4a/etc fall back to
librosa's ffmpeg-backed loader. Install ffmpeg on your system for the
mp3 path to work (see README)."""

import io
import tempfile

import librosa
import numpy as np
import soundfile as sf

TARGET_SAMPLE_RATE = 16000


def load_and_resample(raw_bytes: bytes) -> np.ndarray:
    """
    Takes raw uploaded audio bytes (mp3, wav, etc), returns a mono
    float32 numpy array at 16kHz, ready for the emotion model.
    """
    try:
        # Fast path: works for wav/flac/ogg without needing ffmpeg
        audio_array, sample_rate = sf.read(io.BytesIO(raw_bytes))
    except Exception:
        # Fallback path: mp3/m4a/etc -- librosa shells out to ffmpeg
        # under the hood, so write to a temp file first since librosa
        # needs a real file path (or file-like object) it can hand off.
        with tempfile.NamedTemporaryFile(suffix=".audio") as tmp:
            tmp.write(raw_bytes)
            tmp.flush()
            audio_array, sample_rate = librosa.load(tmp.name, sr=None, mono=False)
            audio_array = audio_array.T if audio_array.ndim > 1 else audio_array

    # Collapse stereo -> mono if needed
    if audio_array.ndim > 1:
        audio_array = np.mean(audio_array, axis=1)

    if sample_rate != TARGET_SAMPLE_RATE:
        audio_array = librosa.resample(
            audio_array.astype(np.float32),
            orig_sr=sample_rate,
            target_sr=TARGET_SAMPLE_RATE,
        )

    return audio_array.astype(np.float32)