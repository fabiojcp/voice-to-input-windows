"""Windows autostart registration using registry or startup folder."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

APP_NAME = "VoiceToInput"
REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_exe_path() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    return sys.executable


def _get_startup_shortcut_path() -> Path:
    startup_folder = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    return startup_folder / f"{APP_NAME}.lnk"


def is_autostart_enabled() -> bool:
    try:
        import winreg
    except ImportError:
        logger.warning("winreg not available, cannot check autostart")
        return False

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except OSError:
        return False


def enable_autostart() -> bool:
    methods = [_enable_autostart_registry, _enable_autostart_shortcut]
    for method in methods:
        try:
            if method():
                return True
        except Exception as exc:
            logger.warning("Autostart method failed: %s", exc)
    return False


def disable_autostart() -> bool:
    success = False

    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            winreg.DeleteValue(key, APP_NAME)
            logger.info("Removed from registry autostart")
            success = True
        except FileNotFoundError:
            pass
        finally:
            winreg.CloseKey(key)
    except ImportError:
        logger.warning("winreg not available")
    except OSError as exc:
        logger.warning("Registry autostart removal failed: %s", exc)

    shortcut = _get_startup_shortcut_path()
    if shortcut.exists():
        try:
            shortcut.unlink()
            logger.info("Removed startup folder shortcut")
            success = True
        except OSError as exc:
            logger.warning("Failed to remove shortcut: %s", exc)

    return success


def _enable_autostart_registry() -> bool:
    try:
        import winreg
        exe_path = _get_exe_path()
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        logger.info("Autostart registered in registry: %s", exe_path)
        return True
    except ImportError:
        logger.warning("winreg not available for registry autostart")
        return False


def _enable_autostart_shortcut() -> bool:
    try:
        import pythoncom
        from win32com.client import Dispatch

        shortcut_path = _get_startup_shortcut_path()
        shortcut_path.parent.mkdir(parents=True, exist_ok=True)

        pythoncom.CoInitialize()
        try:
            shell = Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(str(shortcut_path))
            shortcut.TargetPath = _get_exe_path()
            shortcut.WorkingDirectory = str(Path(_get_exe_path()).parent)
            shortcut.Description = "Voice-to-Input Dictation Tool"
            shortcut.Save()
            logger.info("Startup shortcut created at: %s", shortcut_path)
            return True
        finally:
            pythoncom.CoUninitialize()
    except ImportError:
        logger.warning("win32com not available for shortcut autostart")
        return False
    except Exception as exc:
        logger.warning("Failed to create startup shortcut: %s", exc)
        return False
