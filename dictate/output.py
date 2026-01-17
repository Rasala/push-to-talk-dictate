"""Output handlers for transcribed text."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pyperclip
from pynput.keyboard import Controller as KeyboardController

if TYPE_CHECKING:
    from dictate.config import OutputMode

logger = logging.getLogger(__name__)


class OutputHandler(ABC):
    """Abstract base class for output handlers."""

    @abstractmethod
    def output(self, text: str) -> None:
        """Output the transcribed text."""
        ...


class ClipboardOutput(OutputHandler):
    """Outputs text to the system clipboard."""

    def output(self, text: str) -> None:
        """Copy text to clipboard."""
        pyperclip.copy(text)


class TyperOutput(OutputHandler):
    """Types text directly into the focused window."""

    def __init__(self) -> None:
        self._controller = KeyboardController()

    def output(self, text: str) -> None:
        """Type text into the focused window."""
        try:
            # Small delay to ensure the window is ready
            time.sleep(0.05)
            self._controller.type(text)
        except Exception as e:
            logger.error("Failed to type text: %s", e)
            raise


class CompositeOutput(OutputHandler):
    """Combines multiple output handlers."""

    def __init__(self, *handlers: OutputHandler) -> None:
        self._handlers = handlers

    def output(self, text: str) -> None:
        """Output text through all handlers."""
        for handler in self._handlers:
            try:
                handler.output(text)
            except Exception as e:
                logger.error("Output handler %s failed: %s", type(handler).__name__, e)


class TextAggregator:
    """Aggregates text from multiple transcription chunks."""

    def __init__(self) -> None:
        self._full_text = ""

    @property
    def full_text(self) -> str:
        """Get the complete aggregated text."""
        return self._full_text

    def append(self, text: str) -> str:
        """
        Append text to the aggregated output.
        
        Args:
            text: New text to append.
            
        Returns:
            The complete aggregated text.
        """
        text = text.strip()
        if self._full_text:
            self._full_text = self._full_text.rstrip() + "\n" + text
        else:
            self._full_text = text
        return self._full_text

    def clear(self) -> None:
        """Clear the aggregated text."""
        self._full_text = ""


def create_output_handler(mode: "OutputMode") -> OutputHandler:
    """
    Create an output handler based on the configured mode.
    
    Args:
        mode: The output mode.
        
    Returns:
        An appropriate output handler.
    """
    from dictate.config import OutputMode

    clipboard = ClipboardOutput()

    if mode == OutputMode.CLIPBOARD:
        return clipboard

    # TYPE mode: type into window + clipboard backup
    return CompositeOutput(TyperOutput(), clipboard)
