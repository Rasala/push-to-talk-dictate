import type { LanguageCode, LanguageOption } from '../types';
import './LanguageSelector.css';

interface LanguageSelectorProps {
  id: string;
  label: string;
  value: LanguageCode;
  options: LanguageOption[];
  onChange: (value: LanguageCode) => void;
}

export function LanguageSelector({
  id,
  label,
  value,
  options,
  onChange,
}: LanguageSelectorProps) {
  return (
    <div className="language-selector">
      <label htmlFor={id}>{label}</label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value as LanguageCode)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
