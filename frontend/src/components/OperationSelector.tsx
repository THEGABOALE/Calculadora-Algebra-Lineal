import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';

interface Operation {
  id: string;
  label: string;
  icon: LucideIcon;
  description: string;
  single?: boolean;
}

interface OperationSelectorProps {
  operations: Operation[];
  selectedOperation: string;
  onSelectOperation: (operation: string) => void;
}

export function OperationSelector({
  operations,
  selectedOperation,
  onSelectOperation,
}: OperationSelectorProps) {
  return (
    <motion.div
      className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <h3 className="text-xl text-blue-200 mb-4">Operaciones Disponibles</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {operations.map((op) => (
          <motion.button
            key={op.id}
            onClick={() => onSelectOperation(op.id)}
            className={`backdrop-blur-lg border rounded-xl p-4 flex flex-col items-center gap-2 transition-all group ${
              selectedOperation === op.id
                ? 'bg-gradient-to-br from-purple-500/30 to-pink-500/30 border-purple-400 shadow-lg shadow-purple-500/30'
                : 'bg-white/5 border-white/20 hover:bg-white/10 hover:border-purple-400/50'
            }`}
            whileHover={{ scale: 1.05, y: -2 }}
            whileTap={{ scale: 0.95 }}
          >
            <op.icon
              size={24}
              className={selectedOperation === op.id ? 'text-purple-200' : 'text-blue-300 group-hover:text-purple-300'}
            />
            <span
              className={`text-sm ${
                selectedOperation === op.id ? 'text-purple-100' : 'text-blue-200 group-hover:text-purple-200'
              }`}
            >
              {op.label}
            </span>
            <span
              className={`text-xs text-center ${
                selectedOperation === op.id ? 'text-purple-200/70' : 'text-blue-300/50'
              }`}
            >
              {op.description}
            </span>
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}