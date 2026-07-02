"""Text insertion module using Win32 SendInput with clipboard fallback."""

from __future__ import annotations

import ctypes
import logging
import time
from ctypes import wintypes
from typing import Optional

import pyperclip

from config import TypingConfig

logger = logging.getLogger(__name__)

INPUT_KEYBOARD = 1
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("ki", KEYBDINPUT),
    ]


user32 = ctypes.windll.user32


def send_input_unicode(char: str) -> None:
    inputs = (INPUT * 2)()

    inputs[0].type = INPUT_KEYBOARD
    inputs[0].ki.wScan = ord(char)
    inputs[0].ki.dwFlags = KEYEVENTF_UNICODE

    inputs[1].type = INPUT_KEYBOARD
    inputs[1].ki.wScan = ord(char)
    inputs[1].ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP

    user32.SendInput(2, ctypes.pointer(inputs[0]), ctypes.sizeof(INPUT))


def _send_text_sendinput(text: str, delay_ms: int = 0) -> bool:
    try:
        for char in text:
            send_input_unicode(char)
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
        return True
    except Exception as exc:
        logger.warning("SendInput failed: %s", exc)
        return False


def _send_text_clipboard(text: str) -> bool:
    try:
        import pyautogui
        pyautogui.hotkey("ctrl", "v")
        return True
    except Exception as exc:
        logger.warning("pyautogui clipboard paste failed: %s", exc)
        return False


class TextTyper:
    def __init__(self, config: TypingConfig) -> None:
        self._config = config

    def type_text(self, text: str) -> bool:
        if not text:
            return False

        text_to_type = text.strip()
        if self._config.add_space_after:
            text_to_type = text_to_type + " "

        logger.debug("Typing text (%d chars): '%s'", len(text_to_type), text_to_type[:50])

        method = self._config.method

        if method == "sendinput":
            if _send_text_sendinput(text_to_type, self._config.delay_ms):
                logger.info("Text typed via SendInput")
                return True

        if method == "sendinput" or method == "clipboard":
            original_clipboard: Optional[str] = None
            try:
                original_clipboard = pyperclip.paste()
            except Exception:
                pass

            try:
                pyperclip.copy(text_to_type)
            except Exception as exc:
                logger.error("Failed to copy to clipboard: %s", exc)
                return False

            time.sleep(0.05)
            success = _send_text_clipboard(text_to_type)

            if original_clipboard is not None:
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    pass

            if success:
                logger.info("Text typed via clipboard paste")
                return True
            else:
                logger.error("All typing methods failed")
                return False

        logger.error("Unknown typing method: %s", method)
        return False
