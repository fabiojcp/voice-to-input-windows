"""Audio recording module using sounddevice."""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import sounddevice as sd

from config import AudioConfig

logger = logging.getLogger(__name__)


class AudioRecorder:
    def __init__(self, config: AudioConfig) -> None:
        self._config = config
        self._audio_data: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._is_recording: bool = False

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def _callback(self, indata: np.ndarray, frames: int, time_info: object, status: int) -> None:
        if status:
            logger.warning("Recording status: %s", status)
        self._audio_data.append(indata.copy())

    def start(self) -> None:
        if self._is_recording:
            logger.warning("Already recording")
            return

        self._audio_data.clear()
        self._stream = sd.InputStream(
            samplerate=self._config.sample_rate,
            channels=self._config.channels,
            blocksize=self._config.blocksize,
            callback=self._callback,
            dtype="float32",
        )
        self._stream.start()
        self._is_recording = True
        logger.info("Recording started")

    def stop(self) -> np.ndarray:
        if not self._is_recording or self._stream is None:
            logger.warning("Not recording")
            return np.array([], dtype=np.float32)

        self._stream.stop()
        self._stream.close()
        self._stream = None
        self._is_recording = False

        if not self._audio_data:
            logger.warning("No audio data recorded")
            return np.array([], dtype=np.float32)

        audio = np.concatenate(self._audio_data, axis=0).flatten()
        logger.info("Recording stopped: %.2f seconds of audio", len(audio) / self._config.sample_rate)
        return audio

    def get_duration(self) -> float:
        if not self._audio_data:
            return 0.0
        return sum(len(chunk) for chunk in self._audio_data) / self._config.sample_rate
