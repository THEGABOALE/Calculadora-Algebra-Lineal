import React from 'react';
import { Button } from '../ui/button';
import { MathInput } from '../keyboard_components/MathInput';
import MathQuillRender from '../math/MathQuillRender';
import { integralMethod } from '../../api/client';

// El backend responde {"error": {"code", "message"}}; message es un texto o,
// en errores de validación del formulario, un objeto campo -> lista de
// mensajes. Se muestran esos mensajes en vez del genérico de Axios: 400 es
// una entrada inválida, 422 una integral que no se pudo resolver (o que
// superó el tiempo máximo) y 503 un servidor ocupado.
function mensajeDeError(err: any): string {
  const message = err?.response?.data?.error?.message;
  if (typeof message === 'string' && message) return message;
  if (message && typeof message === 'object') {
    const textos = Object.values(message).flat().map(String).filter(Boolean);
    if (textos.length) return textos.join(' ');
  }
  if (err?.code === 'ECONNABORTED') return 'El servidor tardó demasiado en responder.';
  return err?.message || 'Error en la petición';
}

type Resultado = {
  latex: string;
  interpretedLatex: string | null;
  variable: string;
  note: string | null;
  definitions: Record<string, string>;
};

export default function IntegralInputs() {
  const [latex, setLatex] = React.useState('');
  const [variable, setVariable] = React.useState('x');
  const [loading, setLoading] = React.useState(false);
  const [resultado, setResultado] = React.useState<Resultado | null>(null);
  const [apiError, setApiError] = React.useState<string | null>(null);
  // Bloqueo inmediato: el estado `loading` recién se ve en el siguiente
  // render, así que dos clics seguidos podrían pasar los dos sin esto.
  const enCurso = React.useRef(false);

  const handleCompute = async () => {
    if (enCurso.current) return;
    enCurso.current = true;
    setLoading(true);
    setResultado(null);
    setApiError(null);
    try {
      const res = await integralMethod({ latex, variable: variable.trim() });
      const data = res?.data;
      if (typeof data?.result?.latex === 'string') {
        setResultado({
          latex: data.result.latex,
          interpretedLatex: data.input?.interpreted_latex ?? null,
          variable: data.input?.variable ?? variable.trim(),
          note: data.result.note ?? null,
          definitions: data.result.definitions ?? {},
        });
      } else {
        setApiError('La respuesta del servidor no trae la integral.');
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
          <div className="text-sm text-gray-300 font-semibold">Integrales</div>
        </div>

        <label className="text-sm text-gray-400">Ingresa expresión (LaTeX)</label>
        <MathInput onLatexChange={setLatex} initialLatex={latex} instanceKey="integral_input" />

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-sm text-gray-400">Variable de integración (una letra, p. ej. x o t)</label>
            <input
              className="w-full p-2 rounded bg-white/5 border border-white/10 text-blue-200"
              value={variable}
              maxLength={1}
              onChange={(e) => setVariable(e.target.value)}
            />
          </div>
          <div className="flex items-end">
            <Button onClick={handleCompute} disabled={loading} className="bg-gradient-to-r from-blue-600 to-purple-600 w-full">{loading ? 'Calculando...' : 'Integrar'}</Button>
          </div>
        </div>

        {loading && <div className="text-xs text-gray-400">Calculando la primitiva (puede tardar unos segundos)…</div>}
        {apiError && <div className="text-red-400 text-sm">{apiError}</div>}

        <div className="pt-4">
          <div className="text-sm text-gray-300 mb-2">Resultado</div>
          <div className="p-4 bg-white/5 rounded text-blue-200 space-y-2">
            {resultado ? (
              <>
                {resultado.interpretedLatex && (
                  <div className="text-xs text-gray-400 flex items-center gap-2">
                    <span>f({resultado.variable}) =</span>
                    <MathQuillRender latex={resultado.interpretedLatex} />
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-300">∫ f({resultado.variable}) d{resultado.variable} =</span>
                  <MathQuillRender latex={resultado.latex} />
                </div>
                {resultado.note && <div className="text-xs text-amber-200">{resultado.note}</div>}
                {Object.entries(resultado.definitions).map(([nombre, definicion]) => (
                  <div key={nombre} className="text-xs text-gray-400">
                    <MathQuillRender latex={definicion} />
                  </div>
                ))}
              </>
            ) : (
              <div className="text-gray-400">Aquí aparecerá la integral</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
