"""Global hotkey handler using the keyboard library."""

from __future__ import annotations

import logging
from typing import Callable, Optional

from config import HotkeyConfig

logger = logging.getLogger(__name__)


class HotkeyManager:
    def __init__(self, config: HotkeyConfig) -> None:
        self._config = config
        self._callback: Optional[Callable[[], None]] = None
        self._registered: bool = False

    @property
    def key(self) -> str:
        return self._config.key

    def register(self, callback: Callable[[], None]) -> None:
        if self._registered:
            logger.warning("Hotkey already registered")
            return

        self._callback = callback

        try:
            import keyboard
            keyboard.add_hotkey(self._config.key, self._callback)
            self._registered = True
            logger.info("Hotkey '%s' registered", self._config.key)
        except ImportError:
            logger.error("keyboard library not installed")
            raise
        except Exception as exc:
            logger.exception("Failed to register hotkey: %s", exc)
            raise

    def unregister(self) -> None:
        if not self._registered:
            return

        try:
            import keyboard
            keyboard.remove_hotkey(self._config.key)
            self._registered = False
            logger.info("Hotkey '%s' unregistered", self._config.key)
        except Exception as exc:
            logger.warning("Failed to unregister hotkey: %s", exc)
