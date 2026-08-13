import React from 'react';

type VectorResultPrettyProps = { result: any };

const MatrixTable: React.FC<{ matrix: string[][] }> = ({ matrix }) => {
  const cols = matrix[0]?.length ?? 0;
  const lastCol = Math.max(0, cols - 1);
  return (
    <div className="overflow-auto">
      <table className="border-collapse table-auto text-sm">
        <tbody>
          {matrix.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td
                  key={j}
                  className={`px-3 py-1 border border-white/10 ${j === lastCol ? 'border-l-2 border-white/20' : ''}`}
                >
                  <div className="whitespace-nowrap text-xs text-purple-100">{cell}</div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const renderMatrixObject = (matrixObj: any) => {
  if (!matrixObj) return null;
  const augmented = matrixObj.augmented ?? matrixObj.U ?? matrixObj.RREF ?? null;
  const square = matrixObj.square ?? matrixObj.square_matrix ?? matrixObj.matrix ?? null;
  const extended = matrixObj.extended ?? matrixObj.extended_matrix ?? null;
  const minor = matrixObj.minor ?? matrixObj.submatrix ?? matrixObj.minor_matrix ?? null;

  if (augmented && Array.isArray(augmented)) {
    return <MatrixTable matrix={(augmented as any).map((r: any[]) => r.map((c: any) => String(c)))} />;
  }

  if (square && Array.isArray(square) && Array.isArray(square[0])) {
    return <MatrixTable matrix={square.map((r: any[]) => r.map((c: any) => String(c)))} />;
  }

  if (extended && Array.isArray(extended) && Array.isArray(extended[0])) {
    return <MatrixTable matrix={extended.map((r: any[]) => r.map((c: any) => String(c)))} />;
  }

  if (minor && Array.isArray(minor) && Array.isArray(minor[0])) {
    return <MatrixTable matrix={minor.map((r: any[]) => r.map((c: any) => String(c)))} />;
  }

  if (Array.isArray(matrixObj) && Array.isArray(matrixObj[0])) {
    return <MatrixTable matrix={matrixObj.map((r: any[]) => r.map((c: any) => String(c)))} />;
  }

  return null;
};

const renderVector = (label: string, pretty: string) => (
  <div className="mb-1 text-xs">
    <span className="text-white/70">{label}: </span>
    <span className="text-purple-100">{pretty}</span>
  </div>
);

const renderScalar = (label: string, pretty: string) => (
  <div className="mb-1 text-xs">
    <span className="text-white/70">{label}: </span>
    <span className="text-purple-100">{pretty}</span>
  </div>
);

const renderStepList = (steps: string[]) => (
  <div className="mb-2">
    <div className="text-white/70 text-xs mb-1">Pasos:</div>
    <ul className="list-disc pl-5 text-xs text-purple-100">
      {steps.map((s, i) => <li key={i}>{s}</li>)}
    </ul>
  </div>
);

const renderResultVector = (pretty: string) => (
  <div className="mt-2 text-xs">
    <span className="text-white/70">Resultado: </span>
    <span className="text-purple-100">{pretty}</span>
  </div>
);

const renderResultScalar = (pretty: string) => (
  <div className="mt-2 text-xs">
    <span className="text-white/70">Resultado: </span>
    <span className="text-purple-100">{pretty}</span>
  </div>
);

const renderScalars = (scalars: any) => (
  <div className="mb-1 text-xs">
    {Object.entries(scalars).map(([k, v]: any) => (
      <span key={k} className="mr-3">
        <span className="text-white/70">{k}: </span>
        <span className="text-purple-100">{v.pretty}</span>
      </span>
    ))}
  </div>
);

const renderInputVectors = (vectors: any) => (
  <div className="mb-1">
    {Object.entries(vectors).map(([k, v]: any) => renderVector(k, v.pretty))}
  </div>
);

const renderInputScalars = (scalars: any) => (
  <div className="mb-1">
    {Object.entries(scalars).map(([k, v]: any) => renderScalar(k, v.pretty))}
  </div>
);

const VectorResultPretty: React.FC<VectorResultPrettyProps> = ({ result }) => {
  if (!result) return null;

  // Detect operation type
  const op = result.input?.operation ?? result.operation ?? null;

  // Suma y resta
  if (op === 'add' || op === 'sub') {
    return (
      <div className="space-y-2">
        <div className="text-sm font-semibold text-blue-200 mb-2">Operación: {op === 'add' ? 'Suma de vectores' : 'Resta de vectores'}</div>
        {renderInputVectors(result.input.vectors)}
        {renderStepList(result.steps)}
        {renderResultVector(result.result.vector_pretty)}
      </div>
    );
  }

  // Producto escalar
  if (op === 'dot') {
    return (
      <div className="space-y-2">
        <div className="text-sm font-semibold text-blue-200 mb-2">Operación: Producto escalar</div>
        {renderInputVectors(result.input.vectors)}
        {renderStepList(result.steps)}
        {renderResultScalar(result.result.scalar_pretty)}
      </div>
    );
  }

  // Multiplicación escalar
  if (op === 'escalar') {
    return (
      <div className="space-y-2">
        <div className="text-sm font-semibold text-blue-200 mb-2">Operación: Multiplicación escalar</div>
        {renderInputVectors(result.input.vectors)}
        {renderInputScalars(result.input.scalars)}
        {renderStepList(result.steps)}
        {renderResultVector(result.result.vector_pretty)}
      </div>
    );
  }

  // Combinación lineal 2 vectores
  if (op === 'comb2') {
    return (
      <div className="space-y-2">
        <div className="text-sm font-semibold text-blue-200 mb-2">Operación: Combinación lineal (2 vectores)</div>
        {renderInputVectors(result.input.vectors)}
        {renderInputScalars(result.input.scalars)}
        {renderStepList(result.steps)}
        {renderResultVector(result.result.vector_pretty)}
      </div>
    );
  }

  // Combinación lineal 3 vectores
  if (op === 'comb3') {
    return (
      <div className="space-y-2">
        <div className="text-sm font-semibold text-blue-200 mb-2">Operación: Combinación lineal (3 vectores)</div>
        {renderInputVectors(result.input.vectors)}
        {renderInputScalars(result.input.scalars)}
        {renderStepList(result.steps)}
        {renderResultVector(result.result.vector_pretty)}
      </div>
    );
  }

  // Combinación lineal Ax = b
  if (result.input?.A && result.input?.b && result.gauss_jordan && result.check && result.result) {
    return (
      <div className="space-y-2">
        <div className="text-sm font-semibold text-blue-200 mb-2">Operación: Combinación lineal Ax = b</div>
        {/* Gauss-Jordan steps (if provided) */}
        {result.gauss_jordan?.steps && Array.isArray(result.gauss_jordan.steps) && (
          <div>
            <div className="text-sm font-semibold text-blue-200 mb-2">Pasos (Gauss-Jordan)</div>
            <div className="space-y-3">
              {result.gauss_jordan.steps.map((s:any, i:number) => (
                <div key={i} className="mb-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-sm font-semibold text-blue-200">{s.operation ?? s.op ?? `Paso ${i}`}</div>
                    {s.tag && <div className="text-xs text-white/60 px-2 py-1 rounded bg-white/3">{s.tag}</div>}
                  </div>
                  <div className="p-3 bg-gradient-to-br from-white/3 to-white/2 rounded-lg border border-white/10">
                    {s.matrix ? renderMatrixObject(s.matrix) : <div className="text-xs text-purple-100">{s.operation ?? JSON.stringify(s)}</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        <div className="mb-1 text-xs">
          <span className="text-white/70">Ax: </span>
          <span className="text-purple-100">[{result.check.Ax_pretty?.join(', ')}]</span>
        </div>
        <div className="mb-1 text-xs">
          <span className="text-white/70">b: </span>
          <span className="text-purple-100">[{result.check.b_pretty?.join(', ')}]</span>
        </div>
        <div className="mb-1 text-xs">
          <span className="text-white/70">Verificación: </span>
          <span className="text-purple-100">{result.check.ok ? 'Ax = b' : 'Ax ≠ b'}</span>
        </div>
        <div className="mb-1 text-xs">
          <span className="text-white/70">Tipo de solución: </span>
          <span className="text-purple-100">{result.result.solution_type}</span>
        </div>
        <div className="mb-1 text-xs">
          <span className="text-white/70">Coeficientes particulares: </span>
          <span className="text-purple-100">[{result.result.coefficients_particular_pretty?.join(', ')}]</span>
        </div>
        <div className="mb-1 text-xs">
          <span className="text-white/70">Combinación lineal: </span>
          <span className="text-purple-100">{result.result.columns_statement}</span>
        </div>
      </div>
    );
  }

  // Fallback
  return <pre className="text-xs text-purple-100">{JSON.stringify(result, null, 2)}</pre>;
};

export default VectorResultPretty;
