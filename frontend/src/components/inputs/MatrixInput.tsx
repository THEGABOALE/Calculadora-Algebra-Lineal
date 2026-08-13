import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Grid3x3 } from 'lucide-react';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { MatrixValue } from '../AlgebraicMethods';

// Small controlled number input that allows typing (empty string) and commits on blur or Enter
function DimensionNumberInput({ value, min = 1, max = 6, onCommit, className }: { value: number; min?: number; max?: number; onCommit: (v: number) => void; className?: string }) {
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

interface MatrixInputProps {
  label: string;
  matrix: MatrixValue;
  dimensions: { rows: number; cols: number };
  isSelected: boolean;
  selectedCell: { row: number; col: number } | null;
  onSelectMatrix: () => void;
  onSelectCell: (row: number, col: number) => void;
  onCellChange?: (row: number, col: number, value: string) => void;
  errors?: Record<string, string | undefined>;
  onDimensionsChange: (rows: number, cols: number) => void;
}

export function MatrixInput({
  label,
  matrix,
  dimensions,
  isSelected,
  selectedCell,
  onSelectMatrix,
  onSelectCell,
  onCellChange,
  errors,
  onDimensionsChange,
}: MatrixInputProps) {
  return (
    <motion.div
      className={`backdrop-blur-xl bg-white/5 border rounded-2xl p-6 transition-all duration-300 ${
        isSelected ? 'border-purple-400/50 shadow-lg shadow-purple-500/20' : 'border-white/10'
      }`}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.02 }}
      onClick={onSelectMatrix}
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="backdrop-blur-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/10 rounded-lg p-2">
          <Grid3x3 size={20} className="text-blue-300" />
        </div>
        <h3 className="text-xl text-blue-200">{label}</h3>
      </div>

      {/* Dimension Controls */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <Label className="text-blue-200/80 text-sm mb-1">Filas</Label>
              <DimensionNumberInput
                value={dimensions.rows}
                min={1}
                max={6}
                onCommit={(v) => onDimensionsChange(v, dimensions.cols)}
                className="backdrop-blur-lg bg-white/10 border-white/20 text-blue-100 focus:border-purple-400"
              />
        </div>
        <div>
          <Label className="text-blue-200/80 text-sm mb-1">Columnas</Label>
              <DimensionNumberInput
                value={dimensions.cols}
                min={1}
                max={6}
                onCommit={(v) => onDimensionsChange(dimensions.rows, v)}
                className="backdrop-blur-lg bg-white/10 border-white/20 text-blue-100 focus:border-purple-400"
              />
        </div>
      </div>

      {/* Matrix Grid */}
      <div className="backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl p-4 overflow-x-auto">
        <div className="inline-flex flex-col gap-2">
          {matrix.map((row, i) => (
            <div key={i} className="flex gap-2">
              {row.map((cell, j) => {
                const isCellSelected = selectedCell?.row === i && selectedCell?.col === j && isSelected;
                return (
                  <div key={`${i}-${j}`} className="w-16 h-16">
                      <Input
                        value={String(cell)}
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectCell(i, j);
                        }}
                        onChange={(e) => {
                          onCellChange?.(i, j, e.target.value);
                        }}
                        onFocus={() => onSelectCell(i, j)}
                        title={errors?.[`${i}-${j}`]}
                        className={`w-full h-full text-sm text-center rounded-lg p-2 transition-all ${
                          isCellSelected
                            ? 'bg-purple-500/30 border-purple-400 text-purple-100 shadow-lg shadow-purple-500/30'
                            : 'bg-white/5 border-white/20 text-blue-100 hover:bg-white/10'
                        } ${errors?.[`${i}-${j}`] ? 'border-red-400 ring-1 ring-red-400' : ''}`}
                      />
                    </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
