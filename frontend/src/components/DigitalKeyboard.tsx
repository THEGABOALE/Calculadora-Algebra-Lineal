import { motion } from 'framer-motion';
import { Delete, X, Calculator } from 'lucide-react';

interface DigitalKeyboardProps {
  onKeyPress: (value: string) => void;
  // Can be a matrix cell {row,col} or a vector selection {vector,index}
  // additionally support scalar selection marker (when scalar input is focused)
  selectedCell:
    | { row: number; col: number }
    | { vector: 'A' | 'B' | 'C'; index: number }
    | { scalar: true }
    | null;
}

export function DigitalKeyboard({ onKeyPress, selectedCell }: DigitalKeyboardProps) {
  const keys = [
    ['7', '8', '9', '/'],
    ['4', '5', '6', '*'],
    ['1', '2', '3', '-'],
    ['0', '.', '(', ')'],
    ['^', '√', 'π', '+'],
  ];

  const specialKeys = [
    { label: '+/-', value: '+/-', icon: null },
    { label: 'C', value: 'clear', icon: X },
    { label: '⌫', value: 'backspace', icon: Delete },
  ];

  return (
    <motion.div
      className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6 sticky top-8"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.1 }}
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="backdrop-blur-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-white/10 rounded-lg p-2">
          <Calculator size={20} className="text-purple-300" />
        </div>
        <h3 className="text-xl text-purple-200">Teclado Digital</h3>
      </div>

      {/* Cell indicator */}
      {selectedCell && (
        <motion.div
          className="backdrop-blur-lg bg-purple-500/20 border border-purple-400/30 rounded-lg p-3 mb-4"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <p className="text-sm text-purple-200 text-center">
            { 'scalar' in selectedCell ? (
              <>Escalar seleccionado</>
            ) : "row" in selectedCell ? (
              <>Celda seleccionada: [{selectedCell.row + 1}, {selectedCell.col + 1}]</>
            ) : (
              <>Vector seleccionado: [{selectedCell.vector} - {selectedCell.index + 1}]</>
            )}
          </p>
        </motion.div>
      )}

      {/* Main number pad */}
      <div className="space-y-2 mb-4">
        {keys.map((row, i) => (
          <div key={i} className="grid grid-cols-4 gap-2">
            {row.map((key) => (
              <motion.button
                key={key}
                onClick={() => selectedCell && onKeyPress(key)}
                disabled={!selectedCell}
                className={`backdrop-blur-lg border rounded-lg p-4 transition-all ${
                  selectedCell
                    ? 'bg-white/10 border-white/20 text-blue-100 hover:bg-white/20 hover:border-purple-400/50 hover:shadow-lg hover:shadow-purple-500/20'
                    : 'bg-white/5 border-white/10 text-blue-300/50 cursor-not-allowed'
                }`}
                whileHover={selectedCell ? { scale: 1.05 } : {}}
                whileTap={selectedCell ? { scale: 0.95 } : {}}
              >
                {key}
              </motion.button>
            ))}
          </div>
        ))}
      </div>

      {/* Special keys */}
      <div className="grid grid-cols-3 gap-2">
        {specialKeys.map((key) => (
          <motion.button
            key={key.value}
            onClick={() => selectedCell && onKeyPress(key.value)}
            disabled={!selectedCell}
            className={`backdrop-blur-lg border rounded-lg p-4 flex items-center justify-center gap-2 transition-all ${
              selectedCell
                ? 'bg-gradient-to-br from-purple-500/20 to-pink-500/20 border-purple-400/30 text-purple-200 hover:from-purple-500/30 hover:to-pink-500/30 hover:shadow-lg hover:shadow-purple-500/20'
                : 'bg-white/5 border-white/10 text-purple-300/50 cursor-not-allowed'
            }`}
            whileHover={selectedCell ? { scale: 1.05 } : {}}
            whileTap={selectedCell ? { scale: 0.95 } : {}}
          >
            {key.icon && <key.icon size={16} />}
            <span>{key.label}</span>
          </motion.button>
        ))}
      </div>

      {/* Fraction and Power buttons */}
      <div className="grid grid-cols-2 gap-2 mt-4">
        <motion.button
          onClick={() => selectedCell && onKeyPress('/')}
          disabled={!selectedCell}
          className={`backdrop-blur-lg border rounded-lg p-3 transition-all ${
            selectedCell
              ? 'bg-blue-500/20 border-blue-400/30 text-blue-200 hover:bg-blue-500/30 hover:shadow-lg hover:shadow-blue-500/20'
              : 'bg-white/5 border-white/10 text-blue-300/50 cursor-not-allowed'
          }`}
          whileHover={selectedCell ? { scale: 1.05 } : {}}
          whileTap={selectedCell ? { scale: 0.95 } : {}}
        >
          <div className="flex flex-col items-center">
            <span className="text-xs">Fracción</span>
            <span>a/b</span>
          </div>
        </motion.button>

        <motion.button
          onClick={() => selectedCell && onKeyPress('^')}
          disabled={!selectedCell}
          className={`backdrop-blur-lg border rounded-lg p-3 transition-all ${
            selectedCell
              ? 'bg-blue-500/20 border-blue-400/30 text-blue-200 hover:bg-blue-500/30 hover:shadow-lg hover:shadow-blue-500/20'
              : 'bg-white/5 border-white/10 text-blue-300/50 cursor-not-allowed'
          }`}
          whileHover={selectedCell ? { scale: 1.05 } : {}}
          whileTap={selectedCell ? { scale: 0.95 } : {}}
        >
          <div className="flex flex-col items-center">
            <span className="text-xs">Potencia</span>
            <span>x^n</span>
          </div>
        </motion.button>
      </div>

      {/* Info */}
      {!selectedCell && (
        <motion.div
          className="mt-4 backdrop-blur-lg bg-blue-500/10 border border-blue-400/20 rounded-lg p-3"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <p className="text-xs text-blue-200/70 text-center">
            Selecciona una celda para comenzar a escribir
          </p>
        </motion.div>
      )}
    </motion.div>
  );
}