"""Speech-to-text transcription and text cleanup."""

from __future__ import annotations

import logging
import os
import tempfile
from typing import TYPE_CHECKING

import mlx_whisper
from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler
from scipy.io.wavfile import write as wav_write

if TYPE_CHECKING:
    from numpy.typing import NDArray
    import numpy as np
    from mlx.nn import Module

    from dictate.config import LLMConfig, WhisperConfig

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """Transcribes audio to text using Whisper."""

    def __init__(self, config: "WhisperConfig") -> None:
        self._config = config
        self._model_loaded = False

    def transcribe(
        self,
        audio: "NDArray[np.int16]",
        sample_rate: int,
    ) -> str:
        """
        Transcribe audio to text.
        
        Args:
            audio: Audio data as 16-bit integer samples.
            sample_rate: Sample rate of the audio.
            
        Returns:
            Transcribed text.
        """
        wav_path = self._save_temp_wav(audio, sample_rate)
        try:
            if not self._model_loaded:
                logger.info("Loading Whisper model: %s", self._config.model)
                self._model_loaded = True

            result = mlx_whisper.transcribe(
                wav_path,
                path_or_hf_repo=self._config.model,
                language=self._config.language,
            )
            text = result.get("text", "")
            return str(text) if isinstance(text, str) else ""
        finally:
            self._cleanup_temp_file(wav_path)

    def _save_temp_wav(
        self,
        audio: "NDArray[np.int16]",
        sample_rate: int,
    ) -> str:
        """Save audio to a temporary WAV file."""
        fd, path = tempfile.mkstemp(suffix=".wav", prefix="dictate_")
        os.close(fd)
        wav_write(path, sample_rate, audio)
        return path

    def _cleanup_temp_file(self, path: str) -> None:
        """Remove temporary file."""
        try:
            os.remove(path)
        except OSError as e:
            logger.warning("Failed to remove temp file %s: %s", path, e)


class TextCleaner:
    """Cleans up transcribed text using an LLM."""

    def __init__(self, config: "LLMConfig") -> None:
        self._config = config
        self._model: "Module | None" = None
        self._tokenizer = None

    def load_model(self) -> None:
        """Load the LLM model."""
        if self._model is not None:
            return

        logger.info("Loading LLM model: %s", self._config.model)
        self._model, self._tokenizer = load(self._config.model)
        logger.info("LLM model loaded")

    def cleanup(self, text: str) -> str:
        """
        Clean up transcribed text.
        
        Args:
            text: Raw transcribed text.
            
        Returns:
            Cleaned text with fixed grammar and punctuation.
        """
        if not self._config.enabled:
            return text

        if self._model is None or self._tokenizer is None:
            self.load_model()

        # Build chat-formatted prompt for AI prompt formatting
        messages = [
            {"role": "system", "content": self._config.system_prompt},
            {"role": "user", "content": text},
        ]
        prompt = self._tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        # Limit tokens based on input length to prevent repetition
        input_words = len(text.split())
        max_tokens = min(self._config.max_tokens, max(50, input_words * 3))

        # Use greedy sampling for deterministic output
        sampler = make_sampler(temp=self._config.temperature)
        
        result = generate(
            self._model,
            self._tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            sampler=sampler,
        )

        return self._postprocess(result.strip())

    def _postprocess(self, text: str) -> str:
        """Post-process generated text to handle LLM quirks."""
        # Strip common LLM preambles (case-insensitive)
        preambles = [
            # "Sure" variants
            "Sure, here's the corrected text:",
            "Sure, here is the corrected text:",
            "Sure, here's the text:",
            "Sure, here is the text:",
            "Sure, here you go:",
            "Sure!",
            "Sure:",
            "Sure,",
            # "Here" variants
            "Here's the corrected text:",
            "Here is the corrected text:",
            "Here's the formatted text:",
            "Here is the formatted text:",
            "Here's the text:",
            "Here is the text:",
            "Here you go:",
            "Here it is:",
            # "Corrected/Fixed" variants
            "Corrected text:",
            "Corrected:",
            "Fixed text:",
            "Fixed:",
            "Formatted text:",
            "Formatted:",
            # "The" variants
            "The corrected text is:",
            "The corrected text:",
            "The text:",
            # "I" variants
            "I've corrected the text:",
            "I have corrected the text:",
            "I fixed the text:",
            # "Of course" variants
            "Of course!",
            "Of course:",
            "Of course,",
            # "Certainly" variants
            "Certainly!",
            "Certainly:",
            "Certainly,",
            # Other
            "Output:",
            "Result:",
            "Answer:",
        ]
        
        text_lower = text.lower()
        for preamble in preambles:
            if text_lower.startswith(preamble.lower()):
                text = text[len(preamble):].strip()
                text_lower = text.lower()  # Update for next iteration
        
        # Strip surrounding quotes if present
        if len(text) >= 2 and text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        if len(text) >= 2 and text.startswith("'") and text.endswith("'"):
            text = text[1:-1]
        
        # Remove leading newlines
        text = text.lstrip('\n')
        
        lines = text.split("\n")
        if not lines:
            return text

        # Detect repetition: if lines repeat, return just the first
        first_line = lines[0].strip()
        if len(lines) > 1 and lines[1].strip() == first_line:
            logger.warning("Detected repetition in LLM output, truncating")
            return first_line

        return text


class TranscriptionPipeline:
    """Complete transcription pipeline: audio → text → cleaned text."""

    def __init__(
        self,
        whisper_config: "WhisperConfig",
        llm_config: "LLMConfig",
    ) -> None:
        self._whisper = WhisperTranscriber(whisper_config)
        self._cleaner = TextCleaner(llm_config)
        self._sample_rate = 16_000

    def set_sample_rate(self, sample_rate: int) -> None:
        """Set the audio sample rate."""
        self._sample_rate = sample_rate

    def preload_models(self) -> None:
        """Pre-load all models for faster first transcription."""
        self._cleaner.load_model()
        logger.info("Whisper model will load on first use: %s", self._whisper._config.model)

    def process(self, audio: "NDArray[np.int16]") -> str | None:
        """
        Process audio through the full transcription pipeline.
        
        Args:
            audio: Audio data as 16-bit integer samples.
            
        Returns:
            Cleaned transcribed text, or None if transcription failed.
        """
        duration_s = len(audio) / self._sample_rate
        logger.info("Processing audio chunk (%.2fs)", duration_s)

        # Step 1: Transcribe with Whisper
        logger.info("Running Whisper transcription...")
        import time
        t0 = time.time()
        raw_text = self._whisper.transcribe(audio, self._sample_rate).strip()
        t1 = time.time()
        logger.info("Whisper done in %.2fs", t1 - t0)

        if not raw_text:
            logger.warning("Whisper returned empty transcription")
            return None

        logger.info("Raw transcription: \"%s\"", raw_text)

        # Step 2: Clean up with LLM
        logger.info("Running LLM cleanup...")
        t2 = time.time()
        cleaned_text = self._cleaner.cleanup(raw_text).strip()
        t3 = time.time()
        logger.info("LLM cleanup done in %.2fs", t3 - t2)

        if not cleaned_text:
            logger.warning("LLM returned empty text")
            return None

        logger.info("Cleaned text: \"%s\"", cleaned_text)
        return cleaned_text
