import { useEffect, useRef, useState } from 'react';
import type { WebSocketResponseMessage, WebSocketConfigMessage } from '../types';

interface UseWebSocketOptions {
  onMessage: (message: WebSocketResponseMessage) => void;
  onError?: (error: string) => void;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  sendConfig: (config: Omit<WebSocketConfigMessage, 'type'>) => void;
  sendAudio: (blob: Blob) => void;
}

const RECONNECT_DELAY_MS = 3000;

export function useWebSocket({ onMessage, onError }: UseWebSocketOptions): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  
  const latestOnMessage = useRef(onMessage);
  const latestOnError = useRef(onError);
  latestOnMessage.current = onMessage;
  latestOnError.current = onError;

  useEffect(() => {
    const connect = () => {
      const isAlreadyConnected = socketRef.current?.readyState === WebSocket.OPEN;
      const isConnecting = socketRef.current?.readyState === WebSocket.CONNECTING;
      if (isAlreadyConnected || isConnecting) {
        return;
      }
      
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/transcribe`;

      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
      };

      socket.onclose = () => {
        setIsConnected(false);
        socketRef.current = null;
        reconnectTimerRef.current = window.setTimeout(connect, RECONNECT_DELAY_MS);
      };

      socket.onerror = () => {
        latestOnError.current?.('Connection error. Please refresh the page.');
      };

      socket.onmessage = (event) => {
        const message = JSON.parse(event.data as string) as WebSocketResponseMessage;
        latestOnMessage.current(message);
      };
    };

    connect();

    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (socketRef.current) {
        socketRef.current.onclose = null;
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, []);

  const sendConfig = (config: Omit<WebSocketConfigMessage, 'type'>) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      const message: WebSocketConfigMessage = { type: 'config', ...config };
      socketRef.current.send(JSON.stringify(message));
    }
  };

  const sendAudio = (blob: Blob) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(blob);
    }
  };

  return { isConnected, sendConfig, sendAudio };
}
