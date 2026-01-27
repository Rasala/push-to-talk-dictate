"""Tests for the config module."""

from __future__ import annotations

import os

import pytest

from dictate.config import (
    AudioConfig,
    Config,
    LANGUAGE_NAMES,
    LLMConfig,
    LLMModel,
    OutputMode,
    ToneConfig,
    VADConfig,
    WhisperConfig,
)


class TestAudioConfig:
    """Tests for AudioConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = AudioConfig()
        assert config.sample_rate == 16_000
        assert config.channels == 1
        assert config.block_ms == 30
        assert config.device_id is None

    def test_block_size_calculation(self) -> None:
        """Test block size is calculated correctly."""
        config = AudioConfig(sample_rate=16000, block_ms=30)
        # 16000 * 0.030 = 480
        assert config.block_size == 480

    def test_block_size_with_different_rates(self) -> None:
        """Test block size with different sample rates."""
        config = AudioConfig(sample_rate=48000, block_ms=20)
        # 48000 * 0.020 = 960
        assert config.block_size == 960


class TestVADConfig:
    """Tests for VADConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default VAD configuration."""
        config = VADConfig()
        assert config.rms_threshold == 0.012
        assert config.silence_timeout_s == 2.0
        assert config.pre_roll_s == 0.25
        assert config.post_roll_s == 0.15


class TestToneConfig:
    """Tests for ToneConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default tone configuration."""
        config = ToneConfig()
        assert config.enabled is True
        assert config.start_hz == 880
        assert config.stop_hz == 440
        assert config.duration_s == 0.04
        assert config.volume == 0.15


class TestWhisperConfig:
    """Tests for WhisperConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default Whisper configuration."""
        config = WhisperConfig()
        assert config.model == "mlx-community/whisper-large-v3-mlx"
        assert config.language is None  # Auto-detect

    def test_custom_language(self) -> None:
        """Test setting a specific language."""
        config = WhisperConfig(language="pl")
        assert config.language == "pl"


class TestLLMConfig:
    """Tests for LLMConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default LLM configuration."""
        config = LLMConfig()
        assert config.enabled is True
        assert config.model_choice == LLMModel.QWEN
        assert config.max_tokens == 300
        assert config.temperature == 0.0
        assert config.output_language is None

    def test_model_path_qwen(self) -> None:
        """Test Qwen model path."""
        config = LLMConfig(model_choice=LLMModel.QWEN)
        assert config.model == "mlx-community/Qwen2.5-3B-Instruct-4bit"

    def test_model_path_phi3(self) -> None:
        """Test Phi-3 model path."""
        config = LLMConfig(model_choice=LLMModel.PHI3)
        assert config.model == "mlx-community/Phi-3-mini-4k-instruct-4bit"

    def test_system_prompt_preserves_language(self) -> None:
        """Test system prompt without output language."""
        config = LLMConfig(output_language=None)
        prompt = config.get_system_prompt()
        assert "Preserve the original language" in prompt

    def test_system_prompt_with_output_language(self) -> None:
        """Test system prompt with specific output language."""
        config = LLMConfig(output_language="pt")
        prompt = config.get_system_prompt()
        assert "Portuguese" in prompt
        assert "Translate" in prompt

    def test_system_prompt_override(self) -> None:
        """Test system prompt with language override."""
        config = LLMConfig(output_language=None)
        prompt = config.get_system_prompt(output_language="de")
        assert "German" in prompt
        assert "Translate" in prompt

    def test_system_prompt_backward_compatibility(self) -> None:
        """Test system_prompt property for backward compatibility."""
        config = LLMConfig(output_language="en")
        assert config.system_prompt == config.get_system_prompt()


class TestOutputMode:
    """Tests for OutputMode enum."""

    def test_type_mode(self) -> None:
        """Test TYPE output mode."""
        assert OutputMode.TYPE.value == "type"

    def test_clipboard_mode(self) -> None:
        """Test CLIPBOARD output mode."""
        assert OutputMode.CLIPBOARD.value == "clipboard"

    def test_from_string(self) -> None:
        """Test creating OutputMode from string."""
        assert OutputMode("type") == OutputMode.TYPE
        assert OutputMode("clipboard") == OutputMode.CLIPBOARD


class TestLLMModel:
    """Tests for LLMModel enum."""

    def test_phi3(self) -> None:
        """Test PHI3 model enum."""
        assert LLMModel.PHI3.value == "phi3"

    def test_qwen(self) -> None:
        """Test QWEN model enum."""
        assert LLMModel.QWEN.value == "qwen"


class TestLanguageNames:
    """Tests for language name mapping."""

    def test_all_languages_have_names(self) -> None:
        """Test that all expected languages have names."""
        expected_languages = ["en", "pl", "de", "fr", "es", "it", "pt", "nl", "ja", "zh", "ko", "ru"]
        for lang in expected_languages:
            assert lang in LANGUAGE_NAMES
            assert isinstance(LANGUAGE_NAMES[lang], str)
            assert len(LANGUAGE_NAMES[lang]) > 0


class TestConfig:
    """Tests for main Config dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration."""
        config = Config()
        assert isinstance(config.audio, AudioConfig)
        assert isinstance(config.vad, VADConfig)
        assert isinstance(config.tones, ToneConfig)
        assert isinstance(config.whisper, WhisperConfig)
        assert isinstance(config.llm, LLMConfig)
        assert config.output_mode == OutputMode.TYPE
        assert config.min_hold_to_process_s == 0.25
        assert config.verbose is True

    def test_from_env_audio_device(self, clean_env: None) -> None:
        """Test loading audio device from environment."""
        os.environ["DICTATE_AUDIO_DEVICE"] = "3"
        config = Config.from_env()
        assert config.audio.device_id == 3

    def test_from_env_output_mode(self, clean_env: None) -> None:
        """Test loading output mode from environment."""
        os.environ["DICTATE_OUTPUT_MODE"] = "clipboard"
        config = Config.from_env()
        assert config.output_mode == OutputMode.CLIPBOARD

    def test_from_env_input_language(self, clean_env: None) -> None:
        """Test loading input language from environment."""
        os.environ["DICTATE_INPUT_LANGUAGE"] = "pl"
        config = Config.from_env()
        assert config.whisper.language == "pl"

    def test_from_env_input_language_auto(self, clean_env: None) -> None:
        """Test auto input language from environment."""
        os.environ["DICTATE_INPUT_LANGUAGE"] = "auto"
        config = Config.from_env()
        assert config.whisper.language is None

    def test_from_env_output_language(self, clean_env: None) -> None:
        """Test loading output language from environment."""
        os.environ["DICTATE_OUTPUT_LANGUAGE"] = "en"
        config = Config.from_env()
        assert config.llm.output_language == "en"

    def test_from_env_output_language_auto(self, clean_env: None) -> None:
        """Test auto output language from environment."""
        os.environ["DICTATE_OUTPUT_LANGUAGE"] = "auto"
        config = Config.from_env()
        assert config.llm.output_language is None

    def test_from_env_verbose(self, clean_env: None) -> None:
        """Test loading verbose setting from environment."""
        os.environ["DICTATE_VERBOSE"] = "false"
        config = Config.from_env()
        assert config.verbose is False

        os.environ["DICTATE_VERBOSE"] = "true"
        config = Config.from_env()
        assert config.verbose is True

    def test_from_env_llm_cleanup(self, clean_env: None) -> None:
        """Test loading LLM cleanup setting from environment."""
        os.environ["DICTATE_LLM_CLEANUP"] = "false"
        config = Config.from_env()
        assert config.llm.enabled is False

    def test_from_env_llm_model(self, clean_env: None) -> None:
        """Test loading LLM model choice from environment."""
        os.environ["DICTATE_LLM_MODEL"] = "phi3"
        config = Config.from_env()
        assert config.llm.model_choice == LLMModel.PHI3

    def test_from_env_invalid_llm_model(self, clean_env: None) -> None:
        """Test invalid LLM model keeps default."""
        os.environ["DICTATE_LLM_MODEL"] = "invalid"
        config = Config.from_env()
        assert config.llm.model_choice == LLMModel.QWEN  # Default
