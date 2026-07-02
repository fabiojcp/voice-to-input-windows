"""Voice-to-Input: Dictation tool using Whisper with full local processing.

Press F8 to start recording, press F8 again to stop and transcribe.
The transcribed text is inserted directly into the currently focused control.

CLI:
    python main.py                    Run normally
    python main.py --install-autostart   Register autostart + run
    python main.py --uninstall-autostart Remove autostart + run
"""

from __future__ import annotations

import argparse
import logging
import sys
import threading
from pathlib import Path
from typing import Optional

import ctypes
from ctypes import wintypes

from config import AppConfig, load_config, save_config
from recorder import AudioRecorder
from transcriber import Transcriber
from typer import TextTyper
from hotkeys import HotkeyManager
from autostart import enable_autostart, disable_autostart, is_autostart_enabled

logger = logging.getLogger(__name__)

IDC_ARROW = 32512
IDC_CROSS = 32515
OCR_NORMAL = 32512

_user32 = ctypes.windll.user32
_original_arrow_cursor: Optional[int] = None
_cursor_changed: bool = False


def _set_cursor_recording() -> None:
    global _cursor_changed, _original_arrow_cursor
    if _cursor_changed:
        return
    try:
        _original_arrow_cursor = _user32.CopyIcon(
            _user32.LoadCursorW(None, IDC_ARROW)
        )
        recording_cursor = _user32.LoadCursorW(None, IDC_CROSS)
        _user32.SetSystemCursor(recording_cursor, OCR_NORMAL)
        _cursor_changed = True
        logger.debug("Cursor changed to recording indicator")
    except Exception as exc:
        logger.warning("Failed to change cursor: %s", exc)


def _restore_cursor() -> None:
    global _cursor_changed, _original_arrow_cursor
    if not _cursor_changed or _original_arrow_cursor is None:
        return
    try:
        _user32.SetSystemCursor(_original_arrow_cursor, OCR_NORMAL)
        _cursor_changed = False
        _original_arrow_cursor = None
        logger.debug("Cursor restored to default")
    except Exception as exc:
        logger.warning("Failed to restore cursor: %s", exc)


class VoiceToInputApp:
    def __init__(self, config: Optional[AppConfig] = None) -> None:
        self._config = config or load_config()
        self._recorder = AudioRecorder(self._config.audio)
        self._transcriber = Transcriber(self._config.model, self._config.transcription)
        self._typer = TextTyper(self._config.typing)
        self._hotkeys = HotkeyManager(self._config.hotkey)

        self._lock = threading.Lock()
        self._pending_transcription: bool = False
        self._tray_icon: Optional[object] = None

    def _on_hotkey(self) -> None:
        with self._lock:
            if self._recorder.is_recording:
                self._stop_and_transcribe()
            else:
                self._start_recording()

    def _start_recording(self) -> None:
        print("[Gravando...]")
        logger.info("Hotkey pressed - starting recording")
        try:
            self._recorder.start()
            _set_cursor_recording()
        except Exception as exc:
            print(f"[ERRO] Falha ao iniciar gravação: {exc}")
            logger.exception("Failed to start recording")

    def _stop_and_transcribe(self) -> None:
        print("[Transcrevendo...]")
        logger.info("Hotkey pressed - stopping recording and transcribing")

        _restore_cursor()
        audio = self._recorder.stop()
        if audio.size == 0:
            print("[ERRO] Nenhum áudio capturado.")
            return

        text = self._transcriber.transcribe(audio, self._config.audio.sample_rate)

        if text:
            print(f"[Texto reconhecido] {text}")
            print("[Inserindo texto...]")
            success = self._typer.type_text(text)
            if success:
                print("[Texto inserido.]")
            else:
                print("[ERRO] Falha ao inserir texto.")
        else:
            print("[ERRO] Transcrição vazia.")

    def _load_model_background(self) -> None:
        def _load() -> None:
            print("[Carregando modelo Whisper...]")
            try:
                self._transcriber.load_model()
                print("[Modelo carregado. Pressione F8 para gravar.]")
            except Exception as exc:
                print(f"[ERRO] Falha ao carregar modelo: {exc}")
                logger.exception("Failed to load Whisper model")

        thread = threading.Thread(target=_load, daemon=True)
        thread.start()

    def run(self) -> None:
        print("=" * 50)
        print("  Voice-to-Input")
        print(f"  Atalho: {self._config.hotkey.key.upper()}")
        print(f"  Modelo: {self._config.model.size}")
        print(f"  Idioma: {self._config.transcription.language}")
        print("=" * 50)

        self._hotkeys.register(self._on_hotkey)

        self._load_model_background()

        if self._config.tray.enabled:
            self._setup_tray()

        try:
            print("Aplicação em execução. Ctrl+C para sair.")
            import keyboard
            keyboard.wait()
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def _setup_tray(self) -> None:
        try:
            import pystray
            from PIL import Image, ImageDraw

            def _create_icon_image() -> Image.Image:
                img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                draw.rounded_rectangle([4, 8, 60, 56], radius=8, fill="#2196F3")
                draw.polygon([(28, 20), (28, 44), (44, 32)], fill="white")
                return img

            def _on_quit(icon: object, item: object) -> None:
                self.shutdown()
                icon.stop()

            icon = pystray.Icon(
                "voice_to_input",
                _create_icon_image(),
                menu=pystray.Menu(
                    pystray.MenuItem("Sair", _on_quit),
                ),
            )
            self._tray_icon = icon

            tray_thread = threading.Thread(target=icon.run, daemon=True)
            tray_thread.start()
            logger.info("System tray icon started")
        except ImportError:
            logger.warning("pystray or Pillow not installed, skipping tray icon")
        except Exception as exc:
            logger.warning("Failed to create tray icon: %s", exc)

    def shutdown(self) -> None:
        _restore_cursor()
        self._hotkeys.unregister()
        logger.info("Shutdown complete")


def _handle_autostart(config: AppConfig) -> None:
    if is_autostart_enabled():
        if not config.startup.enabled:
            logger.info("startup.enabled=false but autostart is registered, uninstalling...")
            disable_autostart()
    elif config.startup.enabled:
        logger.info("startup.enabled=true, registering autostart...")
        if enable_autostart():
            print("[OK] Registrado para iniciar junto com o Windows.")
        else:
            print("[ERRO] Falha ao registrar inicializacao automatica.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Voice-to-Input Dictation Tool")
    parser.add_argument("--install-autostart", action="store_true", help="Register autostart with Windows and run")
    parser.add_argument("--uninstall-autostart", action="store_true", help="Remove autostart from Windows and run")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    config = load_config()

    if args.install_autostart:
        if enable_autostart():
            config.startup.enabled = True
            save_config(config)
            print("[OK] Inicializacao automatica ATIVADA.")
        else:
            print("[ERRO] Falha ao ativar inicializacao automatica.")

    if args.uninstall_autostart:
        if disable_autostart():
            config.startup.enabled = False
            save_config(config)
            print("[OK] Inicializacao automatica DESATIVADA.")
        else:
            print("[ERRO] Falha ao desativar inicializacao automatica.")

    _handle_autostart(config)

    app = VoiceToInputApp(config)
    app.run()


if __name__ == "__main__":
    main()
