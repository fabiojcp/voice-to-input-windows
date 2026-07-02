"""Configuration management for Voice-to-Input."""

from __future__ import annotations

import json
import os
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "model": {
        "size": "medium",
        "download_root": "models",
        "device": "auto",
        "compute_type": "auto",
    },
    "transcription": {
        "language": "pt",
        "task": "transcribe",
        "beam_size": 5,
        "vad_filter": True,
        "vad_parameters": {
            "threshold": 0.5,
            "min_speech_duration_ms": 250,
            "min_silence_duration_ms": 2000,
            "window_size_samples": 1024,
            "speech_pad_ms": 400,
        },
    },
    "audio": {
        "sample_rate": 16000,
        "channels": 1,
        "blocksize": 1024,
    },
    "hotkey": {
        "key": "f8",
    },
    "typing": {
        "method": "sendinput",
        "delay_ms": 10,
        "add_space_after": True,
    },
    "sounds": {
        "enabled": True,
    },
    "tray": {
        "enabled": True,
    },
    "startup": {
        "enabled": False,
    },
}


@dataclass
class ModelConfig:
    size: str = "medium"
    download_root: str = "models"
    device: str = "auto"
    compute_type: str = "auto"


@dataclass
class VADParameters:
    threshold: float = 0.5
    min_speech_duration_ms: int = 250
    min_silence_duration_ms: int = 2000
    window_size_samples: int = 1024
    speech_pad_ms: int = 400


@dataclass
class TranscriptionConfig:
    language: str = "pt"
    task: str = "transcribe"
    beam_size: int = 5
    vad_filter: bool = True
    vad_parameters: VADParameters = field(default_factory=VADParameters)


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    blocksize: int = 1024


@dataclass
class HotkeyConfig:
    key: str = "f8"


@dataclass
class TypingConfig:
    method: str = "sendinput"
    delay_ms: int = 10
    add_space_after: bool = True


@dataclass
class SoundsConfig:
    enabled: bool = True


@dataclass
class TrayConfig:
    enabled: bool = True


@dataclass
class StartupConfig:
    enabled: bool = False


@dataclass
class AppConfig:
    model: ModelConfig = field(default_factory=ModelConfig)
    transcription: TranscriptionConfig = field(default_factory=TranscriptionConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    hotkey: HotkeyConfig = field(default_factory=HotkeyConfig)
    typing: TypingConfig = field(default_factory=TypingConfig)
    sounds: SoundsConfig = field(default_factory=SoundsConfig)
    tray: TrayConfig = field(default_factory=TrayConfig)
    startup: StartupConfig = field(default_factory=StartupConfig)


def _dict_to_dataclass(data: dict[str, Any], target: type) -> Any:
    kwargs: dict[str, Any] = {}
    for field_info in target.__dataclass_fields__.values():
        key = field_info.name
        if key in data:
            value = data[key]
            if isinstance(value, dict) and hasattr(field_info.type, "__dataclass_fields__"):
                kwargs[key] = _dict_to_dataclass(value, field_info.type)
            else:
                kwargs[key] = value
    return target(**kwargs)


def load_config(config_path: Path | None = None) -> AppConfig:
    path = config_path or DEFAULT_CONFIG_PATH

    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info("Configuration loaded from %s", path)
            return _dict_to_dataclass(data, AppConfig)  # type: ignore[arg-type]
        except Exception as exc:
            logger.warning("Failed to load config from %s: %s. Using defaults.", path, exc)

    logger.info("No config file found, creating default configuration at %s", path)
    config = AppConfig()
    save_config(config, path)
    return config


def save_config(config: AppConfig, config_path: Path | None = None) -> None:
    path = config_path or DEFAULT_CONFIG_PATH
    data = asdict(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False, default=str)
    logger.info("Configuration saved to %s", path)
