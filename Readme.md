# 🎙️ Dictate - Push-to-Talk Voice Dictation for macOS

A local, privacy-first voice dictation app for macOS using Apple Silicon. Hold a key to speak, release to transcribe and type directly into any application.

## ✨ Features

- **Push-to-Talk**: Hold Left Option (⌥) to record, release to transcribe
- **Local Processing**: All transcription and cleanup runs on-device using MLX
- **Auto-Type**: Transcribed text is typed directly into the focused window
- **Smart Cleanup**: Uses Phi-3-Mini or Qwen LLM to fix grammar and punctuation (configurable)
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

### Configuration File

The easiest way to configure Dictate is with a `.env` file:

```bash
# Copy the example configuration
cp .env.example .env

# Edit your settings
nano .env

# Run (automatically loads .env)
python -m dictate
```

The `.env` file is automatically loaded at startup and ignored by git.

### Configuration via Environment Variables

You can also set environment variables directly:

```bash
# Set specific microphone (device index shown at startup)
export DICTATE_AUDIO_DEVICE=3

# Output mode: 'type' (default) or 'clipboard'
export DICTATE_OUTPUT_MODE=clipboard

# Transcription language
export DICTATE_LANGUAGE=pl

# Disable LLM text cleanup (use raw Whisper output)
export DICTATE_LLM_CLEANUP=false

# Choose LLM model: 'phi3' (default) or 'qwen'
export DICTATE_LLM_MODEL=phi3

# Disable verbose logging
export DICTATE_VERBOSE=false
```

### Programmatic Configuration

```python
from dictate import DictationApp, Config
from dictate.config import OutputMode, LLMModel

config = Config()
config.audio.device_id = 3
config.output_mode = OutputMode.CLIPBOARD
config.whisper.language = "pl"
config.llm.enabled = False
config.llm.model_choice = LLMModel.PHI3  # or LLMModel.QWEN

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
4. **LLM Cleanup**: Phi-3-Mini or Qwen2 fixes grammar/punctuation (configurable)
5. **Output**: Text is typed into the focused window (and copied to clipboard)

## 🎤 Supported Models

- **Transcription**: `mlx-community/whisper-large-v3-mlx`
- **Text Cleanup**: 
  - `mlx-community/Phi-3-mini-4k-instruct-4bit` (default, recommended)
  - `Qwen/Qwen2-1.5B-Instruct-MLX` (alternative)

## 📝 License

MIT

### Dependency Licenses

| Package | License |
|---------|---------|
| mlx, mlx-whisper, mlx-lm | MIT |
| sounddevice | MIT |
| scipy, numpy, psutil | BSD-3-Clause |
| pyperclip | BSD |
| pynput | LGPLv3 |

### Model Licenses

| Model | License |
|-------|---------|
| whisper-large-v3-mlx | MIT |
| Phi-3-mini-4k-instruct-4bit | MIT |
| Qwen2-1.5B-Instruct-MLX | Apache-2.0 |

All dependencies are compatible with the MIT license of this project.