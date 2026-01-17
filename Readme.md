# 🎙️ Dictate - Push-to-Talk Voice Dictation for macOS

A local, privacy-first voice dictation app for macOS using Apple Silicon. Hold a key to speak, release to transcribe and type directly into any application.

## ✨ Features

- **Push-to-Talk**: Hold Left Option (⌥) to record, release to transcribe
- **Local Processing**: All transcription and cleanup runs on-device using MLX
- **Auto-Type**: Transcribed text is typed directly into the focused window
- **Smart Cleanup**: Uses Qwen LLM to fix grammar and punctuation
- **Multiple Microphones**: Choose from any connected audio input device
- **Clipboard Backup**: Text is also copied to clipboard

## 🔧 Requirements

- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.11+
- ffmpeg (for audio processing)
- Accessibility permissions (for keyboard control)

## 📦 Installation

### 1. Install ffmpeg

```bash
brew install ffmpeg
```

### 2. Set up Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
```

### 3. Install dependencies

```bash
pip install mlx mlx-whisper mlx-lm
pip install sounddevice numpy scipy pynput pyperclip
```

### 4. Grant permissions

When you first run the app, macOS will ask for:
- **Accessibility**: To detect key presses and type text
- **Microphone**: To record audio

## 🚀 Usage

```bash
source .venv/bin/activate
python ptt_dictate.py
```

Or run as a module:

```bash
python -m dictate
```

### Controls

| Action | Key |
|--------|-----|
| **Start Recording** | Hold Left Option (⌥) |
| **Stop & Transcribe** | Release Option |
| **Quit** | Cmd + Esc or Ctrl+C |

### Configuration via Environment Variables

```bash
# Set specific microphone (device index shown at startup)
export DICTATE_AUDIO_DEVICE=3

# Output mode: 'type' (default) or 'clipboard'
export DICTATE_OUTPUT_MODE=clipboard

# Transcription language
export DICTATE_LANGUAGE=pl

# Disable LLM text cleanup (use raw Whisper output)
export DICTATE_LLM_CLEANUP=false

# Disable verbose logging
export DICTATE_VERBOSE=false
```

### Programmatic Configuration

```python
from dictate import DictationApp, Config
from dictate.config import OutputMode

config = Config()
config.audio.device_id = 3
config.output_mode = OutputMode.CLIPBOARD
config.whisper.language = "pl"
config.llm.enabled = False

app = DictationApp(config)
app.run()
```

## 📁 Project Structure

```
dictate/
├── __init__.py      # Package exports
├── __main__.py      # Module entry point
├── app.py           # Main application orchestration
├── audio.py         # Audio capture, VAD, device enumeration
├── config.py        # Configuration dataclasses
├── output.py        # Output handlers (typing, clipboard)
└── transcribe.py    # Whisper + LLM transcription pipeline
```

## 🏗️ How It Works

1. **Recording**: Audio is captured while you hold the Option key
2. **VAD**: Voice activity detection segments speech from silence
3. **Whisper**: MLX-optimized Whisper Large V3 transcribes audio locally
4. **Qwen Cleanup**: Qwen 2 1.5B fixes grammar/punctuation errors
5. **Output**: Text is typed into the focused window (and copied to clipboard)

## 🎤 Supported Models

- **Transcription**: `mlx-community/whisper-large-v3-mlx`
- **Text Cleanup**: `Qwen/Qwen2-1.5B-Instruct-MLX`

## 📝 License

MIT