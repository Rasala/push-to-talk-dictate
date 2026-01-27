# Dependency Licenses

This document lists all dependencies used by Dictate and their respective licenses.

## Python Packages

| Package | Version | License | URL |
|---------|---------|---------|-----|
| mlx | ≥0.5.0 | MIT | https://github.com/ml-explore/mlx |
| mlx-whisper | ≥0.1.0 | MIT | https://github.com/ml-explore/mlx-examples |
| mlx-lm | ≥0.5.0 | MIT | https://github.com/ml-explore/mlx-examples |
| FastAPI | ≥0.100.0 | MIT | https://github.com/tiangolo/fastapi |
| Starlette | (FastAPI dep) | BSD-3-Clause | https://github.com/encode/starlette |
| uvicorn | ≥0.22.0 | BSD-3-Clause | https://github.com/encode/uvicorn |
| sounddevice | ≥0.4.6 | MIT | https://github.com/spatialaudio/python-sounddevice |
| scipy | ≥1.10.0 | BSD-3-Clause | https://github.com/scipy/scipy |
| numpy | ≥1.24.0 | BSD-3-Clause | https://github.com/numpy/numpy |
| psutil | ≥5.9.0 | BSD-3-Clause | https://github.com/giampaolo/psutil |
| pyperclip | ≥1.8.2 | BSD-3-Clause | https://github.com/asweigart/pyperclip |
| pynput | ≥1.7.6 | LGPLv3 | https://github.com/moses-palmer/pynput |
| python-dotenv | ≥1.0.0 | BSD-3-Clause | https://github.com/theskumar/python-dotenv |
| python-multipart | ≥0.0.6 | Apache-2.0 | https://github.com/andrew-d/python-multipart |

### Development & Testing

| Package | Version | License | URL |
|---------|---------|---------|-----|
| pytest | ≥7.0.0 | MIT | https://github.com/pytest-dev/pytest |
| pytest-asyncio | ≥0.21.0 | Apache-2.0 | https://github.com/pytest-dev/pytest-asyncio |
| httpx | ≥0.24.0 | BSD-3-Clause | https://github.com/encode/httpx |
| mypy | ≥1.0 | MIT | https://github.com/python/mypy |
| ruff | ≥0.1.0 | MIT | https://github.com/astral-sh/ruff |

## Frontend Packages (npm)

| Package | Version | License | URL |
|---------|---------|---------|-----|
| react | ^19.2.4 | MIT | https://github.com/facebook/react |
| react-dom | ^19.2.4 | MIT | https://github.com/facebook/react |

### Development & Build

| Package | Version | License | URL |
|---------|---------|---------|-----|
| vite | ^7.3.1 | MIT | https://github.com/vitejs/vite |
| @vitejs/plugin-react | ^5.1.2 | MIT | https://github.com/vitejs/vite-plugin-react |
| typescript | ^5.9.3 | Apache-2.0 | https://github.com/microsoft/TypeScript |
| babel-plugin-react-compiler | ^1.0.0 | MIT | https://github.com/facebook/react |
| @types/react | ^19.2.10 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |
| @types/react-dom | ^19.2.3 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |

## ML Models

| Model | License | URL |
|-------|---------|-----|
| whisper-large-v3-mlx | MIT | https://huggingface.co/mlx-community/whisper-large-v3-mlx |
| Qwen2.5-3B-Instruct-4bit | Qwen Research | https://huggingface.co/mlx-community/Qwen2.5-3B-Instruct-4bit |
| Phi-3-mini-4k-instruct-4bit | MIT | https://huggingface.co/mlx-community/Phi-3-mini-4k-instruct-4bit |

## License Compatibility

All dependencies are compatible with the MIT license of this project.

**Note:** pynput is licensed under LGPLv3, which is compatible with MIT when used as a library (dynamically linked). No modifications to pynput source code are distributed with this project.
