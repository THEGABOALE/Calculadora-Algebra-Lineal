import React, { useRef, useEffect } from 'react';

interface EscalarInputProps {
  value: string;
  onChange: (v: string) => void;
  onSelect: () => void;
  onBlur?: () => void;
  isSelected: boolean;
  label?: string;
}

export function EscalarInput({ value, onChange, onSelect, onBlur, isSelected, label = 'Escalar' }: EscalarInputProps) {
  const ref = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (isSelected && ref.current) ref.current.focus();
  }, [isSelected]);

  return (
    <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-3">
      <label className="text-sm text-purple-200 block mb-2">{label}:</label>
      <input
        ref={ref}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => onSelect()}
        onBlur={() => onBlur && onBlur()}
        className={`bg-white/5 border ${isSelected ? 'border-purple-400' : 'border-white/10'} rounded px-2 py-1 w-40`}
        placeholder="1 (ej: 3, pi, 1/2)"
      />
    </div>
  );
}

export default EscalarInput;
