import { useEffect, useRef } from 'react';

interface MathInputProps {
    onLatexChange?: (latex: string) => void;
    initialLatex?: string;
    instanceKey?: string;
}

export function MathInput({ onLatexChange, initialLatex = '', instanceKey }: MathInputProps) {
    const mathFieldRef = useRef<any>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Importar MathQuill dinamicamente
        const loadMathQuill = async () => {
            // Cargar jQuery (requerido por MathQuill)
            const jQueryScript = document.createElement('script');
            jQueryScript.src = 'https://code.jquery.com/jquery-3.6.0.min.js';
            document.head.appendChild(jQueryScript);

            await new Promise((resolve) => {
              jQueryScript.onload = resolve;
            });

            // Cargar MathQuill CSS
            const mathQuillCSS = document.createElement('link');
            mathQuillCSS.rel = 'stylesheet';
            mathQuillCSS.href = 'https://cdn.jsdelivr.net/npm/mathquill@0.10.1/build/mathquill.css';
            document.head.appendChild(mathQuillCSS);

            // Cargar MathQuill JS
            const mathQuillScript = document.createElement('script');
            mathQuillScript.src = 'https://cdn.jsdelivr.net/npm/mathquill@0.10.1/build/mathquill.min.js';
            document.head.appendChild(mathQuillScript);

            await new Promise((resolve) => {
                mathQuillScript.onload = resolve;
            });
        
            // Inicializar MathQuill
            if (containerRef.current && (window as any).MathQuill) {
                const MQ = (window as any).MathQuill.getInterface(2);
                const mathField = MQ.MathField(containerRef.current, {
                    spaceBehavesLikeTab: true,
                    leftRightIntoCmdGoes: 'up',
                    restrictMismatchedBrackets: true,
                    sumStartsWithNEquals: true,
                    supSubsRequireOperand: true,
                    charsThatBreakOutOfSupSub: '+-=<>',
                    autoSubscriptNumerals: true,
                    autoCommands: 'pi theta sqrt sum prod int',
                    autoOperatorNames: 'sin cos tan arcsin arccos arctan sinh cosh tanh ln log',
                    handlers: {
                        edit: function (mathField: any) {
                            const latex = mathField.latex();
                            onLatexChange?.(latex);
                        },
                    },
                });
          
                mathFieldRef.current = mathField;
          
                if (initialLatex) {
                    mathField.latex(initialLatex);
                }

                // Auto-focus para mostrar el cursor inmediatamente
                mathField.focus();

                // Register instances map and set current instance when clicked/focused
                try {
                    (window as any).mathFieldInstances = (window as any).mathFieldInstances || {};
                    if (instanceKey) {
                        (window as any).mathFieldInstances[instanceKey] = mathField;
                    }

                    // When this container is clicked, set the global active mathField
                    const setActive = () => {
                        (window as any).mathFieldInstance = mathField;
                        if (instanceKey) (window as any).currentMathFieldKey = instanceKey;
                    };

                    containerRef.current.addEventListener('mousedown', setActive);
                    // also expose on the mathField to be safe
                    const origFocus = mathField.focus.bind(mathField);
                    mathField.focus = (...args: any[]) => { setActive(); return origFocus(...args); };

                    // save cleanup function on ref for unmount
                    (mathField as any).__cleanup_setActive = () => {
                        try {
                            containerRef.current?.removeEventListener('mousedown', setActive);
                        } catch (e) {}
                        if (instanceKey) delete (window as any).mathFieldInstances[instanceKey];
                        if ((window as any).currentMathFieldKey === instanceKey) {
                            (window as any).currentMathFieldKey = undefined;
                            (window as any).mathFieldInstance = undefined;
                        }
                    };
                } catch (e) {
                    // swallow
                }
            }
        };

        loadMathQuill();

        return () => {
            try {
                const mf = mathFieldRef.current;
                if (mf && typeof mf.__cleanup_setActive === 'function') mf.__cleanup_setActive();
            } catch (e) {}
        };
    }, []);

    // Método público para insertar LaTeX
    useEffect(() => {
        if (mathFieldRef.current) {
            // Keep previous behavior: if no explicit current instance was set, make this the active one
            (window as any).mathFieldInstance = (window as any).mathFieldInstance || mathFieldRef.current;
        }
    }, [mathFieldRef.current]);

    return (
        <div className="relative w-full text-white">
            <div 
                ref={containerRef}
                className="min-h-[80px] w-full bg-[#2a3b5f]/40 border border-[#4a5f8f]/50 rounded-lg p-4 backdrop-blur-sm focus-within:border-[#7c6fd6] transition-colors"
                style={{ fontSize: '24px' }}
            />
        </div>
    );
}

// Funciones helper para interactuar con el MathField desde fuera
export const insertLatex = (latex: string) => {
    const mathField = (window as any).mathFieldInstance || ((window as any).mathFieldInstances && (window as any).mathFieldInstances[(window as any).currentMathFieldKey]);
    if (mathField) {
        if (latex === 'clear') {
            mathField.latex('');
        } else if (latex === 'backspace') {
            mathField.keystroke('Backspace');
        } else if (latex === 'evaluate') {
            // Aquí puedes agregar lógica de evaluación
            const currentLatex = mathField.latex();
            console.log('Evaluando:', currentLatex);
        } else if (latex === '\\frac') {
            mathField.cmd('\\frac');
        } else if (latex === '\\sqrt') {
            mathField.cmd('\\sqrt');
        } else if (latex === '\\sqrt[n]') {
            mathField.typedText('\\sqrt[]');
            mathField.keystroke('Left');
        } else if (latex === '\\int') {
            mathField.cmd('\\int');
        } else if (latex === '\\sum') {
            mathField.cmd('\\sum');
        } else if (latex === '\\prod') {
            mathField.cmd('\\prod');
        } else if (latex === '\\lim') {
            mathField.cmd('\\lim');
        } else if (latex.startsWith('\\')) {
            // Para comandos de LaTeX
            mathField.cmd(latex);
            mathField.typedText('(');
            mathField.keystroke('Left');
        } else if (latex === '^') {
            mathField.cmd('^');
        } else if (latex === '^2') {
            mathField.typedText('^2');
        } else {
            mathField.write(latex);
        }
        mathField.focus();
    }
};