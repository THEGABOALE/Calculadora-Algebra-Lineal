import React from 'react';
import { Button } from '../ui/button';
import { MathInput } from '../keyboard_components/MathInput';
import { Keyboard } from '../keyboard_components/Keyboard';
import katex from 'katex';
import { errorPropagation } from '../../api/client';

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

export function PropagationErrorInputs() {
  const [functionLatex, setFunctionLatex] = React.useState('');
  const [x0Latex, setX0Latex] = React.useState('');
  const [dxLatex, setDxLatex] = React.useState('');
  const [angleMode, setAngleMode] = React.useState<'rad' | 'deg'>('rad');
  const [loading, setLoading] = React.useState(false);
  const [result, setResult] = React.useState<any>(null);
  // Bloqueo inmediato: `loading` recién se ve en el siguiente render.
  const enCurso = React.useRef(false);

  const handleCalculate = async () => {
    if (enCurso.current) return; // sin solicitudes duplicadas
    enCurso.current = true;
    setLoading(true);
    setResult(null);
    try {
      // Los campos vacíos se envían vacíos: el backend los rechaza con un
      // mensaje, en vez de calcular con un 0 que nadie escribió.
      const payload = {
        function_latex: functionLatex,
        x0: x0Latex,
        delta_x: dxLatex,
        angle_mode: angleMode,
      };
      const res = await errorPropagation(payload);
      setResult(res);
    } catch (e: any) {
      console.error(e);
      setResult({ error: mensajeDeError(e) });
    } finally {
      enCurso.current = false;
      setLoading(false);
    }
  };

  const renderLatex = (tex: string) => {
    try {
      return { __html: katex.renderToString(tex, { throwOnError: false }) };
    } catch (e) {
      return { __html: tex };
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div className="space-y-4">
        <label className="text-sm text-blue-200">Función f(x)</label>
        <MathInput instanceKey="prop_func" onLatexChange={(l) => setFunctionLatex(l)} initialLatex={functionLatex} />

        <label className="text-sm text-blue-200">x₀</label>
        <MathInput instanceKey="prop_x0" onLatexChange={(l) => setX0Latex(l)} initialLatex={x0Latex} />

        <label className="text-sm text-blue-200">Δx</label>
        <MathInput instanceKey="prop_dx" onLatexChange={(l) => setDxLatex(l)} initialLatex={dxLatex} />

        <label className="text-sm text-blue-200">Modo Angular</label>
        <select value={angleMode} onChange={(e) => setAngleMode(e.target.value as any)} className="w-40 p-2 rounded bg-white/5 border border-white/10 text-blue-200">
          <option value="rad">Radianes</option>
          <option value="deg">Grados</option>
        </select>

        <div className="pt-2">
          <Button onClick={handleCalculate} disabled={loading} className="bg-gradient-to-r from-blue-600 to-purple-600">
            {loading ? 'Calculando...' : 'Calcular'}
          </Button>
        </div>
      </div>

      <div className="space-y-4">
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-4 min-h-[200px]">
          {result ? (
            result.error ? (
              <div className="text-red-400">{result.error}</div>
            ) : (
              <div className="space-y-3 text-white">
                <div>
                  <div className="text-sm text-purple-300 mb-1">Entrada</div>
                  <div className="text-sm" dangerouslySetInnerHTML={renderLatex(result.steps?.derivative?.formula?.function || result.input?.function_latex || '')} />
                  <div className="text-xs text-gray-300">
                    x₀ = <span dangerouslySetInnerHTML={renderLatex(result.input?.x0_latex || '')} /> ({result.input?.x0})
                    {' — '}Δx = <span dangerouslySetInnerHTML={renderLatex(result.input?.delta_x_latex || '')} /> ({result.input?.delta_x})
                  </div>
                  <div className="text-xs text-gray-300">
                    Modo angular: {result.input?.angle_mode === 'deg' ? 'grados (x₀ y Δx en grados)' : 'radianes'}
                  </div>
                </div>

                <div>
                  <div className="text-sm text-purple-300 mb-1">Derivada</div>
                  <div className="text-sm" dangerouslySetInnerHTML={renderLatex(result.steps?.derivative?.formula?.derivative || '')} />
                  <div className="text-xs text-gray-300">Evaluación: <span dangerouslySetInnerHTML={renderLatex(result.steps?.derivative?.formula?.evaluation || '')} /></div>
                </div>

                <div>
                  <div className="text-sm text-purple-300 mb-1">Δy aproximado</div>
                  <div className="text-sm" dangerouslySetInnerHTML={renderLatex(result.steps?.approx_delta_y?.formula?.expression || '')} />
                  <div className="text-xs text-gray-300">Resultado: {result.steps?.approx_delta_y?.result}</div>
                </div>

                <div>
                  <div className="text-sm text-purple-300 mb-1">Δy real</div>
                  <div className="text-sm" dangerouslySetInnerHTML={renderLatex(result.steps?.exact_delta_y?.formula?.expression || '')} />
                  <div className="text-xs text-gray-300">Resultado: {result.steps?.exact_delta_y?.result}</div>
                </div>

                <div>
                  <div className="text-sm text-purple-300 mb-1">Error absoluto</div>
                  <div className="text-sm" dangerouslySetInnerHTML={renderLatex(result.steps?.absolute_error?.formula?.numerator || '')} />
                  <div className="text-xs text-gray-300">Resultado: {result.steps?.absolute_error?.result}</div>
                </div>
              </div>
            )
          ) : (
            <div className="text-gray-400">Resultados aparecerán aquí</div>
          )}
        </div>

        <div>
          <Keyboard />
        </div>
      </div>
    </div>
  );
}

export default PropagationErrorInputs;
