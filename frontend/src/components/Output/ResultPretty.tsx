import React from 'react';
import VectorResultPretty from './VectorResultPretty';

type ResultPrettyProps = { result: any };

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

export const ResultPretty: React.FC<ResultPrettyProps> = ({ result }) => {
  if (!result) return null;

  // Detect vector operation types
  const vectorOps = ['add', 'sub', 'dot', 'escalar', 'comb2', 'comb3'];
  const isVectorOp = vectorOps.includes(result.input?.operation ?? result.operation ?? '');
  // Detect linear combination Ax=b
  const isLinearComb = result.input?.A && result.input?.b && result.gauss_jordan && result.check && result.result;
  if (isVectorOp || isLinearComb) {
    return <VectorResultPretty result={result} />;
  }

  // steps can be either an array of step objects/strings (legacy) or an
  // object for complex operations like inverse: { frame: { ... }, text_steps: [...] }
  const rawSteps = result.steps;
  const stepsArray = Array.isArray(rawSteps) ? rawSteps : (rawSteps?.text_steps ?? []);
  const frame = rawSteps && !Array.isArray(rawSteps) ? rawSteps.frame ?? null : null;
  const summary = result.summary ?? result.result?.summary ?? null;

  // render a single textual step (string) optionally aligned with a matrix snapshot
  const renderTextStepWithMatrix = (text: string, idx: number) => {
    // try to find an aligned matrix snapshot: prefer frame.step_states, fall back to frame.states
    const snap = frame?.step_states?.[idx] ?? frame?.states?.[idx] ?? null;
    const matrix = snap?.matrix ?? null;
    return (
      <div key={idx} className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="text-sm font-semibold text-blue-200">{text}</div>
          {snap?.tag && <div className="text-xs text-white/60 px-2 py-1 rounded bg-white/3">{snap.tag}</div>}
        </div>

        <div className="p-3 bg-gradient-to-br from-white/3 to-white/2 rounded-lg border border-white/10">
          {matrix ? (
            // matrix may be an augmented matrix (numbers) or an object with 'augmented' etc.
            renderMatrixObject(matrix) ?? <pre className="text-xs text-purple-100">{JSON.stringify(matrix)}</pre>
          ) : (
            <pre className="text-xs text-purple-100">{String(text)}</pre>
          )}
        </div>
      </div>
    );
  };

  const renderMatrixObject = (matrixObj: any) => {
    if (!matrixObj) return null;
    // common shapes: { augmented: [...], square: [...], extended: [...], minor: [...] } or direct 2D array
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

    // if matrixObj itself is a nested array
    if (Array.isArray(matrixObj) && Array.isArray(matrixObj[0])) {
      return <MatrixTable matrix={matrixObj.map((r: any[]) => r.map((c: any) => String(c)))} />;
    }

    return null;
  };

  const renderStep = (s: any, i: number) => {
    // if it's a plain string, render as before
    if (typeof s === 'string') return frame ? renderTextStepWithMatrix(s, i) : (
      <div key={i} className="mb-2">
        <pre className="text-xs text-purple-100">{s}</pre>
      </div>
    );

    // if it's an object with operation and matrix
    const op = s.operation ?? s.op ?? `Paso ${i}`;
    const note = s.note ?? s.tag ?? null;
    const matrixObj = s.matrix ?? null;

    return (
      <div key={i} className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="text-sm font-semibold text-blue-200">{op}</div>
          {note && <div className="text-xs text-white/60 px-2 py-1 rounded bg-white/3">{note}</div>}
        </div>

        <div className="p-3 bg-gradient-to-br from-white/3 to-white/2 rounded-lg border border-white/10">
          {matrixObj ? (
            renderMatrixObject(matrixObj)
          ) : (
            <div className="text-xs text-purple-100">{JSON.stringify(s, null, 2)}</div>
          )}
        </div>
      </div>
    );
  };

  const method = result.input?.method ?? result.method ?? null;

  const renderDeterminantState = (st: any, idx: number) => {
    const tag = st.tag ?? '';
    const title = st.operation ?? tag ?? `Paso ${idx}`;
    return (
      <div key={idx} className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="text-sm font-semibold text-blue-200">{title}</div>
          {st.note && <div className="text-xs text-white/60 px-2 py-1 rounded bg-white/3">{st.note}</div>}
        </div>

        <div className="p-3 bg-gradient-to-br from-white/3 to-white/2 rounded-lg border border-white/10">
          {/* matrix display: try multiple possible keys (square/extended/minor/matrix) */}
          {st.square && (
            <div className="mb-2">
              <div className="text-xs text-white/60 text-right">Matriz cuadrada inicial</div>
              {renderMatrixObject({ square: st.square })}
            </div>
          )}

          {st.extended && (
            <div className="mb-2">
              <div className="text-xs text-white/60 text-right">Matriz extendida</div>
              {renderMatrixObject({ extended: st.extended })}
            </div>
          )}

          {st.matrix && (
            <div className="mb-2">{renderMatrixObject(st.matrix)}</div>
          )}

          {st.minor && (
            <div className="mb-2">
              <div className="text-xs text-white/60">Menor</div>
              {renderMatrixObject({ minor: st.minor })}
            </div>
          )}

          {/* sarrus specific: show partials and sums */}
          {tag === 'sarrus_pos' && st.partials && (
            <div className="mt-2 text-xs text-purple-100">
              <div className="font-semibold">Diagonales principales (positivas):</div>
              <ul className="list-disc pl-5 mt-1">
                {st.partials.map((p:any, i:number) => (
                  <li key={i}>{`${p.triple.join(' · ')} = ${p.value}`}</li>
                ))}
              </ul>
              {st.sum && <div className="mt-1">Suma = {st.sum.as_fraction ?? String(st.sum.as_float)}</div>}
            </div>
          )}

          {tag === 'sarrus_neg' && st.partials && (
            <div className="mt-2 text-xs text-purple-100">
              <div className="font-semibold">Diagonales secundarias (negativas):</div>
              <ul className="list-disc pl-5 mt-1">
                {st.partials.map((p:any, i:number) => (
                  <li key={i}>{`${p.triple.join(' · ')} = ${p.value}`}</li>
                ))}
              </ul>
              {st.sum && <div className="mt-1">Suma = {st.sum.as_fraction ?? String(st.sum.as_float)}</div>}
            </div>
          )}

          {tag === 'result' && (
            <div className="mt-2 text-xs text-purple-100">
              <div><strong>Positive sum:</strong> {st.positive_sum?.as_fraction ?? String(st.positive_sum?.as_float)}</div>
              <div><strong>Negative sum:</strong> {st.negative_sum?.as_fraction ?? String(st.negative_sum?.as_float)}</div>
              <div className="mt-1"><strong>Determinante:</strong> {st.determinant?.as_fraction ?? String(st.determinant?.as_float)}</div>
            </div>
          )}

          {/* cofactors: show det2, sign, cofactor value */}
          {tag === 'minor_2x2' && st.det2 && (
            <div className="mt-2 text-xs text-purple-100">Det(2×2) = {st.det2.as_fraction ?? String(st.det2.as_float)}</div>
          )}

          {tag === 'cofactor_value' && (
            <div className="mt-2 text-xs text-purple-100">
              <div>Sign: {st.sign}</div>
              <div>a_ij = {st.a1j?.as_fraction ?? String(st.a1j?.as_float)}</div>
              <div>Subdet: {st.subdet?.as_fraction ?? String(st.subdet?.as_float)}</div>
              <div className="mt-1"><strong>Cofactor:</strong> {st.cofactor?.as_fraction ?? String(st.cofactor?.as_float)}</div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderPropertiesBlock = (propsObj: any) => {
    if (!propsObj) return null;
    return (
      <div className="mt-3 p-3 rounded bg-white/3 border border-white/10 text-xs text-purple-100">
        <div className="text-sm font-semibold text-blue-200 mb-2">Propiedades</div>
        {Object.entries(propsObj)
          .filter(([k, v]: any) => (v === true) || (v && v.applies === true))
          .map(([k, v]: any) => (
            <div key={k} className="mb-2">
              <div className="text-white/70">{k}</div>
              <div>{(v && v.message) ? v.message : (v === true ? 'Aplica' : '')}</div>
            </div>
          ))}

        {/* consistency: only show subkeys that are true */}
        {propsObj.consistency && typeof propsObj.consistency === 'object' && (
          (() => {
            const positive = Object.entries(propsObj.consistency || {}).filter(([, val]: any) => Boolean(val));
            if (positive.length === 0) return null;
            return (
              <div className="mt-2">
                <div className="text-white/70">Consistency</div>
                <div className="mt-1">
                  {positive.map(([ck, cv]: any) => (
                    <div key={ck} className="text-xs">{ck}: {String(cv)}</div>
                  ))}
                </div>
              </div>
            );
          })()
        )}
      </div>
    );
  };

  const renderParticular = (particularPretty: any, particular: any) => {
    if (particularPretty) {
      if (Array.isArray(particularPretty)) {
        return (
          <ul className="list-disc pl-5">
            {particularPretty.map((v:any, i:number) => (
              <li key={i} className="text-xs">{`x${i+1} = ${v ?? '0'}`}</li>
            ))}
          </ul>
        );
      }
      return <pre className="text-xs">{String(particularPretty)}</pre>;
    }

    if (particular) {
      if (Array.isArray(particular)) {
        return (
          <ul className="list-disc pl-5">
            {particular.map((v:number, i:number) => (
              <li key={i} className="text-xs">{`x${i+1} = ${v}`}</li>
            ))}
          </ul>
        );
      }
      return <pre className="text-xs">{JSON.stringify(particular, null, 2)}</pre>;
    }

    return null;
  };

  const renderSummary = (sm: any) => {
    if (!sm) return null;
    const vars = sm.variables ?? sm?.parametric_form?.symbolic?.variables ?? null;
    const basic = sm.variables?.basic ?? sm?.variables?.basic ?? [];
    const free = sm.variables?.free ?? sm?.variables?.free ?? [];
    const particularPretty = sm.parametric_form?.particular_pretty ?? sm.parametric_form?.particular_pretty ?? null;
    const particular = sm.parametric_form?.particular ?? null;

    return (
      <div className="space-y-3">
        <div className="p-3 rounded bg-white/3 border border-white/10">
          <div className="text-sm font-semibold text-blue-200 mb-2">Resumen</div>
          {sm.ranks && (
            <div className="text-xs text-purple-100 mb-2">Rango A: {sm.ranks.rankA}, Rango [A|b]: {sm.ranks.rankAb}</div>
          )}

          {/* homogeneous and trivial solution info */}
          <div className="text-xs text-purple-100 mb-2">
            {typeof sm.homogeneous === 'boolean' && (
              <div>{sm.homogeneous ? 'El sistema es homogéneo' : 'El sistema no es homogéneo'}</div>
            )}
            {typeof sm.trivial_solution === 'boolean' && (
              <div>{sm.trivial_solution ? 'El sistema tiene solución trivial' : 'El sistema no tiene solución trivial'}</div>
            )}
            {sm.dependence && (
              <div>Dependencia: {String(sm.dependence)}</div>
            )}

          </div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <div className="text-white/70 text-[11px]">Variables básicas</div>
              <div className="text-purple-100">{basic.length ? basic.map((i:number) => `x${i+1}`).join(', ') : '—'}</div>
            </div>
            <div>
              <div className="text-white/70 text-[11px]">Variables libres</div>
              <div className="text-purple-100">{free.length ? free.map((i:number) => `x${i+1}`).join(', ') : '—'}</div>
            </div>

            <div>
              <div className="text-white/70 text-[11px]">Tipo de solución</div>
              <div className="text-purple-100">{sm.solution_type ?? sm?.solution_type ?? '—'}</div>
            </div>
          </div>

          { (particularPretty || particular) && (
            <div className="mt-3">
              <div className="text-white/70 text-[11px]">Solución particular</div>
              <div className="text-purple-100 text-xs mt-1">
                {renderParticular(particularPretty, particular)}
              </div>
            </div>
          )}

          {/* Parametric pretty form if exists */}
          {sm.parametric_form?.pretty && (
            <div className="mt-3">
              <div className="text-white/70 text-[11px]">Forma paramétrica</div>
              <div className="text-purple-100 text-xs mt-1">
                <ul className="list-disc pl-5">
                  {sm.parametric_form.pretty.map((line:any, idx:number) => (
                    <li key={idx}>{line}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Reduced forms (U / RREF) */}
          {sm.reduced_form && (
            <div className="mt-3">
              <div className="text-white/70 text-[11px]">Formas reducidas</div>
              <div className="mt-2 space-y-2">
                {sm.reduced_form.U && (
                  <div>
                    <div className="text-xs text-white/70">U (triangular superior)</div>
                    <div className="p-2 bg-white/3 rounded mt-1">
                      {renderMatrixObject({ U: sm.reduced_form.U })}
                    </div>
                  </div>
                )}

                {sm.reduced_form.RREF && (
                  <div>
                    <div className="text-xs text-white/70">RREF</div>
                    <div className="p-2 bg-white/3 rounded mt-1">
                      {renderMatrixObject({ RREF: sm.reduced_form.RREF })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Steps */}
      {stepsArray.length > 0 && (
        <div>
          <div className="text-sm font-semibold text-blue-200 mb-3">Pasos</div>
          <div className="space-y-3">
            {frame ? (
              // If determinant-like method, render specialized frame.states
              (method === 'sarrus' || method === 'cofactors' || method === 'cramer') ? (
                <div>
                  {(frame.states ?? []).map((st:any, idx:number) => renderDeterminantState(st, idx))}
                  {renderPropertiesBlock(result.properties ?? result.result?.properties)}
                </div>
              ) : (
                // default: align textual steps with frame snapshots
                stepsArray.map((s:any, i:number) => renderTextStepWithMatrix(String(s), i))
              )
            ) : (
              // no frame: generic step rendering
              stepsArray.map((s:any, i:number) => renderStep(s, i))
            )}
          </div>
        </div>
      )}

      {/* Result matrix pretty (for sum/sub/matmul/transpose/scalar etc) */}
      {result?.result?.matrix_pretty && (
        <div>
          <div className="text-sm font-semibold text-blue-200 mb-3">Resultado</div>
          <div className="p-3 bg-gradient-to-br from-white/3 to-white/2 rounded-lg border border-white/10">
            <MatrixTable matrix={result.result.matrix_pretty} />
          </div>
        </div>
      )}

      {/* Summary */}
      {summary && (
        <div>
          {renderSummary(summary)}
        </div>
      )}
    </div>
  );
};

export default ResultPretty;
