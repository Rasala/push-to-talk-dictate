#!/usr/bin/env python3
"""
Dictate - Push-to-Talk Voice Dictation

A local, privacy-first voice dictation app for macOS using Apple Silicon MLX models.

Usage:
    python ptt_dictate.py [options]

Environment Variables:
    DICTATE_AUDIO_DEVICE    Audio input device index
    DICTATE_OUTPUT_MODE     Output mode: 'type' or 'clipboard'
    DICTATE_INPUT_LANGUAGE  Whisper language code (e.g., 'en', 'pl', or 'auto')
    DICTATE_VERBOSE         Enable verbose logging: '1' or 'true'
    DICTATE_LLM_CLEANUP     Enable LLM text cleanup: '1' or 'true'
"""

from dictate.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
