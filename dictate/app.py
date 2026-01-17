"""Main Dictation application."""

from __future__ import annotations

import logging
import queue
import signal
import threading
import time
from typing import TYPE_CHECKING

import numpy as np

from dictate.audio import (
    AudioCapture,
    get_device_name,
    list_input_devices,
    play_tone,
)
from dictate.config import Config
from dictate.output import TextAggregator, create_output_handler
from dictate.transcribe import TranscriptionPipeline

if TYPE_CHECKING:
    from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class DictationApp:
    """
    Push-to-Talk Dictation Application.
    
    Captures audio while a key is held, transcribes it using Whisper,
    cleans up the text with an LLM, and outputs it to the focused window.
    """

    def __init__(self, config: Config | None = None) -> None:
        self._config = config or Config()
        
        # Work queue for background processing
        self._work_queue: queue.Queue[NDArray[np.int16]] = queue.Queue()
        self._stop_event = threading.Event()
        
        # Components (initialized in setup)
        self._audio: AudioCapture | None = None
        self._pipeline: TranscriptionPipeline | None = None
        self._output = create_output_handler(self._config.output_mode)
        self._aggregator = TextAggregator()
        
        # Worker thread
        self._worker: threading.Thread | None = None

    def setup(self) -> None:
        """Initialize all components."""
        self._print_banner()
        self._print_devices()
        
        # Initialize transcription pipeline
        self._pipeline = TranscriptionPipeline(
            whisper_config=self._config.whisper,
            llm_config=self._config.llm,
        )
        self._pipeline.set_sample_rate(self._config.audio.sample_rate)
        self._pipeline.preload_models()
        
        # Initialize audio capture
        self._audio = AudioCapture(
            audio_config=self._config.audio,
            vad_config=self._config.vad,
            on_chunk_ready=self._on_chunk_ready,
        )
        
        # Start worker thread
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()
        
        self._print_instructions()

    def _print_banner(self) -> None:
        """Print application banner."""
        print("=" * 60)
        print("🎙️ DICTATE - Push-to-Talk Voice Dictation")
        print("=" * 60)

    def _print_devices(self) -> None:
        """Print available audio devices."""
        print("\n🎤 Available audio input devices:")
        print("-" * 50)
        for device in list_input_devices():
            print(f"  {device}")
        print("-" * 50)
        
        device_name = get_device_name(self._config.audio.device_id)
        if self._config.audio.device_id is not None:
            print(f"\n✅ Using input device [{self._config.audio.device_id}]: {device_name}")
        else:
            print(f"\n✅ Using DEFAULT input device: {device_name}")
        
        print(f"\n🔊 Output mode: {self._config.output_mode.value}")

    def _print_instructions(self) -> None:
        """Print usage instructions."""
        print("\n" + "=" * 60)
        print("📌 INSTRUCTIONS:")
        print("   • Hold Left Option (⌥) to talk. Release to stop.")
        print("   • Press Cmd+Esc to quit cleanly. Ctrl+C also works.")
        print("   • Pause while holding → processes chunk & keeps listening.")
        print(f"   • Text will be {'TYPED into the focused window' if self._config.output_mode.value == 'type' else 'copied to CLIPBOARD'}.")
        print("=" * 60)
        print("\n🟢 Ready! Hold Option key to start dictating...\n")

    def start_recording(self) -> None:
        """Start recording audio."""
        if self._audio is None:
            logger.error("App not initialized. Call setup() first.")
            return
            
        if self._audio.is_recording:
            return
            
        play_tone(
            self._config.tones,
            self._config.tones.start_hz,
            self._config.audio.sample_rate,
        )
        self._audio.start()
        print("🎙️ Recording...")

    def stop_recording(self) -> None:
        """Stop recording and process audio."""
        if self._audio is None or not self._audio.is_recording:
            return
            
        play_tone(
            self._config.tones,
            self._config.tones.stop_hz,
            self._config.audio.sample_rate,
        )
        
        duration = self._audio.stop()
        
        if duration < self._config.min_hold_to_process_s:
            print("⛔️ Ignored tap (too short)")
            return
            
        print("🛑 Stopped.")

    def _on_chunk_ready(self, audio: "NDArray[np.int16]") -> None:
        """Handle audio chunk ready for processing."""
        self._work_queue.put(audio)

    def _worker_loop(self) -> None:
        """Background worker for processing audio chunks."""
        while not self._stop_event.is_set():
            try:
                audio = self._work_queue.get(timeout=0.5)
            except queue.Empty:
                continue
                
            if self._stop_event.is_set():
                break
                
            if audio.size == 0:
                continue
                
            self._process_chunk(audio)

    def _process_chunk(self, audio: "NDArray[np.int16]") -> None:
        """Process a single audio chunk."""
        if self._pipeline is None:
            return
            
        try:
            text = self._pipeline.process(audio)
            if text:
                self._emit_output(text)
        except Exception as e:
            logger.exception("Processing error: %s", e)
            print(f"❌ Processing error: {e}")

    def _emit_output(self, text: str) -> None:
        """Emit processed text to output."""
        # Aggregate and output
        full_text = self._aggregator.append(text)
        
        print(f"\n✅ Output: \"{text}\"")
        
        try:
            # For clipboard, we want the full aggregated text
            # For typing, we only type the new text
            from dictate.config import OutputMode
            
            if self._config.output_mode == OutputMode.CLIPBOARD:
                from dictate.output import ClipboardOutput
                ClipboardOutput().output(full_text)
            else:
                self._output.output(text)
            
            print("---")
        except Exception as e:
            logger.error("Output error: %s", e)
            print(f"   ⚠️ Output error: {e}")
            print("   📋 Text available in clipboard (Cmd+V)")

    def shutdown(self) -> None:
        """Shutdown the application gracefully."""
        logger.info("Shutting down...")
        
        # Stop recording if active
        if self._audio and self._audio.is_recording:
            play_tone(
                self._config.tones,
                self._config.tones.stop_hz,
                self._config.audio.sample_rate,
            )
            self._audio.stop()
        
        # Signal worker to stop
        self._stop_event.set()
        
        # Unblock the worker queue
        try:
            self._work_queue.put_nowait(np.zeros((0,), dtype=np.int16))
        except queue.Full:
            pass
        
        # Wait for worker to finish
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=2.0)

    def run(self) -> None:
        """Run the application with keyboard listener."""
        from pynput import keyboard
        
        self.setup()
        
        cmd_down = False
        quitting = False
        listener_ref: keyboard.Listener | None = None
        
        def request_quit() -> bool:
            nonlocal quitting
            if quitting:
                return False
            quitting = True
            print("\n👋 Quitting...")
            self.shutdown()
            return True
        
        def on_press(key: keyboard.Key | keyboard.KeyCode | None) -> None:
            nonlocal cmd_down
            
            if key == self._config.keybinds.quit_modifier:
                cmd_down = True
                return
            
            if key == self._config.keybinds.ptt_key:
                self.start_recording()
        
        def on_release(key: keyboard.Key | keyboard.KeyCode | None) -> bool | None:
            nonlocal cmd_down
            
            if key == self._config.keybinds.quit_modifier:
                cmd_down = False
                return None
            
            if key == self._config.keybinds.quit_key and cmd_down:
                if request_quit():
                    return False  # Stop listener
                return None
            
            if key == self._config.keybinds.ptt_key:
                time.sleep(0.05)  # Small delay for cleaner cutoff
                self.stop_recording()
            
            return None
        
        # Handle Ctrl+C
        def handle_sigint(sig: int, frame: object) -> None:
            self.shutdown()
            raise SystemExit(0)
        
        signal.signal(signal.SIGINT, handle_sigint)
        
        # Run keyboard listener
        with keyboard.Listener(
            on_press=on_press,
            on_release=on_release,
        ) as listener:
            listener_ref = listener
            listener.join()
        
        # Ensure shutdown on listener exit
        self.shutdown()
