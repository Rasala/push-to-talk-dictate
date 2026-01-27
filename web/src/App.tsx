import { useState, useEffect } from 'react';
import {
  StatusIndicator,
  RecordButton,
  AudioVisualizer,
  LanguageSelector,
  TranscriptionOutput,
  ErrorMessage,
} from './components';
import { useWebSocket, useAudioRecorder } from './hooks';
import {
  type LanguageCode,
  type StatusState,
  type ServerConfig,
  Language,
  Status,
  WebSocketStatus,
  LANGUAGE_OPTIONS,
  OUTPUT_LANGUAGE_OPTIONS,
} from './types';
import './App.css';

const TIMER_INTERVAL_MS = 100;

function formatTime(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

export function App() {
  const [inputLanguage, setInputLanguage] = useState<LanguageCode>(Language.AUTO);
  const [outputLanguage, setOutputLanguage] = useState<LanguageCode>(Language.AUTO);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [transcription, setTranscription] = useState('');
  const [lastResultMessage, setLastResultMessage] = useState<string | null>(null);

  const { isConnected, sendConfig, sendAudio } = useWebSocket({
    onMessage: (message) => {
      if (message.status === WebSocketStatus.COMPLETE) {
        setIsProcessing(false);
        if (message.text) {
          setTranscription(message.text);
          setLastResultMessage('Done!');
        } else {
          setLastResultMessage('No speech detected');
        }
      } else if (message.status === WebSocketStatus.ERROR) {
        setIsProcessing(false);
        setError(message.text ?? 'Transcription failed');
      }
    },
    onError: setError,
  });

  const handleRecordingComplete = (blob: Blob) => {
    sendConfig({
      input_language: inputLanguage === Language.AUTO ? null : inputLanguage,
      output_language: outputLanguage === Language.AUTO ? null : outputLanguage,
    });
    sendAudio(blob);
  };

  const { isRecording, startRecording, stopRecording, analyser } = useAudioRecorder({
    onRecordingComplete: handleRecordingComplete,
    onError: setError,
  });

  useEffect(() => {
    fetch('/config')
      .then((res) => res.json())
      .then((config: ServerConfig) => {
        setInputLanguage((config.input_language as LanguageCode) ?? Language.AUTO);
        setOutputLanguage((config.output_language as LanguageCode) ?? Language.AUTO);
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!isRecording) {
      setRecordingTime(0);
      return;
    }

    const startTime = Date.now();
    const interval = setInterval(() => {
      setRecordingTime(Date.now() - startTime);
    }, TIMER_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [isRecording]);

  const status: StatusState = (() => {
    if (error) return Status.ERROR;
    if (isRecording) return Status.RECORDING;
    if (isProcessing) return Status.PROCESSING;
    if (lastResultMessage === 'Done!') return Status.SUCCESS;
    return Status.IDLE;
  })();

  const statusText = (() => {
    if (error) return 'Error';
    if (isRecording) return 'Recording...';
    if (isProcessing) return 'Processing...';
    if (lastResultMessage) return lastResultMessage;
    return 'Ready';
  })();

  const hintText = (() => {
    if (isProcessing) return 'Processing...';
    if (isRecording) return 'Click to stop recording';
    return 'Click to start recording';
  })();

  const handleToggleRecording = async () => {
    if (isProcessing) return;

    if (isRecording) {
      stopRecording();
      setIsProcessing(true);
    } else {
      setError(null);
      setLastResultMessage(null);
      await startRecording();
    }
  };

  return (
    <div className="container">
      <header>
        <h1>🎙️ Dictate</h1>
        <p className="subtitle">Local Voice Transcription powered by MLX Whisper</p>
      </header>

      <main>
        <StatusIndicator state={status} text={statusText} />

        <RecordButton
          isRecording={isRecording}
          isProcessing={isProcessing}
          onClick={handleToggleRecording}
        />

        <p className="hint">{hintText}</p>

        <AudioVisualizer analyser={analyser} isActive={isRecording} />

        {isRecording && <div className="timer">{formatTime(recordingTime)}</div>}

        <TranscriptionOutput text={transcription} />

        <ErrorMessage message={error} onDismiss={() => setError(null)} />
      </main>

      <footer>
        <div className="config">
          <LanguageSelector
            id="inputLanguage"
            label="Input:"
            value={inputLanguage}
            options={LANGUAGE_OPTIONS}
            onChange={setInputLanguage}
          />
          <LanguageSelector
            id="outputLanguage"
            label="Output:"
            value={outputLanguage}
            options={OUTPUT_LANGUAGE_OPTIONS}
            onChange={setOutputLanguage}
          />
        </div>
        <p className="info">
          <span className={`connection-status ${isConnected ? 'connected' : ''}`}>
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
        </p>
      </footer>
    </div>
  );
}
