"""Tests for the server module."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from numpy.typing import NDArray
    import numpy as np


@pytest.fixture
def mock_pipeline() -> MagicMock:
    """Create a mock transcription pipeline."""
    pipeline = MagicMock()
    pipeline.process.return_value = "Transcribed text"
    pipeline.preload_models.return_value = None
    pipeline.set_sample_rate.return_value = None
    return pipeline


@pytest.fixture
def mock_config() -> MagicMock:
    """Create a mock configuration."""
    from dictate.config import LLMConfig, LLMModel, WhisperConfig, AudioConfig

    config = MagicMock()
    config.whisper = WhisperConfig(language="en")
    config.llm = LLMConfig(enabled=True, output_language=None)
    config.audio = AudioConfig(sample_rate=16000)
    return config


@pytest.fixture
def test_client(mock_pipeline: MagicMock, mock_config: MagicMock) -> TestClient:
    """Create a test client with mocked dependencies."""
    with patch("dictate.server._pipeline", mock_pipeline), \
         patch("dictate.server._config", mock_config):
        from dictate.server import create_app

        app = create_app()
        return TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check_healthy(
        self, test_client: TestClient, mock_pipeline: MagicMock
    ) -> None:
        """Test health check returns healthy when pipeline is loaded."""
        with patch("dictate.server._pipeline", mock_pipeline):
            response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["models_loaded"] is True

    def test_health_check_not_loaded(self, test_client: TestClient) -> None:
        """Test health check when pipeline is not loaded."""
        with patch("dictate.server._pipeline", None):
            response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["models_loaded"] is False


class TestConfigEndpoint:
    """Tests for /config endpoint."""

    def test_get_config(
        self, test_client: TestClient, mock_config: MagicMock
    ) -> None:
        """Test getting configuration."""
        with patch("dictate.server._config", mock_config):
            response = test_client.get("/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "input_language" in data
        assert "output_language" in data
        assert "llm_enabled" in data
        assert "sample_rate" in data

    def test_get_config_not_initialized(self, test_client: TestClient) -> None:
        """Test getting config when not initialized."""
        with patch("dictate.server._config", None):
            response = test_client.get("/config")
        
        assert response.status_code == 503
        data = response.json()
        assert "error" in data


class TestConvertWebmToWav:
    """Tests for convert_webm_to_wav function."""

    @patch("dictate.server.subprocess.run")
    def test_convert_success(self, mock_run: MagicMock) -> None:
        """Test successful WebM to WAV conversion."""
        from dictate.server import convert_webm_to_wav

        mock_run.return_value = MagicMock(returncode=0)

        # Create minimal WebM data (just needs to be bytes)
        webm_data = b"fake webm data"

        wav_path = convert_webm_to_wav(webm_data, 16000)

        assert wav_path.endswith(".wav")
        mock_run.assert_called_once()

        # Verify ffmpeg command structure
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "ffmpeg"
        assert "-ar" in call_args
        assert "16000" in call_args
        assert "-ac" in call_args
        assert "1" in call_args

    @patch("dictate.server.subprocess.run")
    def test_convert_failure(self, mock_run: MagicMock) -> None:
        """Test WebM to WAV conversion failure."""
        from dictate.server import convert_webm_to_wav

        mock_run.return_value = MagicMock(returncode=1, stderr="ffmpeg error")

        webm_data = b"fake webm data"

        with pytest.raises(RuntimeError, match="ffmpeg conversion failed"):
            convert_webm_to_wav(webm_data, 16000)


class TestProcessAudioData:
    """Tests for process_audio_data function."""

    @patch("dictate.server.convert_webm_to_wav")
    @patch("dictate.server.wav_read")
    def test_process_audio_success(
        self,
        mock_wav_read: MagicMock,
        mock_convert: MagicMock,
        mock_pipeline: MagicMock,
        mock_config: MagicMock,
        sample_audio_16k: "NDArray[np.int16]",
    ) -> None:
        """Test successful audio processing."""
        import numpy as np
        from dictate.server import process_audio_data

        mock_convert.return_value = "/tmp/test.wav"
        mock_wav_read.return_value = (16000, sample_audio_16k)
        mock_pipeline.process.return_value = "Hello world"

        with patch("dictate.server._pipeline", mock_pipeline), \
             patch("dictate.server._config", mock_config), \
             patch("dictate.server.os.remove"):
            result = process_audio_data(b"webm data", "en", "pt")

        assert result == "Hello world"
        mock_pipeline.process.assert_called_once()
        
        # Verify language parameters were passed
        call_kwargs = mock_pipeline.process.call_args[1]
        assert call_kwargs["input_language"] == "en"
        assert call_kwargs["output_language"] == "pt"

    def test_process_audio_not_initialized(self) -> None:
        """Test processing when pipeline not initialized."""
        from dictate.server import process_audio_data

        with patch("dictate.server._pipeline", None), \
             patch("dictate.server._config", None):
            with pytest.raises(RuntimeError, match="Pipeline not initialized"):
                process_audio_data(b"webm data")


class TestWebSocketProtocol:
    """Tests for WebSocket message handling."""

    def test_config_message_parsing(self) -> None:
        """Test parsing of config message."""
        config_msg = {
            "type": "config",
            "input_language": "pl",
            "output_language": "en",
        }

        assert config_msg["type"] == "config"
        assert config_msg["input_language"] == "pl"
        assert config_msg["output_language"] == "en"

    def test_config_message_with_auto(self) -> None:
        """Test config message with auto (null) languages."""
        config_msg = {
            "type": "config",
            "input_language": None,
            "output_language": None,
        }

        assert config_msg["input_language"] is None
        assert config_msg["output_language"] is None

    def test_response_message_processing(self) -> None:
        """Test processing response message format."""
        response = {
            "status": "processing",
        }
        assert response["status"] == "processing"

    def test_response_message_complete(self) -> None:
        """Test complete response message format."""
        response = {
            "status": "complete",
            "text": "Transcribed text",
        }
        assert response["status"] == "complete"
        assert response["text"] == "Transcribed text"

    def test_response_message_error(self) -> None:
        """Test error response message format."""
        response = {
            "status": "error",
            "text": "Something went wrong",
        }
        assert response["status"] == "error"
        assert response["text"] == "Something went wrong"
