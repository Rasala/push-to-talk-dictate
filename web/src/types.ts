/**
 * Language code constants
 */
export const Language = {
  AUTO: 'auto',
  EN: 'en',
  PL: 'pl',
  DE: 'de',
  FR: 'fr',
  ES: 'es',
  IT: 'it',
  PT: 'pt',
  NL: 'nl',
  JA: 'ja',
  ZH: 'zh',
  KO: 'ko',
  RU: 'ru',
} as const;

/**
 * Supported language codes for transcription
 */
export type LanguageCode = (typeof Language)[keyof typeof Language];

/**
 * Server configuration response from /config endpoint
 */
export interface ServerConfig {
  input_language: string | null;
  output_language: string | null;
  llm_enabled: boolean;
  llm_model: string;
  sample_rate: number;
}

/**
 * WebSocket configuration message sent to server before audio
 */
export interface WebSocketConfigMessage {
  type: 'config';
  input_language: string | null;
  output_language: string | null;
}

/**
 * WebSocket message status constants
 */
export const WebSocketStatus = {
  PROCESSING: 'processing',
  COMPLETE: 'complete',
  ERROR: 'error',
} as const;

/**
 * WebSocket response message from server
 */
export interface WebSocketResponseMessage {
  status: (typeof WebSocketStatus)[keyof typeof WebSocketStatus];
  text?: string;
  message?: string;
}

/**
 * Status states for the UI
 */
export const Status = {
  IDLE: 'idle',
  RECORDING: 'recording',
  PROCESSING: 'processing',
  SUCCESS: 'success',
  ERROR: 'error',
} as const;

export type StatusState = (typeof Status)[keyof typeof Status];

/**
 * Language option for select dropdowns
 */
export interface LanguageOption {
  value: LanguageCode;
  label: string;
}

export const LANGUAGE_OPTIONS: LanguageOption[] = [
  { value: 'auto', label: 'Auto-detect' },
  { value: 'en', label: 'English' },
  { value: 'pl', label: 'Polish' },
  { value: 'de', label: 'German' },
  { value: 'fr', label: 'French' },
  { value: 'es', label: 'Spanish' },
  { value: 'it', label: 'Italian' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'nl', label: 'Dutch' },
  { value: 'ja', label: 'Japanese' },
  { value: 'zh', label: 'Chinese' },
  { value: 'ko', label: 'Korean' },
  { value: 'ru', label: 'Russian' },
];

export const OUTPUT_LANGUAGE_OPTIONS: LanguageOption[] = [
  { value: 'auto', label: 'Same as input' },
  ...LANGUAGE_OPTIONS.slice(1),
];

/**
 * Declare webkitAudioContext for Safari compatibility
 */
declare global {
  interface Window {
    webkitAudioContext: typeof AudioContext;
  }
}
