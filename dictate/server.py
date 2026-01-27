"""Web server for Dictate - serves API and demo web app."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from scipy.io.wavfile import read as wav_read

if TYPE_CHECKING:
    from numpy.typing import NDArray
    from dictate.config import Config
    from dictate.transcribe import TranscriptionPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_SAMPLE_RATE = 16000
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
FFMPEG_TIMEOUT_SECONDS = 30
MONO_CHANNELS = 1
INT16_MAX = 32767
FIRST_CHANNEL_INDEX = 0

_pipeline: TranscriptionPipeline | None = None
_config: Config | None = None
_processing_lock = asyncio.Lock()


def get_web_dir() -> Path:
    return Path(__file__).parent.parent / "web"


def get_static_dir() -> Path:
    web_dir = get_web_dir()
    dist_dir = web_dir / "dist"
    if dist_dir.exists():
        return dist_dir
    return web_dir


def build_frontend() -> bool:
    web_dir = get_web_dir()
    dist_dir = web_dir / "dist"
    
    if dist_dir.exists():
        return True
    
    package_json = web_dir / "package.json"
    if not package_json.exists():
        logger.warning("No package.json found in web directory")
        return False
    
    node_modules = web_dir / "node_modules"
    
    print("\n🔨 Building frontend...")
    
    try:
        if not node_modules.exists():
            print("   Installing npm dependencies...")
            subprocess.run(
                ["npm", "install"],
                cwd=web_dir,
                check=True,
                capture_output=True,
            )
        
        print("   Compiling TypeScript and bundling...")
        subprocess.run(
            ["npm", "run", "build"],
            cwd=web_dir,
            check=True,
            capture_output=True,
        )
        
        print("   ✅ Frontend built successfully!")
        return True
        
    except FileNotFoundError:
        logger.warning("npm not found - please install Node.js to build the frontend")
        print("   ⚠️  npm not found. Install Node.js or run 'cd web && npm run build' manually.")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Frontend build failed: {e.stderr.decode() if e.stderr else str(e)}")
        print(f"   ❌ Build failed. Run 'cd web && npm run build' manually for details.")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _pipeline, _config
    
    print("\n🌐 Dictate Web Server")
    print("=" * 40)
    
    build_frontend()
    
    from dictate.config import Config
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    _config = Config.from_env()
    
    from dictate.transcribe import TranscriptionPipeline
    
    print("\n📦 Loading models...")
    _pipeline = TranscriptionPipeline(
        whisper_config=_config.whisper,
        llm_config=_config.llm,
    )
    _pipeline.set_sample_rate(_config.audio.sample_rate)
    _pipeline.preload_models()
    
    print("\n✅ Server ready!")
    print(f"   Input language: {_config.whisper.language or 'auto-detect'}")
    print(f"   Output language: {_config.llm.output_language or 'preserve input'}")
    print(f"   LLM cleanup: {'enabled' if _config.llm.enabled else 'disabled'}")
    print("=" * 40)
    
    yield
    
    print("\n👋 Shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Dictate Web API",
        description="Local voice transcription service using MLX Whisper",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health_check():
        return JSONResponse({
            "status": "healthy",
            "models_loaded": _pipeline is not None,
        })

    @app.get("/config")
    async def get_config():
        if _config is None:
            return JSONResponse({"error": "Not initialized"}, status_code=503)
        
        return JSONResponse({
            "input_language": _config.whisper.language,
            "output_language": _config.llm.output_language,
            "llm_enabled": _config.llm.enabled,
            "llm_model": _config.llm.model_choice.value,
            "sample_rate": _config.audio.sample_rate,
        })

    @app.websocket("/ws/transcribe")
    async def websocket_transcribe(websocket: WebSocket):
        client_id = id(websocket)
        logger.info(f"WebSocket client {client_id} attempting to connect")
        await websocket.accept()
        logger.info(f"WebSocket client {client_id} connected and accepted")
        
        request_input_language = None
        request_output_language = None
        
        try:
            while True:
                try:
                    message = await websocket.receive()
                except RuntimeError:
                    break
                
                if message.get("type") == "websocket.disconnect":
                    break
                
                if "text" in message:
                    try:
                        config_data = json.loads(message["text"])
                        if config_data.get("type") == "config":
                            request_input_language = config_data.get("input_language")
                            request_output_language = config_data.get("output_language")
                            logger.info(
                                f"Config received: input={request_input_language}, "
                                f"output={request_output_language}"
                            )
                            continue
                    except json.JSONDecodeError:
                        pass
                
                if "bytes" not in message:
                    continue
                    
                data = message["bytes"]
                logger.info(f"Received {len(data)} bytes of audio data")
                
                if _pipeline is None:
                    await websocket.send_json({
                        "status": "error",
                        "text": "Server not ready, models still loading",
                    })
                    continue
                
                async with _processing_lock:
                    await websocket.send_json({"status": "processing"})
                    
                    try:
                        result = await asyncio.to_thread(
                            process_audio_data,
                            data,
                            request_input_language,
                            request_output_language,
                        )
                        
                        if result:
                            await websocket.send_json({
                                "status": "complete",
                                "text": result,
                            })
                        else:
                            await websocket.send_json({
                                "status": "complete",
                                "text": "",
                                "message": "No speech detected",
                            })
                    except Exception as e:
                        logger.exception("Transcription error")
                        await websocket.send_json({
                            "status": "error",
                            "text": str(e),
                        })
                        
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.exception("WebSocket error")

    static_dir = get_static_dir()
    
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        @app.get("/")
        async def serve_index():
            index_path = static_dir / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return JSONResponse({"error": "Web demo not found"}, status_code=404)
        
        @app.get("/assets/{path:path}")
        async def serve_assets(path: str):
            asset_path = static_dir / "assets" / path
            if asset_path.exists():
                return FileResponse(asset_path)
            return JSONResponse({"error": "Asset not found"}, status_code=404)

    return app


def convert_webm_to_wav(webm_data: bytes, sample_rate: int = DEFAULT_SAMPLE_RATE) -> str:
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as webm_file:
        webm_file.write(webm_data)
        webm_path = webm_file.name
    
    wav_path = webm_path.replace(".webm", ".wav")
    
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-i", webm_path,
            "-ar", str(sample_rate),
            "-ac", str(MONO_CHANNELS),
            "-acodec", "pcm_s16le",
            wav_path,
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
        
        if result.returncode != 0:
            logger.error(f"ffmpeg error: {result.stderr}")
            raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")
        
        return wav_path
        
    finally:
        try:
            os.remove(webm_path)
        except OSError:
            pass


def process_audio_data(
    webm_data: bytes,
    input_language: str | None = None,
    output_language: str | None = None,
) -> str | None:
    global _pipeline, _config
    
    if _pipeline is None or _config is None:
        raise RuntimeError("Pipeline not initialized")
    
    sample_rate = _config.audio.sample_rate
    wav_path = convert_webm_to_wav(webm_data, sample_rate)

    try:
        file_sample_rate, audio_data = wav_read(wav_path)
        
        if file_sample_rate != sample_rate:
            logger.warning(
                f"Sample rate mismatch: {file_sample_rate} vs {sample_rate}"
            )
        
        if audio_data.dtype != np.int16:
            if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                audio_data = (audio_data * INT16_MAX).astype(np.int16)
            else:
                audio_data = audio_data.astype(np.int16)
        
        if len(audio_data.shape) > 1:
            audio_data = audio_data[:, FIRST_CHANNEL_INDEX]
        
        logger.info(
            f"Audio loaded: {len(audio_data)} samples, "
            f"{len(audio_data) / sample_rate:.1f}s duration"
        )
        
        logger.info(
            f"Processing with input_language={input_language}, "
            f"output_language={output_language}"
        )
        
        result = _pipeline.process(
            audio_data,
            input_language=input_language,
            output_language=output_language,
        )
        return result
        
    finally:
        try:
            os.remove(wav_path)
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser(description="Dictate Web Server")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    
    import uvicorn
    
    print(f"\n🚀 Starting Dictate Web Server at http://{args.host}:{args.port}")
    print("   Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "dictate.server:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
