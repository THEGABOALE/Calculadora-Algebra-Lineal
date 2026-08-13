import React from 'react';
import { Button } from '../ui/button';
import { MathInput } from '../keyboard_components/MathInput';
import { Keyboard } from '../keyboard_components/Keyboard';
import { newtonRaphsonMethod } from '../../api/client';
import BlockMath from '../math/BlockMath';
import { Dialog, DialogTrigger, DialogContent, DialogTitle, DialogDescription, DialogFooter } from '../ui/dialog';

export function NewtonRaphsonInputs() {
  const [funcLatex, setFuncLatex] = React.useState('');
  const [x0, setX0] = React.useState<string>('');
  const [tol, setTol] = React.useState<string>('0.0001');
  const [maxIter, setMaxIter] = React.useState<string>('');
  const [derMode, setDerMode] = React.useState<string>('symbolic');
  const [loading, setLoading] = React.useState(false);
  const [result, setResult] = React.useState<any>(null);

  const handleCalculate = async () => {
    setLoading(true);
    setResult(null);
    try {
      const payload: any = {
        function_latex: funcLatex || '\\,',
        x0: parseFloat(x0),
        tolerance: parseFloat(tol),
        derivate_mode: derMode,
      };
      if (maxIter) payload.max_iterations = parseInt(maxIter, 10);

      const res = await newtonRaphsonMethod(payload);
      setResult(res?.data ?? res);
    } catch (e: any) {
      console.error(e);
      setResult({ error: e?.message || 'Error en la petición' });
    } finally {
      setLoading(false);
    }
  };

  const fmt = (v: any) => {
    if (v === null || v === undefined) return '-';
    const n = Number(v);
    return Number.isFinite(n) ? n.toFixed(6) : String(v);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div className="space-y-4">
        <label className="text-sm text-blue-200">f(x)</label>
        <MathInput instanceKey="newton_func" onLatexChange={setFuncLatex} initialLatex={funcLatex} />

        <div>
          <label className="text-sm text-blue-200">Punto inicial (x0)</label>
          <input className="w-full p-2 rounded bg-white/5 border border-white/10 text-blue-200" value={x0} onChange={(e) => setX0(e.target.value)} placeholder="0.0" />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-sm text-blue-200">Tolerancia</label>
            <input className="w-full p-2 rounded bg-white/5 border border-white/10 text-blue-200" value={tol} onChange={(e) => setTol(e.target.value)} />
          </div>
          <div>
            <label className="text-sm text-blue-200">Máximo iteraciones (opcional)</label>
            <input className="w-full p-2 rounded bg-white/5 border border-white/10 text-blue-200" value={maxIter} onChange={(e) => setMaxIter(e.target.value)} />
          </div>
        </div>

        <div>
          <label className="text-sm text-blue-200">Modo derivada</label>
          <select value={derMode} onChange={(e) => setDerMode(e.target.value)} className="w-full p-2 rounded bg-white/5 border border-white/10 text-blue-200">
            <option value="symbolic">symbolic</option>
          </select>
        </div>

        <div>
          <Button onClick={handleCalculate} className="bg-gradient-to-r from-blue-600 to-purple-600">{loading ? 'Calculando...' : 'Calcular'}</Button>
        </div>
      </div>

      <div className="space-y-4">
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-4">
          {result ? (
            result.error ? (
              <div className="text-red-400">{result.error}</div>
            ) : (
              <div>
                <div className="text-sm text-purple-300 mb-2">Tabla de iteraciones</div>
                <div className="overflow-auto max-h-72">
                  <table className="w-full text-sm table-auto border-collapse">
                    <thead>
                      <tr className="text-left text-xs text-gray-300">
                        <th className="p-2">iter</th>
                        <th className="p-2">x<sub>i</sub></th>
                        <th className="p-2">f(x<sub>i</sub>)</th>
                        <th className="p-2">f'(x<sub>i</sub>)</th>
                        <th className="p-2">x<sub>i+1</sub></th>
                        <th className="p-2">E<sub>a</sub></th>
                        <th className="p-2">E<sub>a</sub>&lt;E</th> 
                      </tr>
                    </thead>
                    <tbody>
                      {(result.table || []).map((row: any) => (
                        <tr key={row.iteration} className="odd:bg-white/3 even:bg-white/5 text-blue-200">
                          <td className="p-2">{row.iteration}</td>
                          <td className="p-2">{fmt(row.xk)}</td>
                          <td className="p-2">{fmt(row.fxk)}</td>
                          <td className="p-2">{fmt(row.fprimexk)}</td>
                          <td className="p-2">{fmt(row.x_next)}</td>
                          <td className="p-2">{fmt(row.Ea)}</td>
                          <td className="p-2">{row.Ea_lt_E === null || row.Ea_lt_E === undefined ? '-' : (row.Ea_lt_E ? 'true' : 'false')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-3 flex gap-3">
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button className="bg-gradient-to-r from-blue-600 to-purple-600">Evaluaciones</Button>
                    </DialogTrigger>
                    <DialogContent className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6 w-[min(1200px,96vw)] max-w-6xl max-h-[90vh] mx-auto">
                      <DialogTitle><span className='text-gray-200'>Evaluaciones</span></DialogTitle>
                      <DialogDescription>
                        <div className="mt-2 text-gray-400 pr-2 w-full">
                          <BlockMath className="w-full">{result.iterations_estimate?.latex?.formula_newton}</BlockMath>
                          <BlockMath className="w-full">{result.iterations_estimate?.latex?.formula_error_general}</BlockMath>
                          <BlockMath className="w-full">{result.iterations_estimate?.latex?.formula_error_substitution}</BlockMath>
                          <BlockMath className="w-full">{result.iterations_estimate?.latex?.formula_error_numeric}</BlockMath>
                          <div className="mt-2 text-sm text-gray-300">n_min: {result.iterations_estimate?.latex?.iterations ?? result.iterations_estimate?.numeric?.iterations}</div>
                          <div className="mt-2 text-sm text-gray-300">tolerance: {result.iterations_estimate?.numeric?.tolerance}</div>
                          <div className="mt-1 text-sm text-gray-300">last_error: {result.iterations_estimate?.numeric?.last_error}</div>
                        </div>
                      </DialogDescription>
                      <DialogFooter />
                    </DialogContent>
                  </Dialog>

                  <Dialog>
                    <DialogTrigger asChild>
                      <Button className="bg-gradient-to-r from-blue-600 to-purple-600">Detalles iteraciones</Button>
                    </DialogTrigger>
                    <DialogContent className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6
                                                w-[75vw] max-w-[75vw] sm:max-w-[75vw]
                                                max-h-[80vh] mx-auto overflow-hidden">
                      <DialogTitle><span className='text-gray-300'>Detalles por iteración </span></DialogTitle>
                      <DialogDescription>
                        <div className="space-y-4 mt-2 overflow-auto max-h-[68vh] pr-2">
                          {(result.details || []).map((it: any) => (
                            <div key={it.iteration} className="p-3 bg-white/5 rounded">
                              <div className="font-semibold text-gray-300">Iteración {it.iteration}</div>
                              <div className="mt-2 space-y-1 text-gray-400">
                                {it.lines.map((line: string, idx: number) => (
                                  <BlockMath key={idx} className="w-full">{line}</BlockMath>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </DialogDescription>
                      <DialogFooter />
                    </DialogContent>
                  </Dialog>

                  <Dialog>
                    <DialogTrigger asChild>
                      <Button className="bg-gradient-to-r from-blue-600 to-purple-600">Conclusión</Button>
                    </DialogTrigger>
                    <DialogContent className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6
                                                w-[50vw] max-w-[50vw] sm:max-w-[50vw]
                                                max-h-[80vh] mx-auto overflow-hidden">
                      <DialogTitle><span className='text-gray-200'>Conclusiones</span></DialogTitle>
                      <DialogDescription>
                        <div className="mt-2 text-gray-400 pr-2 w-full">
                          <BlockMath className="w-full">{result.conclusion?.latex}</BlockMath>
                          <div className="mt-2 text-sm text-gray-400">raíz: {result.conclusion?.root} — iteraciones: {result.conclusion?.iterations}</div>
                        </div>
                      </DialogDescription>
                      <DialogFooter />
                    </DialogContent>
                  </Dialog>
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

export default NewtonRaphsonInputs;
