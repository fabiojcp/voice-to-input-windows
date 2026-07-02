@echo off
echo ============================================
echo   Voice-to-Input - Build Script
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado. Instale o Python 3.11+.
    pause
    exit /b 1
)

echo [1/3] Instalando dependencias...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [2/3] Gerando executavel...
pyinstaller ^
    --onefile ^
    --noconsole ^
    --name="VoiceToInput" ^
    --add-data="config.py;." ^
    --add-data="recorder.py;." ^
    --add-data="transcriber.py;." ^
    --add-data="typer.py;." ^
    --add-data="hotkeys.py;." ^
    --add-data="autostart.py;." ^
    --hidden-import="faster_whisper" ^
    --hidden-import="sounddevice" ^
    --hidden-import="keyboard" ^
    --hidden-import="pyperclip" ^
    --hidden-import="pyautogui" ^
    --hidden-import="scipy" ^
    --hidden-import="numpy" ^
    --hidden-import="pystray" ^
    --hidden-import="PIL" ^
    --hidden-import="PIL.Image" ^
    --hidden-import="PIL.ImageDraw" ^
    --hidden-import="ctypes" ^
    --hidden-import="winreg" ^
    --hidden-import="torch" ^
    --hidden-import="pythoncom" ^
    --hidden-import="win32com.client" ^
    --collect-all="faster_whisper" ^
    --collect-all="sounddevice" ^
    --collect-all="scipy" ^
    --collect-submodules="faster_whisper" ^
    main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Build falhou.
    pause
    exit /b 1
)

echo.
echo [3/3] Build concluido!
echo Executavel em: dist\VoiceToInput.exe
echo.
echo Para iniciar junto com o Windows, execute:
echo   VoiceToInput.exe --install-autostart
echo.
pause
