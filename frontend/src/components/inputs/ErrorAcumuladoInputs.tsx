import React, { useState } from 'react';
import { Button } from '../ui/button';
import { errorAcumulado } from '../../api/client';

// Los valores numéricos llegan como texto decimal: el backend calcula con
// Decimal y pasarlos por number perdería justamente la precisión que se mide.
// *_pretty ya viene formateado (con "≈" si está redondeado para mostrarse).
type ApiRow = {
  iteration: number;
  prev_amount_pretty: string;
  prev_amount_real_pretty?: string;
  prev_amount_approx_pretty?: string;
  interest_real_pretty: string;
  interest_approx_pretty: string;
  amount_real_pretty: string;
  amount_approx_pretty: string;
  difference: string;
  difference_pretty?: string;
  error_accum: string;
  error_accum_pretty?: string;
  approx_mode?: string;
  approx_operation_text?: string;
}

type ApiSummary = {
  iterations?: number;
  initial_amount_pretty?: string;
  initial_amout_pretty?: string;
  final_amount_real_pretty?: string;
  final_amount_approx_pretty?: string;
  final_error_accum_pretty?: string;
  rate?: string;
  rate_percent?: string;
  mode?: 'trunc' | 'round';
  approx_operation_text?: string;
}

type ApiResponse = {
  input?: { initial_amount?: string; mode?: 'trunc' | 'round'; rate?: string };
  data?: {
    rows: ApiRow[];
    summary?: ApiSummary;
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

// El backend responde {"error": {"code", "message"}}; message es un texto o,
// en errores de validación, un objeto campo -> lista de mensajes. Se muestran
// esos mensajes en vez del genérico "Request failed with status code 400".
function mensajeDeError(err: any): string {
  const message = err?.response?.data?.error?.message;
  if (typeof message === 'string' && message) return message;
  if (message && typeof message === 'object') {
    const textos = Object.values(message).flat().map(String).filter(Boolean);
    if (textos.length) return textos.join(' ');
  }
  return err?.message || 'Error en la petición';
}

// Campo vacío -> undefined (el backend lo rechaza con un mensaje), nunca 0.
function entero(valor: string): number | undefined {
  return valor.trim() === '' ? undefined : Number(valor);
}

function numeroONulo(valor: string): number | null {
  return valor.trim() === '' ? null : Number(valor);
}

export function ErrorAcumuladoInputs({ onCalculate }: Props) {
  const [montoInicial, setMontoInicial] = useState<string>('');
  const [iteraciones, setIteraciones] = useState<string>('');
  const [modo, setModo] = useState<'trunc' | 'round'>('trunc');
  const [rate, setRate] = useState<string>('');
  const [decimalesAproximados, setDecimalesAproximados] = useState<string>('');
  const [decimalesBase, setDecimalesBase] = useState<string>('');

  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [result, setResult] = useState<ApiResponse | null>(null);

  // Un solo disparador: el submit del formulario (botón type="submit" o
  // Enter). Mientras hay una petición en curso no se envía otra.
  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (loading) return;
    onCalculate?.({
      montoInicial: numeroONulo(montoInicial),
      iteraciones: numeroONulo(iteraciones),
      modo,
      rate: numeroONulo(rate),
      decimalesAproximados: numeroONulo(decimalesAproximados),
      decimalesBase: numeroONulo(decimalesBase),
    });
    fetchTable({
      initial_amount: montoInicial.trim(),
      iterations: entero(iteraciones),
      mode: modo,
      rate: rate.trim(),
      approx_decimals: entero(decimalesAproximados),
      interest_display_decimals: entero(decimalesBase),
    });
  }

  async function fetchTable(payload: Parameters<typeof errorAcumulado>[0]) {
    setApiError(null);
    setLoading(true);
    setResult(null);
    try {
      const res = await errorAcumulado(payload);
      setResult(res as ApiResponse);
    } catch (err: any) {
      console.error(err);
      setApiError(mensajeDeError(err));
    } finally {
      setLoading(false);
    }
  }

  // Encabezados según el modo con el que se CALCULÓ la tabla, no el que esté
  // seleccionado ahora en el formulario.
  const modoCalculado = result?.input?.mode ?? modo;
  const aprox = modoCalculado === 'trunc' ? 'truncado' : 'redondeado';
  const summary = result?.data?.summary;

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
          <div className="text-xs text-white/80 mb-1">Iteraciones (períodos)</div>
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
          <div className="text-xs text-white/80 mb-1">Aproximación del interés</div>
          <select
            className="w-full bg-white/3 rounded p-2 text-sm"
            value={modo}
            onChange={(e) => setModo(e.target.value as 'trunc' | 'round')}
          >
            <option value="trunc">Truncar</option>
            <option value="round">Redondear</option>
          </select>
        </label>

        <label className="block">
          <div className="text-xs text-white/80 mb-1">Tasa por período (decimal: 0.05 = 5 %)</div>
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
          <div className="text-xs text-white/80 mb-1">Decimales de la aproximación</div>
          <input
            className="w-full bg-white/3 rounded p-2 text-sm"
            value={decimalesAproximados}
            onChange={(e) => setDecimalesAproximados(e.target.value)}
            placeholder="Ej: 2"
            inputMode="numeric"
          />
        </label>

        <label className="block">
          <div className="text-xs text-white/80 mb-1">Decimales para mostrar (opcional, 4 por defecto)</div>
          <input
            className="w-full bg-white/3 rounded p-2 text-sm"
            value={decimalesBase}
            onChange={(e) => setDecimalesBase(e.target.value)}
            placeholder="Ej: 4"
            inputMode="numeric"
          />
        </label>
      </div>

      <div className="flex items-center justify-between mb-4">
          <Button
            type="submit"
            disabled={loading}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
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
                  <th className="px-3 py-2">Monto anterior real</th>
                  <th className="px-3 py-2">Monto anterior {aprox}</th>
                  <th className="px-3 py-2">Interés real</th>
                  <th className="px-3 py-2">Interés {aprox}</th>
                  <th className="px-3 py-2">Monto real</th>
                  <th className="px-3 py-2">Monto {aprox}</th>
                  <th className="px-3 py-2" title="Interés real − interés aproximado de esta iteración">Diferencia de la iteración</th>
                  <th className="px-3 py-2" title="Monto real − monto aproximado">Error acumulado</th>
                </tr>
              </thead>
              <tbody>
                {result.data.rows.map((r) => (
                  <tr key={r.iteration} className="odd:bg-white/3 even:bg-white/5 text-purple-200">
                    <td className="px-3 py-2">{r.iteration}</td>
                    <td className="px-3 py-2">{r.prev_amount_real_pretty ?? r.prev_amount_pretty}</td>
                    <td className="px-3 py-2">{r.prev_amount_approx_pretty ?? r.prev_amount_pretty}</td>
                    <td className="px-3 py-2">{r.interest_real_pretty}</td>
                    <td className="px-3 py-2">{r.interest_approx_pretty}</td>
                    <td className="px-3 py-2">{r.amount_real_pretty}</td>
                    <td className="px-3 py-2">{r.amount_approx_pretty}</td>
                    <td className="px-3 py-2">{r.difference_pretty ?? r.difference}</td>
                    <td className="px-3 py-2">{r.error_accum_pretty ?? r.error_accum}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Summary */}
          {summary && (
            <div className="mt-4 text-sm text-purple-100">
              <div><strong>Iteraciones:</strong> {summary.iterations}</div>
              <div><strong>Monto inicial:</strong> {summary.initial_amount_pretty ?? summary.initial_amout_pretty ?? result.input?.initial_amount}</div>
              {summary.final_amount_real_pretty && <div><strong>Monto final real:</strong> {summary.final_amount_real_pretty}</div>}
              {summary.final_amount_approx_pretty && <div><strong>Monto final {aprox}:</strong> {summary.final_amount_approx_pretty}</div>}
              <div><strong>Error acumulado final:</strong> {summary.final_error_accum_pretty}</div>
              <div><strong>Tasa por período:</strong> {summary.rate_percent ?? summary.rate}</div>
              <div><strong>Aproximación:</strong> {summary.approx_operation_text ?? summary.mode} el interés de cada período</div>
              <div className="mt-2 text-xs text-white/60">
                Error acumulado = monto real − monto {aprox}. Incluye lo que cada aproximación quitó (o agregó) y el interés que esa diferencia dejó de generar (o generó de más) en los períodos siguientes. Los valores con ≈ están redondeados para mostrarse.
              </div>
            </div>
          )}
        </div>
      )}
    </form>
  );
}

export default ErrorAcumuladoInputs;
