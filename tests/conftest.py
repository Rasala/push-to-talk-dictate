"""Pytest configuration and fixtures."""

from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING, Generator

import numpy as np
import pytest

if TYPE_CHECKING:
    from numpy.typing import NDArray


@pytest.fixture
def sample_audio_16k() -> NDArray[np.int16]:
    """Generate 1 second of sample audio at 16kHz."""
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    # Generate a 440Hz sine wave
    audio = np.sin(2 * np.pi * 440 * t) * 0.5
    return (audio * 32767).astype(np.int16)


@pytest.fixture
def sample_audio_silent() -> NDArray[np.int16]:
    """Generate 1 second of silent audio at 16kHz."""
    return np.zeros(16000, dtype=np.int16)


@pytest.fixture
def temp_wav_file(sample_audio_16k: NDArray[np.int16]) -> Generator[str, None, None]:
    """Create a temporary WAV file with sample audio."""
    from scipy.io.wavfile import write as wav_write

    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    wav_write(path, 16000, sample_audio_16k)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Fixture to clean environment variables before/after tests."""
    # Store original values
    env_vars = [
        "DICTATE_AUDIO_DEVICE",
        "DICTATE_OUTPUT_MODE",
        "DICTATE_INPUT_LANGUAGE",
        "DICTATE_OUTPUT_LANGUAGE",
        "DICTATE_VERBOSE",
        "DICTATE_LLM_CLEANUP",
        "DICTATE_LLM_MODEL",
    ]
    original_values = {var: os.environ.get(var) for var in env_vars}

    # Clear all
    for var in env_vars:
        os.environ.pop(var, None)

    yield

    # Restore original values
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value
        else:
            os.environ.pop(var, None)
