"""Tests for the transcribe module."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from dictate.config import LLMConfig, LLMModel, WhisperConfig

if TYPE_CHECKING:
    from numpy.typing import NDArray
    import numpy as np


class TestWhisperTranscriber:
    """Tests for WhisperTranscriber class."""

    def test_init(self) -> None:
        """Test WhisperTranscriber initialization."""
        from dictate.transcribe import WhisperTranscriber

        config = WhisperConfig(language="en")
        transcriber = WhisperTranscriber(config)
        assert transcriber._config == config
        assert transcriber._model_loaded is False

    def test_save_temp_wav(self, sample_audio_16k: "NDArray[np.int16]") -> None:
        """Test saving audio to temporary WAV file."""
        import os

        from dictate.transcribe import WhisperTranscriber

        config = WhisperConfig()
        transcriber = WhisperTranscriber(config)

        wav_path = transcriber._save_temp_wav(sample_audio_16k, 16000)
        try:
            assert os.path.exists(wav_path)
            assert wav_path.endswith(".wav")
            assert "dictate_" in wav_path
        finally:
            transcriber._cleanup_temp_file(wav_path)

    def test_cleanup_temp_file(self, temp_wav_file: str) -> None:
        """Test cleaning up temporary files."""
        import os

        from dictate.transcribe import WhisperTranscriber

        config = WhisperConfig()
        transcriber = WhisperTranscriber(config)

        assert os.path.exists(temp_wav_file)
        transcriber._cleanup_temp_file(temp_wav_file)
        assert not os.path.exists(temp_wav_file)

    def test_cleanup_nonexistent_file(self) -> None:
        """Test cleanup handles missing files gracefully."""
        from dictate.transcribe import WhisperTranscriber

        config = WhisperConfig()
        transcriber = WhisperTranscriber(config)
        # Should not raise
        transcriber._cleanup_temp_file("/nonexistent/path/file.wav")

    @patch("dictate.transcribe.mlx_whisper.transcribe")
    def test_transcribe_uses_config_language(
        self, mock_transcribe: MagicMock, sample_audio_16k: "NDArray[np.int16]"
    ) -> None:
        """Test transcribe uses language from config."""
        from dictate.transcribe import WhisperTranscriber

        mock_transcribe.return_value = {"text": "Hello world"}

        config = WhisperConfig(language="en")
        transcriber = WhisperTranscriber(config)
        result = transcriber.transcribe(sample_audio_16k, 16000)

        assert result == "Hello world"
        mock_transcribe.assert_called_once()
        call_kwargs = mock_transcribe.call_args[1]
        assert call_kwargs["language"] == "en"

    @patch("dictate.transcribe.mlx_whisper.transcribe")
    def test_transcribe_uses_override_language(
        self, mock_transcribe: MagicMock, sample_audio_16k: "NDArray[np.int16]"
    ) -> None:
        """Test transcribe uses language override when provided."""
        from dictate.transcribe import WhisperTranscriber

        mock_transcribe.return_value = {"text": "Bonjour monde"}

        config = WhisperConfig(language="en")  # Config says English
        transcriber = WhisperTranscriber(config)
        result = transcriber.transcribe(sample_audio_16k, 16000, language="fr")  # Override to French

        assert result == "Bonjour monde"
        call_kwargs = mock_transcribe.call_args[1]
        assert call_kwargs["language"] == "fr"

    @patch("dictate.transcribe.mlx_whisper.transcribe")
    def test_transcribe_returns_empty_on_no_text(
        self, mock_transcribe: MagicMock, sample_audio_16k: "NDArray[np.int16]"
    ) -> None:
        """Test transcribe returns empty string when no text detected."""
        from dictate.transcribe import WhisperTranscriber

        mock_transcribe.return_value = {}

        config = WhisperConfig()
        transcriber = WhisperTranscriber(config)
        result = transcriber.transcribe(sample_audio_16k, 16000)

        assert result == ""


class TestTextCleaner:
    """Tests for TextCleaner class."""

    def test_init(self) -> None:
        """Test TextCleaner initialization."""
        from dictate.transcribe import TextCleaner

        config = LLMConfig()
        cleaner = TextCleaner(config)
        assert cleaner._config == config
        assert cleaner._model is None
        assert cleaner._tokenizer is None

    def test_cleanup_disabled(self) -> None:
        """Test cleanup returns original text when disabled."""
        from dictate.transcribe import TextCleaner

        config = LLMConfig(enabled=False)
        cleaner = TextCleaner(config)

        result = cleaner.cleanup("hello world")
        assert result == "hello world"

    @patch("dictate.transcribe.load")
    @patch("dictate.transcribe.generate")
    def test_cleanup_calls_llm(
        self, mock_generate: MagicMock, mock_load: MagicMock
    ) -> None:
        """Test cleanup calls LLM with correct prompt."""
        from dictate.transcribe import TextCleaner

        mock_tokenizer = MagicMock()
        mock_tokenizer.apply_chat_template.return_value = "formatted prompt"
        mock_load.return_value = (MagicMock(), mock_tokenizer)
        mock_generate.return_value = "Hello, world."

        config = LLMConfig(enabled=True)
        cleaner = TextCleaner(config)
        result = cleaner.cleanup("hello world")

        assert result == "Hello, world."
        mock_generate.assert_called_once()

    @patch("dictate.transcribe.load")
    @patch("dictate.transcribe.generate")
    def test_cleanup_with_output_language(
        self, mock_generate: MagicMock, mock_load: MagicMock
    ) -> None:
        """Test cleanup passes output language to prompt."""
        from dictate.transcribe import TextCleaner

        mock_tokenizer = MagicMock()
        mock_tokenizer.apply_chat_template.return_value = "formatted prompt"
        mock_load.return_value = (MagicMock(), mock_tokenizer)
        mock_generate.return_value = "Olá mundo."

        config = LLMConfig(enabled=True)
        cleaner = TextCleaner(config)
        cleaner.cleanup("hello world", output_language="pt")

        # Verify the system prompt contains Portuguese
        call_args = mock_tokenizer.apply_chat_template.call_args[0][0]
        system_message = call_args[0]
        assert "Portuguese" in system_message["content"]


class TestTextCleanerPostprocess:
    """Tests for TextCleaner._postprocess method."""

    def test_strips_special_tokens(self) -> None:
        """Test that special tokens are stripped."""
        from dictate.transcribe import TextCleaner

        config = LLMConfig(enabled=False)
        cleaner = TextCleaner(config)

        assert cleaner._postprocess("Hello<|end|>") == "Hello"
        assert cleaner._postprocess("Hello<|endoftext|>") == "Hello"
        assert cleaner._postprocess("Hello<|im_end|>") == "Hello"
        assert cleaner._postprocess("Hello</s>") == "Hello"

    def test_strips_preambles(self) -> None:
        """Test that common LLM preambles are stripped."""
        from dictate.transcribe import TextCleaner

        config = LLMConfig(enabled=False)
        cleaner = TextCleaner(config)

        assert cleaner._postprocess("Sure, here's the corrected text: Hello") == "Hello"
        assert cleaner._postprocess("Here is the text: Hello") == "Hello"
        assert cleaner._postprocess("Corrected: Hello") == "Hello"

    def test_strips_surrounding_quotes(self) -> None:
        """Test that surrounding quotes are stripped."""
        from dictate.transcribe import TextCleaner

        config = LLMConfig(enabled=False)
        cleaner = TextCleaner(config)

        assert cleaner._postprocess('"Hello world"') == "Hello world"
        assert cleaner._postprocess("'Hello world'") == "Hello world"

    def test_detects_repetition(self) -> None:
        """Test that repeated lines are truncated."""
        from dictate.transcribe import TextCleaner

        config = LLMConfig(enabled=False)
        cleaner = TextCleaner(config)

        result = cleaner._postprocess("Hello world\nHello world\nHello world")
        assert result == "Hello world"


class TestTranscriptionPipeline:
    """Tests for TranscriptionPipeline class."""

    def test_init(self) -> None:
        """Test TranscriptionPipeline initialization."""
        from dictate.transcribe import TranscriptionPipeline

        whisper_config = WhisperConfig()
        llm_config = LLMConfig()
        pipeline = TranscriptionPipeline(whisper_config, llm_config)

        assert pipeline._sample_rate == 16_000

    def test_set_sample_rate(self) -> None:
        """Test setting sample rate."""
        from dictate.transcribe import TranscriptionPipeline

        whisper_config = WhisperConfig()
        llm_config = LLMConfig()
        pipeline = TranscriptionPipeline(whisper_config, llm_config)

        pipeline.set_sample_rate(48000)
        assert pipeline._sample_rate == 48000

    @patch.object(
        __import__("dictate.transcribe", fromlist=["WhisperTranscriber"]).WhisperTranscriber,
        "transcribe",
    )
    @patch.object(
        __import__("dictate.transcribe", fromlist=["TextCleaner"]).TextCleaner,
        "cleanup",
    )
    def test_process_passes_languages(
        self,
        mock_cleanup: MagicMock,
        mock_transcribe: MagicMock,
        sample_audio_16k: "NDArray[np.int16]",
    ) -> None:
        """Test process passes language settings through pipeline."""
        from dictate.transcribe import TranscriptionPipeline

        mock_transcribe.return_value = "raw text"
        mock_cleanup.return_value = "cleaned text"

        whisper_config = WhisperConfig()
        llm_config = LLMConfig()
        pipeline = TranscriptionPipeline(whisper_config, llm_config)

        result = pipeline.process(
            sample_audio_16k,
            input_language="pl",
            output_language="en",
        )

        assert result == "cleaned text"
        mock_transcribe.assert_called_once()
        # Verify language was passed to transcribe
        assert mock_transcribe.call_args[1]["language"] == "pl"
        # Verify output_language was passed to cleanup
        assert mock_cleanup.call_args[1]["output_language"] == "en"

    @patch.object(
        __import__("dictate.transcribe", fromlist=["WhisperTranscriber"]).WhisperTranscriber,
        "transcribe",
    )
    def test_process_returns_none_on_empty(
        self,
        mock_transcribe: MagicMock,
        sample_audio_16k: "NDArray[np.int16]",
    ) -> None:
        """Test process returns None when no speech detected."""
        from dictate.transcribe import TranscriptionPipeline

        mock_transcribe.return_value = ""

        whisper_config = WhisperConfig()
        llm_config = LLMConfig()
        pipeline = TranscriptionPipeline(whisper_config, llm_config)

        result = pipeline.process(sample_audio_16k)
        assert result is None
