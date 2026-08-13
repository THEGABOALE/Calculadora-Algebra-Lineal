import React from 'react';
import ResultPretty from '../Output/ResultPretty';

type Props = { lastResult: any };

export default function ResultSection({ lastResult }: Props) {
  return (
    <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl text-blue-200">Resultado</h3>
      </div>

      <div className="backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl p-6 min-h-32 flex items-center justify-center">
        <div className="w-full">
          {lastResult ? (
            <div className="text-left">
              <ResultPretty result={lastResult} />
            </div>
          ) : (
            <p className="text-purple-300/50 text-center">No hay resultados aún.</p>
          )}
        </div>
      </div>
    </div>
  );
}
