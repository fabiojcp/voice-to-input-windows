# Voice-to-Input

Ferramenta de ditado offline para Windows usando Whisper (faster-whisper).

Pressione **F8** para iniciar a gravação e **F8** novamente para transcrever. O texto é inserido diretamente no controle focado.

## Funcionalidades

- Processamento totalmente local (offline após download do modelo)
- GPU NVIDIA (CUDA) com fallback automático para CPU
- Voice Activity Detection (VAD) integrado
- Inserção direta via SendInput + fallback de clipboard
- Ícone na bandeja do sistema (system tray)
- Configuração via `config.json`
- Sons de início/parada de gravação (opcional)
- Pronto para empacotamento com PyInstaller

## Requisitos

- Windows 10/11
- Python 3.11+
- (Opcional) GPU NVIDIA com CUDA Toolkit

## Instalação

### 1. Clonar o repositório

```bash
git clone <repo-url>
cd voice-to-input-windows
```

### 2. Criar ambiente virtual

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

## Instalação com suporte CUDA (GPU NVIDIA)

Para desempenho máximo com GPU NVIDIA:

### 1. Instalar CUDA Toolkit 12.x

Baixe e instale o CUDA Toolkit em:
https://developer.nvidia.com/cuda-downloads

### 2. Instalar cuDNN

Baixe cuDNN para CUDA 12.x em:
https://developer.nvidia.com/cudnn

Extraia os arquivos para o diretório de instalação do CUDA.

### 3. Instalar PyTorch com CUDA

```bash
pip uninstall torch -y
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### 4. Instalar faster-whisper com suporte CUDA

```bash
pip install faster-whisper
```

### 5. Verificar instalação

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

Deve retornar `True`.

## Uso

```bash
python main.py
```

### Atalho

| Tecla | Ação |
|-------|------|
| F8 (primeiro) | Iniciar gravação |
| F8 (segundo) | Parar gravação e transcrever |

### Modo CPU (sem GPU)

Se você não tem GPU NVIDIA, o programa detecta automaticamente e usa CPU. Para forçar CPU:

Edite `config.json`:
```json
{
    "model": {
        "device": "cpu",
        "compute_type": "int8"
    }
}
```

Modelos recomendados para CPU: `tiny`, `base` ou `small`.

## Configuração

Edite `config.json` para personalizar:

| Chave | Descrição | Padrão |
|-------|-----------|--------|
| `model.size` | Tamanho do modelo Whisper | `"medium"` |
| `model.device` | Dispositivo (`"auto"`, `"cuda"`, `"cpu"`) | `"auto"` |
| `model.compute_type` | Tipo de computação | `"auto"` |
| `model.download_root` | Pasta dos modelos | `"models"` |
| `transcription.language` | Idioma | `"pt"` |
| `transcription.beam_size` | Beam size | `5` |
| `transcription.vad_filter` | Ativar VAD | `true` |
| `hotkey.key` | Atalho global | `"f8"` |
| `typing.method` | Método de inserção | `"sendinput"` |
| `typing.add_space_after` | Adicionar espaço após texto | `true` |
| `tray.enabled` | Ícone na bandeja | `true` |

### Modelos disponíveis

| Modelo | VRAM | Velocidade (GPU) | Qualidade |
|--------|------|------------------|-----------|
| `tiny` | ~1 GB | Muito rápido | Básica |
| `base` | ~1 GB | Rápido | Boa |
| `small` | ~2 GB | Médio | Muito boa |
| `medium` | ~5 GB | Lento | Excelente |
| `large-v3` | ~10 GB | Muito lento | Máxima |

## Gerar executável (.exe)

### Build automático (recomendado)

Execute o script de build:

```batch
build.bat
```

O executável será gerado em `dist\VoiceToInput.exe`.

### Inicialização automática com Windows

Após gerar o `.exe`, execute no terminal:

```batch
VoiceToInput.exe --install-autostart
```

Para remover:

```batch
VoiceToInput.exe --uninstall-autostart
```

Também é possível ativar/desativar editando `config.json`:

```json
{
    "startup": {
        "enabled": true
    }
}
```

O registro é feito no registro do Windows (`HKCU\...\Run`) e também como atalho na pasta Startup.

### Build manual (via linha de comando)

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name="VoiceToInput" ^
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
    --hidden-import="scipy" ^
    --hidden-import="pystray" ^
    --hidden-import="PIL" ^
    --hidden-import="pythoncom" ^
    --hidden-import="win32com.client" ^
    --hidden-import="winreg" ^
    --hidden-import="torch" ^
    --collect-all="faster_whisper" ^
    --collect-all="sounddevice" ^
    --collect-all="scipy" ^
    main.py
```

### Distribuir

Copie `dist\VoiceToInput.exe` e a pasta `models\` (com os modelos baixados) para o computador de destino. Ou distribua apenas o `.exe` --- os modelos serão baixados no primeiro uso.

## Estrutura do projeto

```
voice-to-input-windows/
    main.py           # Ponto de entrada, system tray, orquestracao
    config.py         # Gerenciamento de configuracao
    recorder.py       # Gravacao de audio
    transcriber.py    # Transcricao com faster-whisper + VAD
    typer.py          # Insercao de texto (SendInput + clipboard)
    hotkeys.py        # Atalhos globais
    autostart.py      # Inicializacao automatica com Windows
    build.bat         # Script de build para .exe
    requirements.txt  # Dependencias
    README.md         # Documentacao
    config.json       # Configuracao (gerado automaticamente)
    models/           # Modelos Whisper baixados
```

## Solução de problemas

### Erro ao carregar modelo

Verifique a conexão com internet na primeira execução (para download do modelo).

### Áudio não capturado

Verifique se o microfone está configurado como dispositivo padrão no Windows.

### Hotkey não funciona

Execute como administrador. Alguns aplicativos bloqueiam hooks de teclado globais.

### CUDA out of memory

Use um modelo menor (`small` ou `base`) no `config.json`.

## Licença

MIT
