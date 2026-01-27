import { useState } from 'react';
import './TranscriptionOutput.css';

interface TranscriptionOutputProps {
  text: string;
}

export function TranscriptionOutput({ text }: TranscriptionOutputProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  if (!text) return null;

  return (
    <div className="output">
      <h2>Transcription</h2>
      <div className="transcription-text">{text}</div>
      <button className="copy-btn" onClick={handleCopy} title="Copy to clipboard">
        {copied ? '✅ Copied!' : '📋 Copy'}
      </button>
    </div>
  );
}
