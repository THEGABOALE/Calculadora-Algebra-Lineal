import React from 'react';
import { Button } from '../ui/button';
import { MathInput } from '../keyboard_components/MathInput';
import MathQuillRender from '../math/MathQuillRender';
import { derivativeMethod } from '../../api/client';

// El backend responde {"error": {"code", "message"}}; message es un texto o,
// en errores de validación del formulario, un objeto campo -> lista de
// mensajes. Se muestran esos mensajes en vez del genérico de Axios.
function mensajeDeError(err: any): string {
  const message = err?.response?.data?.error?.message;
  if (typeof message === 'string' && message) return message;
  if (message && typeof message === 'object') {
    const textos = Object.values(message).flat().map(String).filter(Boolean);
    if (textos.length) return textos.join(' ');
  }
  return err?.message || 'Error en la petición';
}

export default function DerivativeInputs() {
  const [latex, setLatex] = React.useState('');
  const [variable, setVariable] = React.useState('x');
  const [loading, setLoading] = React.useState(false);
  const [resultLatex, setResultLatex] = React.useState<string | null>(null);
  const [interpretedLatex, setInterpretedLatex] = React.useState<string | null>(null);
  const [resultVariable, setResultVariable] = React.useState('x');
  const [apiError, setApiError] = React.useState<string | null>(null);
  // Bloqueo inmediato: el estado `loading` recién se ve en el siguiente
  // render, así que dos clics seguidos podrían pasar los dos sin esto.
  const enCurso = React.useRef(false);

  const handleCompute = async () => {
    if (enCurso.current) return; // sin solicitudes duplicadas mientras hay una en curso
    enCurso.current = true;
    setLoading(true);
    setResultLatex(null);
    setInterpretedLatex(null);
    setApiError(null);
    try {
      const res = await derivativeMethod({ latex, variable: variable.trim() });
      const data = res?.data;
      // "0" es un resultado válido (derivada de una constante): se compara
      // con string, no por truthiness.
      if (typeof data?.result?.latex === 'string') {
        setResultLatex(data.result.latex);
        setInterpretedLatex(data.input?.interpreted_latex ?? null);
        setResultVariable(data.input?.variable ?? variable.trim());
      } else {
        setApiError('La respuesta del servidor no trae la derivada.');
      }
    } catch (e: any) {
      console.error(e);
      setApiError(mensajeDeError(e));
    } finally {
      enCurso.current = false;
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#1e2b4a]/60 rounded-2xl p-6 border border-[#4a5f8f]/30 backdrop-blur-sm shadow-2xl w-full">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-300 font-semibold">Derivadas</div>
        </div>

        <label className="text-sm text-gray-400">Ingresa expresión (LaTeX)</label>
        <MathInput onLatexChange={setLatex} initialLatex={latex} instanceKey="derivative_input" />

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-sm text-gray-400">Variable de derivación (una letra, p. ej. x o t)</label>
            <input
              className="w-full p-2 rounded bg-white/5 border border-white/10 text-blue-200"
              value={variable}
              maxLength={1}
              onChange={(e) => setVariable(e.target.value)}
            />
          </div>
          <div className="flex items-end">
            <Button onClick={handleCompute} disabled={loading} className="bg-gradient-to-r from-blue-600 to-purple-600 w-full">{loading ? 'Calculando...' : 'Derivar'}</Button>
          </div>
        </div>

        {apiError && <div className="text-red-400 text-sm">{apiError}</div>}

        <div className="pt-4">
          <div className="text-sm text-gray-300 mb-2">Resultado</div>
          <div className="p-4 bg-white/5 rounded text-blue-200 space-y-2">
            {resultLatex !== null ? (
              <>
                {interpretedLatex && (
                  <div className="text-xs text-gray-400 flex items-center gap-2">
                    <span>f({resultVariable}) =</span>
                    <MathQuillRender latex={interpretedLatex} />
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-300">f′({resultVariable}) =</span>
                  <MathQuillRender latex={resultLatex} />
                </div>
              </>
            ) : (
              <div className="text-gray-400">Aquí aparecerá la derivada</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
