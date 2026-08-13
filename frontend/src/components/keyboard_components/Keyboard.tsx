import { useState } from "react";
import { KEY_CATEGORIES, KeyCategory, Key } from "../../constants/keyboard-keys";
import { insertLatex } from "./MathInput";
import { Calculator, Sigma, TrendingUp, SquareFunction } from "lucide-react";

const CATEGORY_ICONS = {
    basicas: Calculator,
    funciones: SquareFunction,
    trigonometria: TrendingUp,
    calculos: Sigma,
}

const CATEGORY_LABELS = {
    basicas: 'Básicas',
    funciones: 'Funciones',
    trigonometria: 'Trigonometría',
    calculos: 'Cálculos',
}

export function Keyboard() {
    const [activeCategory, setActiveCategory] = useState<KeyCategory>('basicas');

    const handleKeyPress = (key: Key) => {
        insertLatex(key.latex);
    };

    const currentKeys = KEY_CATEGORIES[activeCategory];

    return (
        <div className="w-full space-y-4">
            {/* Selector de categorías */}
            <div className="flex gap-2 overflow-x-auto pb-2">
                {(Object.keys(KEY_CATEGORIES) as KeyCategory[]).map((category) => {
                    const Icon = CATEGORY_ICONS[category];
                    const isActive = activeCategory === category;
                    
                    return (
                        <button
                            key={category}
                            onClick={() => setActiveCategory(category)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all whitespace-nowrap ${
                                isActive
                                    ? 'bg-gradient-to-r from-[#5b4fc7] to-[#7c6fd6] text-white shadow-lg'
                                    : 'bg-[#2a3b5f]/40 text-gray-300 hover:bg-[#2a3b5f]/60'
                            }`}
                        >
                            <Icon className="w-4 h-4" />
                            <span>{CATEGORY_LABELS[category]}</span>
                        </button>
                    );
                })}
            </div>

            {/* Grid de teclas */}
            <div className="grid grid-cols-5 gap-2 p-4 bg-[#1e2b4a]/60 rounded-xl border border-[#4a5f8f]/30 backdrop-blur-sm">
                {currentKeys.map((key, index) => {
                    const isSpecial = ['AC', '⌫', '='].includes(key.label);
                    const isOperator = ['÷', '×', '−', '+', '−'].includes(key.label);
                    
                    return (
                        <button
                            key={`${key.label}-${index}`}
                            onClick={() => handleKeyPress(key)}
                            className={`
                                h-14 rounded-lg transition-all hover:scale-105 active:scale-95
                                flex items-center justify-center
                                ${isSpecial 
                                    ? 'bg-gradient-to-br from-[#7c6fd6] to-[#9b8ae8] text-white' 
                                    : isOperator
                                    ? 'bg-[#4a5f8f]/50 text-[#9b8ae8]'
                                    : 'bg-[#2a3b5f]/80 text-gray-200'
                                }
                                hover:shadow-lg hover:shadow-[#7c6fd6]/20
                                border border-[#4a5f8f]/30
                            `}
                        >
                            <span className={key.label.length > 3 ? 'text-sm' : ''}>{key.label}</span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}