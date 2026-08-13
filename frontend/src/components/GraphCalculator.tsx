import { useState, useEffect, useRef } from 'react';
import { MathInput } from './keyboard_components/MathInput';
import { Keyboard } from './keyboard_components/Keyboard';
import { Plus, Trash2, LineChart } from 'lucide-react';

interface Expression {
  id: string;
  latex: string;
  color: string;
}

const COLORS = [
  '#c74440', '#2d70b3', '#388c46', '#6042a6', '#000000',
  '#fa7e19', '#6b3c8f', '#ee4266', '#0ead69', '#ffd23f'
];

declare global {
  interface Window {
    Desmos?: any;
  }
}


export function GraphCalculator() {
    const [currentLatex, setCurrentLatex] = useState('');
    const [expressions, setExpressions] = useState<Expression[]>([]);
    const calculatorRef = useRef<any>(null);
    const graphContainerRef = useRef<HTMLDivElement>(null);
    const colorIndexRef = useRef(0);

    useEffect(() => {
    let destroyed = false;
    let calculator: any = null;

    const initCalculator = () => {
        if (!graphContainerRef.current || !window.Desmos || destroyed) return;
    
        calculator = window.Desmos.GraphingCalculator(graphContainerRef.current, {
            keypad: false,
            expressions: false,
            settingsMenu: true,
            zoomButtons: true,
            expressionsTopbar: false,
            border: false,
        });
    
        calculatorRef.current = calculator;
    
        calculator.updateSettings({
            fontSize: 14,
            invertedColors: true,
        });
    };

    const ensureDesmosLoaded = () => {
        // Si ya está cargado (porque otro componente lo hizo, o por HMR), solo inicializamos
        if (window.Desmos) {
            initCalculator();
            return;
        }
    
        // Evitar cargar dos veces el script
        const existingScript = document.querySelector<HTMLScriptElement>(
            'script[data-desmos="true"]'
        );
        if (existingScript) {
            existingScript.addEventListener('load', initCalculator);
            return;
        }
      
        const script = document.createElement('script');
        script.src = 'https://www.desmos.com/api/v1.9/calculator.js?apiKey=dcb31709b452b1cf9dc26972add0fda6';
        script.async = true;
        script.dataset.desmos = 'true';
      
        script.onload = () => {
            console.log('Desmos loaded:', window.Desmos);
            initCalculator();
        };
      
        document.body.appendChild(script);
    };

    ensureDesmosLoaded();

    return () => {
        destroyed = true;
        if (calculatorRef.current) {
            calculatorRef.current.destroy?.();
            calculatorRef.current = null;
        }
    };
    }, []);

    const handleAddExpression = () => {
        if (!currentLatex.trim() || !calculatorRef.current) return;

        const newExpression: Expression = {
            id: `expr-${Date.now()}`,
            latex: currentLatex,
            color: COLORS[colorIndexRef.current % COLORS.length],
        };

        // Agregar a Desmos
        calculatorRef.current.setExpression({
            id: newExpression.id,
            latex: newExpression.latex,
            color: newExpression.color,
        });

        // Agregar a la lista local
        setExpressions([...expressions, newExpression]);

        // Incrementar índice de color
        colorIndexRef.current += 1;

        // Limpiar input
        setCurrentLatex('');
        if ((window as any).mathFieldInstance) {
            (window as any).mathFieldInstance.latex('');
        }
    };

    const handleRemoveExpression = (id: string) => {
        if (!calculatorRef.current) return;

        // Remover de Desmos
        calculatorRef.current.removeExpression({ id });

        // Remover de la lista local
        setExpressions(expressions.filter(expr => expr.id !== id));
    };

    const handleClearAll = () => {
        if (!calculatorRef.current) return;

        // Remover todas las expresiones de Desmos
        expressions.forEach(expr => {
            calculatorRef.current.removeExpression({ id: expr.id });
        });

        // Limpiar lista local
        setExpressions([]);
        colorIndexRef.current = 0;
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleAddExpression();
        }
    };

    return (
        <div className="bg-[#1e2b4a]/60 rounded-2xl p-6 border border-[#4a5f8f]/30 backdrop-blur-sm shadow-2xl w-full max-w-[1400px]">
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center gap-2 text-sm text-gray-400">
                    <LineChart className="w-4 h-4 text-[#7c6fd6]" />
                    <span>Graficadora de Funciones</span>
                </div>

                {/* Input y Keyboard lado a lado */}
                <div className="grid grid-cols-1 lg:grid-cols-[1fr,400px] gap-6">
                    {/* Columna Izquierda: Input y botón */}
                    <div className="space-y-3">
                        <label className="text-sm text-gray-400">Ingresa tu función:</label>
                        <div className="flex gap-2">
                            <div className="flex-1" onKeyPress={handleKeyPress}>
                                <MathInput 
                                  onLatexChange={setCurrentLatex}
                                  initialLatex=""
                                />
                            </div>
                            <button
                                onClick={handleAddExpression}
                                disabled={!currentLatex.trim()}
                                className="px-4 py-2 bg-gradient-to-r from-[#5b4fc7] to-[#7c6fd6] rounded-lg hover:shadow-lg hover:shadow-[#7c6fd6]/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 whitespace-nowrap"
                            >
                                <Plus className="w-4 h-4" />
                                Graficar
                            </button>
                        </div>

                        {/* Lista de expresiones */}
                        {expressions.length > 0 && (
                          <div className="space-y-2 mt-4">
                                <div className="flex items-center justify-between">
                                    <label className="text-sm text-gray-400">Funciones graficadas:</label>
                                    <button
                                        onClick={handleClearAll}
                                        className="text-xs text-gray-400 hover:text-red-400 transition-colors"
                                    >
                                        Limpiar todo
                                    </button>
                                </div>
                                <div className="space-y-2 max-h-40 overflow-y-auto">
                                    {expressions.map((expr) => (
                                        <div
                                            key={expr.id}
                                            className="flex items-center gap-3 p-3 bg-[#2a3b5f]/40 rounded-lg border border-[#4a5f8f]/30 group hover:border-[#7c6fd6]/50 transition-colors"
                                        >
                                            <div
                                                className="w-3 h-3 rounded-full flex-shrink-0"
                                                style={{ backgroundColor: expr.color }}
                                            />
                                            <code className="flex-1 text-sm text-gray-300 break-all">
                                                {expr.latex}
                                            </code>
                                            <button
                                                onClick={() => handleRemoveExpression(expr.id)}
                                                className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-500/20 rounded"
                                            >
                                                <Trash2 className="w-4 h-4 text-red-400" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                          </div>
                        )}
                    </div>
                    
                    {/* Columna Derecha: Keyboard */}
                    <div>
                        <label className="text-sm text-gray-400 mb-3 block">Teclado matemático:</label>
                        <Keyboard />
                    </div>
                </div>
                  
                {/* Gráfica de Desmos */}
                <div className="space-y-2">
                    <label className="text-sm text-gray-400">Plano cartesiano:</label>
                    <div
                        ref={graphContainerRef}
                        className="w-full h-[500px] rounded-lg overflow-hidden border border-[#4a5f8f]/30 bg-white"
                        style={{ minHeight: '500px' }}
                    />
                </div>
                  
                {/* Tips */}
                <div className="p-3 bg-[#2a3b5f]/20 rounded-lg border border-[#4a5f8f]/20">
                    <div className="text-xs text-gray-400 space-y-1">
                        <div><strong className="text-gray-300">Tip:</strong> Presiona Enter para graficar rápidamente</div>
                        <div><strong className="text-gray-300">Ejemplos:</strong> y = x², y = sin(x), x² + y² = 25</div>
                    </div>
                </div>
            </div>
        </div>

    );

}