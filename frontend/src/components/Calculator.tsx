import { useState } from 'react';
import { MathInput } from './keyboard_components/MathInput';
import { Keyboard } from './keyboard_components/Keyboard';

export function Calculator() {
    const [latex, setLatex] = useState('');

    return (
        <div className="bg-[#1e2b4a]/60 rounded-2xl p-6 border border-[#4a5f8f]/30 backdrop-blur-sm shadow-2xl">
            <div className="space-y-6">
                {/* Vista Previa Label */}
                <div className="flex items-center gap-2 text-sm text-gray-400">
                    <div className="w-4 h-4 grid grid-cols-2 gap-0.5">
                        <div className="bg-[#7c6fd6] rounded-sm"></div>
                        <div className="bg-[#7c6fd6] rounded-sm"></div>
                        <div className="bg-[#7c6fd6] rounded-sm"></div>
                        <div className="bg-[#7c6fd6] rounded-sm"></div>
                    </div>
                    <span>Editor de Expresiones</span>
                </div>

                {/* Math Input */}
                <div className="space-y-2">
                    <label className="text-sm text-gray-400">Expresión matemática:</label>
                    <MathInput 
                        onLatexChange={setLatex}
                        initialLatex=""
                    />
                </div>

                {/* LaTeX Output (opcional, para debug) */}
                {latex && (
                    <div className="p-3 bg-[#2a3b5f]/40 rounded-lg border border-[#4a5f8f]/30">
                        <div className="text-xs text-gray-400 mb-1">LaTeX:</div>
                        <code className="text-sm text-[#9b8ae8] break-all">{latex}</code>
                    </div>
                )}

                {/* Keyboard */}
                <Keyboard />
            </div>
        </div>
    );
}   