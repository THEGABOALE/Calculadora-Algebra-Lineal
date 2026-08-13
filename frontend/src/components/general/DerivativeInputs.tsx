import React from 'react';
import { Button } from '../ui/button';
import { MathInput } from '../keyboard_components/MathInput';
import MathQuillRender from '../math/MathQuillRender';
import { derivativeMethod } from '../../api/client';

export default function DerivativeInputs() {
  const [latex, setLatex] = React.useState('');
  const [variable, setVariable] = React.useState('x');
  const [loading, setLoading] = React.useState(false);
  const [resultLatex, setResultLatex] = React.useState<string | null>(null);

  const handleCompute = async () => {
    setLoading(true);
    setResultLatex(null);
    try {
      const payload: any = { latex };
      const res = await derivativeMethod(payload);
      if (res && res.data && res.data.result && res.data.result.latex) {
        setResultLatex(res.data.result.latex);
      } else {
        setResultLatex('');
      }
    } catch (e: any) {
      console.error(e);
      setResultLatex('');
    } finally {
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
            <label className="text-sm text-gray-400">Variable</label>
            <input className="w-full p-2 rounded bg-white/5 border border-white/10 text-blue-200" value={variable} onChange={(e) => setVariable(e.target.value)} />
          </div>
          <div className="flex items-end">
            <Button onClick={handleCompute} className="bg-gradient-to-r from-blue-600 to-purple-600 w-full">{loading ? 'Calculando...' : 'Derivar'}</Button>
          </div>
        </div>

        <div className="pt-4">
          <div className="text-sm text-gray-300 mb-2">Resultado</div>
          <div className="p-4 bg-white/5 rounded text-blue-200">
            {resultLatex ? (
              <MathQuillRender latex={resultLatex} />
            ) : (
              <div className="text-gray-400">Aquí aparecerá la derivada</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
