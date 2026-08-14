"""
Wrapper around audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim.
This model outputs three continuous scores (roughly 0-1 each):
    arousal    - how energetic / activated the voice sounds
    dominance  - how in-control / assertive the voice sounds
    valence    - how positive / negative the voice sounds

"""

import threading
from functools import lru_cache

import numpy as np
import torch
import torch.nn as nn
from transformers import Wav2Vec2Processor
from transformers.models.wav2vec2.modeling_wav2vec2 import (
    Wav2Vec2Model,
    Wav2Vec2PreTrainedModel,
)

MODEL_ID = "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim"
TARGET_SAMPLE_RATE = 16000    #expects 16,000 samples/sec i.e. audio should be 16khz

_lock = threading.Lock()


class RegressionHead(nn.Module):
    """Regression head copied from the audeering model card."""

    def __init__(self, config):
        super().__init__()
        self.dense = nn.Linear(config.hidden_size, config.hidden_size)
        self.dropout = nn.Dropout(config.final_dropout)
        self.out_proj = nn.Linear(config.hidden_size, config.num_labels)

    def forward(self, features, **kwargs):
        x = features
        x = self.dropout(x)
        x = self.dense(x)
        x = torch.tanh(x)
        x = self.dropout(x)
        x = self.out_proj(x)
        return x


class EmotionModel(Wav2Vec2PreTrainedModel):
    """Wav2Vec2 backbone + regression head -> (arousal, dominance, valence)."""

    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.wav2vec2 = Wav2Vec2Model(config)
        self.classifier = RegressionHead(config)
        self.init_weights()

    def forward(self, input_values):
        outputs = self.wav2vec2(input_values)
        hidden_states = outputs[0]
        hidden_states = torch.mean(hidden_states, dim=1)
        logits = self.classifier(hidden_states)
        return hidden_states, logits


@lru_cache(maxsize=1)
def _load():
    """Load processor + model once and cache them for the life of the process."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    processor = Wav2Vec2Processor.from_pretrained(MODEL_ID)
    model = EmotionModel.from_pretrained(MODEL_ID).to(device)
    model.eval()
    return processor, model, device


def predict_arousal_dominance_valence(audio_array: np.ndarray, sample_rate: int):
    """
    audio_array: 1-D float32 numpy array, mono
    sample_rate: must already be 16000 (resample before calling this)

    Returns: (arousal, dominance, valence) as plain Python floats
    """
    if sample_rate != TARGET_SAMPLE_RATE:
        raise ValueError(
            f"Expected {TARGET_SAMPLE_RATE}Hz audio, got {sample_rate}Hz. "
            "Resample before calling predict_arousal_dominance_valence()."
        )

    # Loading the model is not thread-safe on first call; guard it.
    with _lock:
        processor, model, device = _load()

    inputs = processor(audio_array, sampling_rate=sample_rate, return_tensors="pt")
    input_values = inputs.input_values.to(device)

    with torch.no_grad():
        _, logits = model(input_values)

    arousal, dominance, valence = logits[0].cpu().numpy().tolist()
    return arousal, dominance, valence