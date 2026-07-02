"""Transcription module using faster-whisper with CUDA support and VAD."""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Optional

import numpy as np

from config import ModelConfig, TranscriptionConfig

logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self, model_cfg: ModelConfig, transcribe_cfg: TranscriptionConfig) -> None:
        self._model_cfg = model_cfg
        self._transcribe_cfg = transcribe_cfg
        self._model: Optional[object] = None
        self._loaded: bool = False
        self._load_lock = threading.Lock()

    def load_model(self) -> None:
        if self._loaded:
            return

        with self._load_lock:
            if self._loaded:
                return

            from faster_whisper import WhisperModel

            device = self._model_cfg.device
            compute_type = self._model_cfg.compute_type

            if device == "auto" or compute_type == "auto":
                try:
                    import torch  # type: ignore[import-untyped]
                    if torch.cuda.is_available():
                        device = "cuda"
                        compute_type = "float16"
                        logger.info("CUDA GPU detected, using device=cuda compute_type=float16")
                    else:
                        device = "cpu"
                        compute_type = "int8"
                        logger.info("CUDA not available, using device=cpu compute_type=int8")
                except ImportError:
                    device = "cpu"
                    compute_type = "int8"
                    logger.info("PyTorch not found, using device=cpu compute_type=int8")

            download_root = str(Path(self._model_cfg.download_root).resolve())
            os.makedirs(download_root, exist_ok=True)

            logger.info(
                "Loading Whisper model '%s' (device=%s, compute_type=%s)...",
                self._model_cfg.size,
                device,
                compute_type,
            )
            self._model = WhisperModel(
                self._model_cfg.size,
                device=device,
                compute_type=compute_type,
                download_root=download_root,
                local_files_only=False,
            )
            self._loaded = True
            logger.info("Model loaded successfully")

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        if self._model is None:
            self.load_model()

        if audio.size == 0:
            logger.warning("Empty audio, returning empty string")
            return ""

        try:
            segments, info = self._model.transcribe(  # type: ignore[union-attr]
                audio,
                language=self._transcribe_cfg.language,
                task=self._transcribe_cfg.task,
                beam_size=self._transcribe_cfg.beam_size,
                vad_filter=self._transcribe_cfg.vad_filter,
                vad_parameters=_vad_params_dict(self._transcribe_cfg),
            )

            text = " ".join(segment.text.strip() for segment in segments)

            if text:
                logger.info("Transcription: '%s'", text)
            else:
                logger.info("Transcription returned empty text")

            return text
        except Exception as exc:
            logger.exception("Transcription failed: %s", exc)
            return ""


def _vad_params_dict(cfg: TranscriptionConfig) -> dict:
    if not cfg.vad_parameters:
        return {}
    vp = cfg.vad_parameters
    return {
        "threshold": vp.threshold,
        "min_speech_duration_ms": vp.min_speech_duration_ms,
        "min_silence_duration_ms": vp.min_silence_duration_ms,
        "window_size_samples": vp.window_size_samples,
        "speech_pad_ms": vp.speech_pad_ms,
    }
