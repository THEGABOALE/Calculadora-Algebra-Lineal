import React, { useState } from 'react';
import { Button } from '../ui/button';
import { errorAcumulado } from '../../api/client';

type ApiRow = {
  iteration: number;
  prev_amount_pretty: string;
  interest_real_pretty: string;
  interest_approx_pretty: string;
  amount_real_pretty: string;
  amount_approx_pretty: string;
  difference: number;
  error_accum: number;
  approx_mode?: string;
  approx_operation_text?: string;
}

type ApiResponse = {
  input?: any;
  data?: {
    rows: ApiRow[];
    summary: any;
  }
}

interface Props {
  onCalculate?: (data: {
    montoInicial: number | null;
    iteraciones: number | null;
    modo: 'trunc' | 'round';
    rate: number | null;
    decimalesAproximados: number | null;
    decimalesBase: number | null;
  }) => void;
}

export function ErrorAcumuladoInputs({ onCalculate }: Props) {
  const [montoInicial, setMontoInicial] = useState<string>('');
  const [iteraciones, setIteraciones] = useState<string>('');
  const [modo, setModo] = useState<'trunc' | 'round'>('trunc');
  const [rate, setRate] = useState<string>('');
  const [decimalesAproximados, setDecimalesAproximados] = useState<string>('');
  const [decimalesBase, setDecimalesBase] = useState<string>('');

  function handleSubmit(e?: React.FormEvent) {
    if (e) e.preventDefault();
    const payload = {
      initial_amount: montoInicial === '' ? '0' : String(montoInicial),
      iterations: iteraciones === '' ? 0 : Number(iteraciones),
      mode: modo,
      rate: rate === '' ? '0' : String(rate),
      approx_decimals: decimalesAproximados === '' ? 0 : Number(decimalesAproximados),
      interest_display_decimals: decimalesBase === '' ? undefined : Number(decimalesBase),
    };
    onCalculate?.({
      montoInicial: payload.initial_amount === '' ? null : Number(payload.initial_amount),
      iteraciones: payload.iterations,
      modo: payload.mode,
      rate: payload.rate === '' ? null : Number(payload.rate),
      decimalesAproximados: payload.approx_decimals,
      decimalesBase: payload.interest_display_decimals ?? null,
    });

    fetchTable(payload);
  }

  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [result, setResult] = useState<ApiResponse | null>(null);

  async function fetchTable(payload: any) {
    setApiError(null);
    setLoading(true);
    setResult(null);
    try {
      const res = await errorAcumulado(payload);
      setResult(res as ApiResponse);
    } catch (err: any) {
      console.error(err);
      setApiError(err?.message || 'Error en la petición');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <label className="block">
          <div className="text-xs text-white/80 mb-1">Monto inicial</div>
          <input
            className="w-full bg-white/3 rounded p-2 text-sm"
            value={montoInicial}
            onChange={(e) => setMontoInicial(e.target.value)}
            placeholder="Ej: 1000"
            inputMode="decimal"
          />
        </label>

        <label className="block">
          <div className="text-xs text-white/80 mb-1">Iteraciones</div>
          <input
            className="w-full bg-white/3 rounded p-2 text-sm"
            value={iteraciones}
            onChange={(e) => setIteraciones(e.target.value)}
            placeholder="Ej: 5"
            inputMode="numeric"
          />
        </label>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <label className="block">
          <div className="text-xs text-white/80 mb-1">Modo</div>
          <select
            className="w-full bg-white/3 rounded p-2 text-sm"
            value={modo}
            onChange={(e) => setModo(e.target.value as 'trunc' | 'round')}
          >
            <option value="trunc">trunc</option>
            <option value="round">round</option>
          </select>
        </label>

        <label className="block">
          <div className="text-xs text-white/80 mb-1">Rate</div>
          <input
            className="w-full bg-white/3 rounded p-2 text-sm"
            value={rate}
            onChange={(e) => setRate(e.target.value)}
            placeholder="Ej: 0.05"
            inputMode="decimal"
          />
        </label>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <label className="block">
          <div className="text-xs text-white/80 mb-1">Decimales aproximados</div>
          <input
            className="w-full bg-white/3 rounded p-2 text-sm"
            value={decimalesAproximados}
            onChange={(e) => setDecimalesAproximados(e.target.value)}
            placeholder="Ej: 3"
            inputMode="numeric"
          />
        </label>

        <label className="block">
          <div className="text-xs text-white/80 mb-1">Decimales base</div>
          <input
            className="w-full bg-white/3 rounded p-2 text-sm"
            value={decimalesBase}
            onChange={(e) => setDecimalesBase(e.target.value)}
            placeholder="Ej: 5"
            inputMode="numeric"
          />
        </label>
      </div>

      <div className="flex items-center justify-between mb-4">
          <Button
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            onClick={handleSubmit}
          >
            {loading ? 'Calculando...' : 'Calcular'}
          </Button>
      </div>

      {/* Result table */}
      {apiError && <div className="text-red-400 text-sm mt-3">{apiError}</div>}

      {result?.data && (
        <div className="mt-6 backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-4">
          <div className="text-sm font-semibold text-blue-200 mb-3">Resultados</div>
          <div className="overflow-auto">
            <table className="w-full table-auto text-sm">
              <thead>
                <tr className="text-left text-xs text-white/80">
                  <th className="px-3 py-2">Iteración</th>
                  <th className="px-3 py-2">Monto anterior</th>
                  <th className="px-3 py-2">Interés real</th>
                  <th className="px-3 py-2">Interés {modo === 'trunc' ? 'truncado' : 'redondeado'}</th>
                  <th className="px-3 py-2">Monto real</th>
                  <th className="px-3 py-2">Monto {modo === 'trunc' ? 'truncado' : 'redondeado'}</th>
                  <th className="px-3 py-2">Diferencia</th>
                  <th className="px-3 py-2">Error acumulado</th>
                </tr>
              </thead>
              <tbody>
                {result.data.rows.map((r) => (
                  <tr key={r.iteration} className="odd:bg-white/3 even:bg-white/5 text-purple-200">
                    <td className="px-3 py-2">{r.iteration}</td>
                    <td className="px-3 py-2">{r.prev_amount_pretty}</td>
                    <td className="px-3 py-2">{r.interest_real_pretty}</td>
                    <td className="px-3 py-2">{r.interest_approx_pretty}</td>
                    <td className="px-3 py-2">{r.amount_real_pretty}</td>
                    <td className="px-3 py-2">{r.amount_approx_pretty}</td>
                    <td className="px-3 py-2">{r.difference}</td>
                    <td className="px-3 py-2">{r.error_accum}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Summary */}
          {result.data.summary && (
            <div className="mt-4 text-sm text-purple-100">
              <div><strong>Iteraciones:</strong> {result.data.summary.iterations}</div>
              <div><strong>Monto inicial:</strong> {result.data.summary.initial_amout_pretty ?? result.input?.initial_amount}</div>
              <div><strong>Error acumulado final:</strong> {result.data.summary.final_error_accum_pretty}</div>
              <div><strong>Rate:</strong> {result.data.summary.rate}</div>
              <div><strong>Modo:</strong> {result.data.summary.mode}</div>
            </div>
          )}
        </div>
      )}
    </form>
  );
}

export default ErrorAcumuladoInputs;
