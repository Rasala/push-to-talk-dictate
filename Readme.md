# 🎙️ Dictate - Push-to-Talk Voice Dictation for macOS

A local, privacy-first voice dictation app for macOS using Apple Silicon. Hold a key to speak, release to transcribe and type directly into any application.

## ✨ Features

- **Push-to-Talk**: Hold Left Option (⌥) to record, release to transcribe
- **Local Processing**: All transcription and cleanup runs on-device using MLX
- **Auto-Type**: Transcribed text is typed directly into the focused window
- **Smart Cleanup**: Uses Qwen2.5 or Phi-3-Mini LLM to fix grammar and punctuation (configurable)
- **Multiple Microphones**: Choose from any connected audio input device
- **Clipboard Backup**: Text is also copied to clipboard

## 🔧 Requirements

- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.11+
- ffmpeg (for audio processing)
- Node.js 24+ (for web server frontend, auto-builds on first run)
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

### Desktop Mode (Push-to-Talk)

```bash
source .venv/bin/activate
python ptt_dictate.py
```

Or run as a module:

```bash
python -m dictate
```

### Web Server Mode

Start the web server to use Dictate from your browser:

```bash
source .venv/bin/activate
python -m dictate.server
```

Then open http://localhost:8000 in your browser.

The frontend will be built automatically on first run (requires Node.js).

**Web server options:**

```bash
# Custom port
python -m dictate.server --port 9000

# Allow network access (not just localhost)
python -m dictate.server --host 0.0.0.0

# Development mode with auto-reload (Python only)
python -m dictate.server --reload
```

### Desktop Controls

| Action | Key |
|--------|-----|
| **Start Recording** | Hold Left Option (⌥) |
| **Stop & Transcribe** | Release Option |
| **Quit** | Cmd + Esc or Ctrl+C |

### Web Controls

| Action | Button |
|--------|--------|
| **Start Recording** | Click microphone button |
| **Stop & Transcribe** | Click stop button |

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

# Input language for transcription ('auto' for auto-detect, or language code)
export DICTATE_INPUT_LANGUAGE=auto

# Output language for cleaned text ('auto' preserves input language)
export DICTATE_OUTPUT_LANGUAGE=en

# Disable LLM text cleanup (use raw Whisper output)
export DICTATE_LLM_CLEANUP=false

# Choose LLM model: 'qwen' (default, multilingual) or 'phi3' (English only)
export DICTATE_LLM_MODEL=qwen

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
config.llm.model_choice = LLMModel.QWEN  # or LLMModel.PHI3 for English only

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
├── server.py        # Web server (FastAPI + WebSocket)
├── transcribe.py    # Whisper + LLM transcription pipeline
└── types.py         # TypedDict definitions for API contracts

web/
├── src/
│   ├── components/  # React components (RecordButton, AudioVisualizer, etc.)
│   ├── hooks/       # Custom React hooks (useWebSocket, useAudioRecorder)
│   ├── App.tsx      # Main React application
│   ├── main.tsx     # React entry point
│   └── types.ts     # TypeScript type definitions
├── index.html       # HTML entry point
├── package.json     # npm dependencies (React 19, Vite)
├── tsconfig.json    # TypeScript configuration
└── vite.config.ts   # Vite build configuration with API proxy

tests/
├── conftest.py      # Pytest fixtures
├── test_config.py   # Configuration tests
├── test_server.py   # Server endpoint tests
└── test_transcribe.py # Transcription pipeline tests
```

## 🛠️ Development

### Running the Server

```bash
source .venv/bin/activate
python -m dictate.server
```

The server automatically builds the frontend on first run if `web/dist/` doesn't exist (requires Node.js).

### Web Client Development

For frontend development with hot reload:

```bash
# Terminal 1: Start the Python API server
python -m dictate.server

# Terminal 2: Start Vite dev server (proxies API to Python)
cd web
npm run dev
```

Open http://localhost:5173 for hot reload during frontend development.

### Manual Frontend Build

```bash
cd web
npm install
npm run build
```

### Running Tests

```bash
python -m pytest tests/ -v
```

## 🏗️ How It Works

### Desktop Mode
1. **Recording**: Audio is captured while you hold the Option key
2. **VAD**: Voice activity detection segments speech from silence
3. **Whisper**: MLX-optimized Whisper Large V3 transcribes audio locally
4. **LLM Cleanup**: Qwen2.5 or Phi-3-Mini fixes grammar/punctuation (configurable)
5. **Output**: Text is typed into the focused window (and copied to clipboard)

### Web Mode
1. **Recording**: Click to start, click again to stop (toggle mode)
2. **WebSocket**: Audio is sent to the server as WebM/Opus
3. **Conversion**: Server converts WebM to WAV using ffmpeg
4. **Whisper**: MLX-optimized Whisper Large V3 transcribes audio locally
5. **LLM Cleanup**: Qwen2.5 or Phi-3-Mini fixes grammar/punctuation (configurable)
6. **Response**: Transcribed text is returned via WebSocket

## 🎤 Supported Models

- **Transcription**: `mlx-community/whisper-large-v3-mlx`
- **Text Cleanup**: 
  - `mlx-community/Qwen2.5-3B-Instruct-4bit` (default, best multilingual support)
  - `mlx-community/Phi-3-mini-4k-instruct-4bit` (English only, faster)

## 📝 License

MIT

See [LICENSES.md](LICENSES.md) for a complete list of dependency licenses.