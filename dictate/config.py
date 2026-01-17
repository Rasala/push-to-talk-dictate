"""Configuration for the Dictate application."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pynput.keyboard import Key

from pynput import keyboard


class OutputMode(str, Enum):
    """Output mode for transcribed text."""

    TYPE = "type"  # Type directly into focused window
    CLIPBOARD = "clipboard"  # Copy to clipboard only


@dataclass
class AudioConfig:
    """Audio capture configuration."""

    sample_rate: int = 16_000
    channels: int = 1
    block_ms: int = 30
    device_id: int | None = None  # None = system default

    @property
    def block_size(self) -> int:
        """Calculate block size in samples."""
        return int(self.sample_rate * (self.block_ms / 1000.0))


@dataclass
class VADConfig:
    """Voice Activity Detection configuration."""

    rms_threshold: float = 0.012
    silence_timeout_s: float = 2.0
    pre_roll_s: float = 0.25
    post_roll_s: float = 0.15


@dataclass
class ToneConfig:
    """Audio feedback tone configuration."""

    enabled: bool = True
    start_hz: int = 880
    stop_hz: int = 440
    duration_s: float = 0.04
    volume: float = 0.15


@dataclass
class WhisperConfig:
    """Whisper transcription configuration."""

    model: str = "mlx-community/whisper-large-v3-mlx"
    language: str = "en"


@dataclass
class LLMConfig:
    """LLM text cleanup configuration."""

    enabled: bool = True
    model: str = "Qwen/Qwen2-1.5B-Instruct-MLX"
    system_prompt: str = (
        "You are a prompt formatter for AI coding assistants. Your job is to clean up "
        "voice-transcribed text into a clear, well-structured prompt. "
        "RULES: "
        "1) Fix punctuation and capitalize properly. "
        "2) PRESERVE all technical terms exactly: SQL, API, JSON, REST, GraphQL, Python, JavaScript, etc. "
        "3) PRESERVE code snippets, file paths, variable names, and CLI commands exactly. "
        "4) Keep the original meaning and intent - do NOT add or remove information. "
        "5) Do NOT answer the prompt or respond to it - just format it. "
        "6) Output ONLY the formatted prompt text, nothing else."
    )
    max_tokens: int = 300
    temperature: float = 0.0


@dataclass
class KeybindConfig:
    """Keyboard shortcut configuration."""

    ptt_key: "Key" = field(default_factory=lambda: keyboard.Key.alt_l)
    quit_key: "Key" = field(default_factory=lambda: keyboard.Key.esc)
    quit_modifier: "Key" = field(default_factory=lambda: keyboard.Key.cmd)


@dataclass
class Config:
    """Main application configuration."""

    # Sub-configurations
    audio: AudioConfig = field(default_factory=AudioConfig)
    vad: VADConfig = field(default_factory=VADConfig)
    tones: ToneConfig = field(default_factory=ToneConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    keybinds: KeybindConfig = field(default_factory=KeybindConfig)

    # Output settings
    output_mode: OutputMode = OutputMode.TYPE
    min_hold_to_process_s: float = 0.25

    # Logging
    verbose: bool = True

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        config = cls()

        # Audio device
        if device := os.environ.get("DICTATE_AUDIO_DEVICE"):
            config.audio.device_id = int(device)

        # Output mode
        if mode := os.environ.get("DICTATE_OUTPUT_MODE"):
            config.output_mode = OutputMode(mode.lower())

        # Whisper language
        if lang := os.environ.get("DICTATE_LANGUAGE"):
            config.whisper.language = lang

        # Verbose logging
        if verbose := os.environ.get("DICTATE_VERBOSE"):
            config.verbose = verbose.lower() in ("1", "true", "yes")

        # LLM cleanup
        if llm_enabled := os.environ.get("DICTATE_LLM_CLEANUP"):
            config.llm.enabled = llm_enabled.lower() in ("1", "true", "yes")

        return config
