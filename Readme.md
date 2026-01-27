# 🎙️ Dictate - Push-to-Talk Voice Dictation for macOS

A local, privacy-first voice dictation app for macOS using Apple Silicon. Transcribe speech to text directly on your device using MLX-optimized models.

## ✨ Features

- **100% Local**: All processing runs on-device—no cloud, no data leaves your Mac
- **Two Modes**: Desktop push-to-talk or web browser interface
- **Smart Cleanup**: LLM-powered grammar and punctuation fixes (Qwen2.5 or Phi-3)
- **Translation**: Optionally translate transcriptions to different languages
- **Multiple Microphones**: Choose from any connected audio input device
- **Auto-Type**: Desktop mode types directly into the focused window

## 🔧 Requirements

- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.11+
- ffmpeg (`brew install ffmpeg`)
- Node.js 24+ (for web mode only, auto-builds on first run)

## 📦 Installation

```bash
# Install ffmpeg
brew install ffmpeg

# Set up Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip

# Install dependencies
pip install mlx mlx-whisper mlx-lm
pip install sounddevice numpy scipy pynput pyperclip
pip install fastapi uvicorn python-dotenv  # For web mode
```

## 🚀 Usage

### Desktop Mode (Push-to-Talk)

Hold a key to record, release to transcribe and type into the focused window.

```bash
source .venv/bin/activate
python -m dictate
```

| Action | Key |
|--------|-----|
| Record | Hold Left Option (⌥) |
| Transcribe | Release Option |
| Quit | Cmd+Esc or Ctrl+C |

> **Note:** macOS will prompt for Accessibility and Microphone permissions on first run.

### Web Mode (Browser Interface)

Click to record, click again to stop. View transcriptions in your browser.

```bash
source .venv/bin/activate
python -m dictate.server
```

Open http://localhost:8000 in your browser.

**Server options:**
```bash
python -m dictate.server --port 9000      # Custom port
python -m dictate.server --host 0.0.0.0   # Allow network access
python -m dictate.server --reload         # Auto-reload for development
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`) or set variables directly:

| Variable | Description | Default |
|----------|-------------|---------|
| `DICTATE_AUDIO_DEVICE` | Microphone device index | System default |
| `DICTATE_OUTPUT_MODE` | `type` or `clipboard` | `type` |
| `DICTATE_INPUT_LANGUAGE` | Whisper language (`auto`, `en`, `pl`, etc.) | `auto` |
| `DICTATE_OUTPUT_LANGUAGE` | Translation target (`auto` = preserve input) | `auto` |
| `DICTATE_LLM_CLEANUP` | Enable LLM text cleanup | `true` |
| `DICTATE_LLM_MODEL` | `qwen` (multilingual) or `phi3` (English) | `qwen` |
| `DICTATE_VERBOSE` | Enable verbose logging | `false` |

### Programmatic Configuration

```python
from dictate import DictationApp, Config
from dictate.config import OutputMode, LLMModel

config = Config()
config.audio.device_id = 3
config.output_mode = OutputMode.CLIPBOARD
config.whisper.language = "pl"
config.llm.enabled = True
config.llm.model_choice = LLMModel.QWEN

app = DictationApp(config)
app.run()
```

## 🏗️ How It Works

```
Audio Input → Whisper (transcription) → LLM (cleanup/translation) → Output
```

1. **Recording**: Audio captured via microphone (push-to-talk or click)
2. **VAD**: Voice activity detection segments speech from silence
3. **Whisper**: MLX-optimized Whisper Large V3 transcribes locally
4. **LLM**: Qwen2.5 or Phi-3-Mini fixes grammar, punctuation, and optionally translates
5. **Output**: Text typed into window (desktop) or displayed in browser (web)

## 🎤 Supported Models

| Purpose | Model |
|---------|-------|
| Transcription | `mlx-community/whisper-large-v3-mlx` |
| Cleanup (default) | `mlx-community/Qwen2.5-3B-Instruct-4bit` |
| Cleanup (fast) | `mlx-community/Phi-3-mini-4k-instruct-4bit` |

## 🛠️ Development

### Project Structure

```
dictate/           # Python backend
├── app.py         # Desktop application
├── server.py      # Web server (FastAPI + WebSocket)
├── transcribe.py  # Whisper + LLM pipeline
├── audio.py       # Audio capture and VAD
├── config.py      # Configuration
└── output.py      # Output handlers

web/               # React frontend
├── src/
│   ├── App.tsx
│   ├── components/
│   ├── hooks/
│   └── types.ts
└── package.json

tests/             # Pytest tests
```

### Frontend Development

```bash
# Terminal 1: Start API server
python -m dictate.server

# Terminal 2: Start Vite dev server with hot reload
cd web && npm run dev
```

Open http://localhost:5173 for hot reload during frontend development.

### Running Tests

```bash
python -m pytest tests/ -v
```

## 📝 License

MIT — See [LICENSES.md](LICENSES.md) for dependency licenses.