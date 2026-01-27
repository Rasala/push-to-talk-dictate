import type { StatusState } from '../types';
import './StatusIndicator.css';

interface StatusIndicatorProps {
  state: StatusState;
  text: string;
}

export function StatusIndicator({ state, text }: StatusIndicatorProps) {
  return (
    <div className={`status status-${state}`}>
      <span className="status-dot" />
      <span className="status-text">{text}</span>
    </div>
  );
}
