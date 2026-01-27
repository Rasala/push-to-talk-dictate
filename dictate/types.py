"""Type definitions for the Dictate application."""

from __future__ import annotations

from typing import Literal, TypedDict

# Language codes supported by the application
LanguageCode = Literal[
    "en", "pl", "de", "fr", "es", "it", "pt", "nl", "ja", "zh", "ko", "ru"
]


class TranscriptionResult(TypedDict, total=False):
    """Result from Whisper transcription."""

    text: str
    segments: list[dict]
    language: str


class WebSocketConfigMessage(TypedDict):
    """Configuration message sent over WebSocket."""

    type: Literal["config"]
    input_language: str | None
    output_language: str | None


class WebSocketResponseMessage(TypedDict, total=False):
    """Response message sent over WebSocket."""

    status: Literal["processing", "complete", "error"]
    text: str
    message: str


class ServerConfig(TypedDict):
    """Server configuration returned by /config endpoint."""

    input_language: str | None
    output_language: str | None
    llm_enabled: bool
    llm_model: str
    sample_rate: int


class HealthCheck(TypedDict):
    """Health check response."""

    status: Literal["healthy", "unhealthy"]
    models_loaded: bool
