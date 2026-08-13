import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Triangle } from 'lucide-react';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { VectorValue } from '../AlgebraicMethods';

function DimensionNumberInput({ value, min = 2, max = 6, onCommit, className }: { value: number; min?: number; max?: number; onCommit: (v: number) => void; className?: string }) {
  const [str, setStr] = useState(String(value));
  useEffect(() => setStr(String(value)), [value]);
  return (
    <Input
      type="number"
      min={String(min)}
      max={String(max)}
      value={str}
      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setStr(e.target.value)}
      onBlur={() => {
        const n = parseInt(str);
        if (!isNaN(n)) onCommit(Math.max(min, Math.min(max, n)));
        else onCommit(min);
      }}
      onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
          const n = parseInt(str);
          if (!isNaN(n)) onCommit(Math.max(min, Math.min(max, n)));
          else onCommit(min);
        }
      }}
      className={className}
    />
  );
}

interface VectorInputProps {
  label: string;
  vector: VectorValue;
  dimension: number;
  isSelected: boolean;
  selectedIndex: number | null;
  onSelectVector: () => void;
  onSelectCell: (index: number) => void;
  onCellChange?: (index: number, value: string) => void;
  errors?: Record<string, string | undefined>;
  onDimensionChange: (dimension: number) => void;
}

export function VectorInput({
  label,
  vector,
  dimension,
  isSelected,
  selectedIndex,
  onSelectVector,
  onSelectCell,
  onCellChange,
  errors,
  onDimensionChange,
}: VectorInputProps) {
  return (
    <motion.div
      className={`backdrop-blur-xl bg-white/5 border rounded-2xl p-6 transition-all duration-300 ${
        isSelected ? 'border-purple-400/50 shadow-lg shadow-purple-500/20' : 'border-white/10'
      }`}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.02 }}
      onClick={onSelectVector}
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="backdrop-blur-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-white/10 rounded-lg p-2">
          <Triangle size={20} className="text-purple-300" />
        </div>
        <h3 className="text-xl text-purple-200">{label}</h3>
      </div>

      {/* Dimension Control */}
      <div className="mb-4">
        <Label className="text-purple-200/80 text-sm mb-1">Dimensión</Label>
        <DimensionNumberInput
          value={dimension}
          min={2}
          max={6}
          onCommit={(v) => onDimensionChange(v)}
          className="backdrop-blur-lg bg-white/10 border-white/20 text-purple-100 focus:border-purple-400"
        />
      </div>

      {/* Vector Display */}
      <div className="backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl p-4">
        <div className="flex items-center gap-2">
          <span className="text-purple-200 text-2xl">[</span>
          <div className="flex flex-col gap-2">
            {vector.map((value, i) => {
              const isCellSelected = selectedIndex === i && isSelected;
              return (
                <div key={i} className="w-20 h-14">
                  <Input
                    value={String(value)}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectCell(i);
                    }}
                    onChange={(e) => onCellChange?.(i, e.target.value)}
                    onFocus={() => onSelectCell(i)}
                    title={errors?.[String(i)]}
                    className={`w-full h-full text-sm text-center rounded-lg p-2 transition-all ${
                      isCellSelected
                        ? 'bg-purple-500/30 border-purple-400 text-purple-100 shadow-lg shadow-purple-500/30'
                        : 'bg-white/5 border-white/20 text-purple-100 hover:bg-white/10'
                    } ${errors?.[String(i)] ? 'border-red-400 ring-1 ring-red-400' : ''}`}
                  />
                </div>
              );
            })}
          </div>
          <span className="text-purple-200 text-2xl">]</span>
        </div>
      </div>

      {/* Info text */}
      <p className="text-purple-300/60 text-xs mt-3 text-center">
        Vector de dimensión {dimension}
      </p>
    </motion.div>
  );
}