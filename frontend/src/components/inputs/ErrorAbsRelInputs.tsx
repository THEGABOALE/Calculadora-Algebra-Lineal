import React, { useState } from 'react';
import { Button } from '../ui/button';
import { errorAbsRel } from '../../api/client';

type ApiResponse = {
  input?: { true_value_pretty?: string; approx_value_pretty?: string };
  absolute_error?: {
    operation?: { numerator?: string };
    formula?: { numerator?: string };
    result?: string;
  };
  relative_error?: {
    operation?: { numerator?: string; denominator?: string };
    formula?: { numerator?: string; denominator?: string };
    result?: string;
  };
};

interface Props {
  onCalculate?: (data: { m: number | null; mTilde: number | null; decimalesBase: number | null }) => void;
}

export function ErrorAbsRelInputs({ onCalculate }: Props) {
  const [m, setM] = useState<string>('');
  const [mTilde, setMTilde] = useState<string>('');
  const [decimalesBase, setDecimalesBase] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [result, setResult] = useState<ApiResponse | null>(null);

  function handleSubmit(e?: React.FormEvent) {
    if (e) e.preventDefault();
    onCalculate?.({
      m: m === '' ? null : Number(m),
      mTilde: mTilde === '' ? null : Number(mTilde),
      decimalesBase: decimalesBase === '' ? null : Number(decimalesBase),
    });

    fetchResult();
  }

  async function fetchResult() {
    setApiError(null);
    setLoading(true);
    setResult(null);
    try {
      const payload = {
        true_value: m === '' ? '0' : String(m),
        approx_value: mTilde === '' ? '0' : String(mTilde),
        decimals_display: decimalesBase === '' ? undefined : Number(decimalesBase),
      };
      const res = await errorAbsRel(payload);
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
          <div className="text-xs text-white/80 mb-1">Valor verdadero (m)</div>
          <input
            className="w-full bg-white/3 rounded p-2 text-sm"
            value={m}
            onChange={(e) => setM(e.target.value)}
            placeholder="Ej: 3.1415"
            inputMode="decimal"
          />
        </label>

        <label className="block">
          <div className="text-xs text-white/80 mb-1">Valor aproximado (m~)</div>
          <input
            className="w-full bg-white/3 rounded p-2 text-sm"
            value={mTilde}
            onChange={(e) => setMTilde(e.target.value)}
            placeholder="Ej: 3.14"
            inputMode="decimal"
          />
        </label>
      </div>

      <label className="block">
        <div className="text-xs text-white/80 mb-1">Decimales base</div>
        <input
          className="w-full bg-white/3 rounded p-2 text-sm"
          value={decimalesBase}
          onChange={(e) => setDecimalesBase(e.target.value)}
          placeholder="Ej: 4"
          inputMode="numeric"
        />
      </label>

      <div className="flex items-center justify-between mb-4">
          <Button
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            onClick={handleSubmit}
          >
            {loading ? 'Calculando...' : 'Calcular'}
          </Button>
      </div>

      {apiError && <div className="text-red-400 text-sm mt-3">{apiError}</div>}

      {result && (
        <div className="mt-4 backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-4 text-sm text-purple-200">
          <div className="text-xl font-semibold text-blue-200 mb-3">Resultados</div>

          {/* Absolute error */}
          <div className="mb-4 text-purple-200">
            <div className="text-xm mb-1 font-medium">Error absoluto</div>
            <div className="text-x mb-1">Fórmula: <code className="px-2 py-1 bg-white/3 rounded">{result.absolute_error?.operation?.numerator ?? ''}</code></div>
            <div className="mb-1">Sustitución: <code className="px-2 py-1 bg-white/3 rounded">{result.absolute_error?.formula?.numerator ?? ''}</code> = <strong className="text-white">{result.absolute_error?.result ?? ''}</strong></div>
          </div>

          {/* Relative error */}
          <div>
            <div className="text-xm mb-1 font-medium">Error relativo</div>
            <div className="text-x mb-2">Fórmula:</div>
            <div className="mb-2">
              <div className="inline-block text-center align-middle">
                <div className="px-3">{result.relative_error?.operation?.numerator ?? ''}</div>
                <div className="border-t border-white/20 mx-auto w-full" style={{ width: '100%' }} />
                <div className="px-3">{result.relative_error?.operation?.denominator ?? ''}</div>
              </div>
            </div>

            <div className="mb-1">Sustitución:</div>
            <div className="mb-2">
              <div className="inline-block text-center align-middle">
                <div className="px-3">{result.relative_error?.formula?.numerator ?? ''}</div>
                <div className="border-t border-white/20 mx-auto" style={{ width: '100%' }} />
                <div className="px-3">{result.relative_error?.formula?.denominator ?? ''}</div>
              </div>
              <span className="ml-3">= <strong className="text-white">{result.relative_error?.result ?? ''}</strong></span>
            </div>
          </div>
        </div>
      )}
    </form>
  );
}

export default ErrorAbsRelInputs;
