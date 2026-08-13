// Definición de las teclas del teclado organizadas por categorías

export interface Key {
    label: string;
    latex: string;
    displayType?: 'text' | 'symbol';
}

// Operaciones básicas
export const BASIC_KEYS: Key[] = [
    { label: '7', latex: '7' },
    { label: '8', latex: '8' },
    { label: '9', latex: '9' },
    { label: '÷', latex: '\\div' },
    { label: 'AC', latex: 'clear' },
    { label: '4', latex: '4' },
    { label: '5', latex: '5' },
    { label: '6', latex: '6' },
    { label: '×', latex: '\\times' },
    { label: '⌫', latex: 'backspace' },
    { label: '1', latex: '1' },
    { label: '2', latex: '2' },
    { label: '3', latex: '3' },
    { label: '−', latex: '-' },
    { label: '(', latex: '(' },
    { label: '0', latex: '0' },
    { label: '.', latex: '.' },
    { label: '=', latex: 'evaluate' },
    { label: '+', latex: '+' },
    { label: ')', latex: ')' },
];

// Funciones matemáticas
export const FUNCTION_KEYS: Key[] = [
    { label: 'x²', latex: '^2' },
    { label: 'xⁿ', latex: '^' },
    { label: '√', latex: '\\sqrt' },
    { label: 'ⁿ√', latex: '\\sqrt[n]' },
    { label: '|x|', latex: '\\left|\\right|' },
    { label: 'log', latex: '\\log' },
    { label: 'ln', latex: '\\ln' },
    { label: 'eˣ', latex: 'e^' },
    { label: '10ˣ', latex: '10^' },
    { label: 'π', latex: '\\pi' },
    { label: 'e', latex: 'e' },
    { label: 'x!', latex: '!' },
    { label: 'x/y', latex: '\\frac' },
    { label: '%', latex: '\\%' },
];

// Trigonometría
export const TRIG_KEYS: Key[] = [
    { label: 'sin', latex: '\\sin' },
    { label: 'cos', latex: '\\cos' },
    { label: 'tan', latex: '\\tan' },
    { label: 'sin⁻¹', latex: '\\arcsin' },
    { label: 'cos⁻¹', latex: '\\arccos' },
    { label: 'tan⁻¹', latex: '\\arctan' },
    { label: 'sinh', latex: '\\sinh' },
    { label: 'cosh', latex: '\\cosh' },
    { label: 'tanh', latex: '\\tanh' },
    { label: 'csc', latex: '\\csc' },
    { label: 'sec', latex: '\\sec' },
    { label: 'cot', latex: '\\cot' },
];

// Cálculo (integrales, derivadas, sumatorias)
export const CALCULUS_KEYS: Key[] = [
    { label: '∫', latex: '\\int' },
    { label: '∫ᵇₐ', latex: '\\int_a^b' },
    { label: '∬', latex: '\\iint' },
    { label: 'd/dx', latex: '\\frac{d}{dx}' },
    { label: '∂/∂x', latex: '\\frac{\\partial}{\\partial x}' },
    { label: '∑', latex: '\\sum' },
    { label: '∑ⁿᵢ', latex: '\\sum_{i=1}^{n}' },
    { label: '∏', latex: '\\prod' },
    { label: 'lim', latex: '\\lim' },
    { label: '∞', latex: '\\infty' },
    { label: '∇', latex: '\\nabla' },
];

export type KeyCategory = 'basicas' | 'funciones' | 'trigonometria' | 'calculos';

export const KEY_CATEGORIES: Record<KeyCategory, Key[]> = {
    basicas: BASIC_KEYS,
    funciones: FUNCTION_KEYS,
    trigonometria: TRIG_KEYS,
    calculos: CALCULUS_KEYS,
};
