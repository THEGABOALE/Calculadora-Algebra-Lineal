import React from 'react';
import { MatrixInput } from '../inputs/MatrixInput';
import EscalarInput from '../inputs/EscalarInput';

type Props = {
  operation: string;
  manyOps: string[];
  manyMatrices: any[];
  manyCount: number;
  matrixA: any;
  matrixB: any;
  dimensionsA: any;
  dimensionsB: any;
  selectedMatrixCell: any;
  selectedVectorCell: any;
  selectedScalar: boolean;
  matrixErrorsA: Record<string, string>;
  matrixErrorsB: Record<string, string>;
  manyMatricesErrors: Record<string, string>[];
  setSelectedMatrixCell: (v: any) => void;
  setSelectedVectorCell: (v: any) => void;
  setSelectedScalar: (v: boolean) => void;
  handleMatrixCellChange: (m: 'A'|'B', r:number, c:number, v:string) => void;
  handleManyMatrixCellChange: (idx:number, r:number, c:number, v:string) => void;
  onDimensionsAChange: (r:number, c:number) => void;
  onDimensionsBChange: (r:number, c:number) => void;
  onManyDimensionsChange: (idx:number, r:number, c:number) => void;
  scalarInput: string;
  setScalarInput: (s:string) => void;
  setScalarError: (e: string|null) => void;
  setManyCount: (n:number) => void;
};

export default function MatricesSection(props: Props) {
  const {
    operation, manyOps, manyMatrices, manyCount,
    matrixA, matrixB, dimensionsA, dimensionsB,
    selectedMatrixCell, selectedVectorCell, selectedScalar,
    matrixErrorsA, matrixErrorsB, manyMatricesErrors,
    setSelectedMatrixCell, setSelectedVectorCell, setSelectedScalar,
    handleMatrixCellChange, handleManyMatrixCellChange,
    onDimensionsAChange, onDimensionsBChange, onManyDimensionsChange,
    scalarInput, setScalarInput, setScalarError, setManyCount,
  } = props;

  const needsTwoInputs = !['transpose', 'inverse'].includes(operation);

  return (
    <>
      {operation === 'scalar_mult' ? (
        <div className="col-span-2 space-y-4">
          <MatrixInput
            label="Matriz A"
            matrix={matrixA}
            dimensions={dimensionsA}
            isSelected={selectedMatrixCell?.matrix === 'A'}
            selectedCell={selectedMatrixCell?.matrix === 'A' ? { row: selectedMatrixCell.row, col: selectedMatrixCell.col } : null}
            onSelectMatrix={() => {}}
            onSelectCell={(row, col) => {
              setSelectedMatrixCell({ matrix: 'A', row, col });
              setSelectedVectorCell(null);
              setSelectedScalar(false);
            }}
            onCellChange={(r, c, v) => handleMatrixCellChange('A', r, c, v)}
            errors={matrixErrorsA}
            onDimensionsChange={(rows, cols) => onDimensionsAChange(rows, cols)}
          />

          <EscalarInput
            value={scalarInput}
            onChange={(v) => { setScalarInput(v); setScalarError(null); }}
            onSelect={() => { setSelectedScalar(true); setSelectedMatrixCell(null); setSelectedVectorCell(null); }}
            onBlur={() => setSelectedScalar(false)}
            isSelected={selectedScalar}
            label="Escalar k"
          />
        </div>
      ) : manyOps.includes(operation) ? (
        <div className="col-span-2 space-y-4">
          <div className="flex items-center gap-3">
            <label className="text-sm text-purple-200">Número de matrices:</label>
            <input
              type="number"
              min={2}
              max={6}
              value={manyCount}
              onChange={(e) => setManyCount(Number(e.target.value || 2))}
              className="bg-white/5 border border-white/10 rounded px-2 py-1 w-20 text-blue-200"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {manyMatrices.map((M, idx) => (
              <MatrixInput
                key={`many-${idx}`}
                label={`Matriz ${idx + 1}`}
                matrix={M}
                dimensions={{ rows: M.length, cols: M[0]?.length ?? 0 }}
                isSelected={false}
                selectedCell={null}
                onSelectMatrix={() => {}}
                onSelectCell={(row, col) => {
                  setSelectedMatrixCell(null);
                  setSelectedVectorCell(null);
                }}
                onCellChange={(r, c, v) => handleManyMatrixCellChange(idx, r, c, v)}
                errors={manyMatricesErrors[idx] || {}}
                onDimensionsChange={(rows, cols) => onManyDimensionsChange(idx, rows, cols)}
              />
            ))}
          </div>
        </div>
      ) : (
        <>
          <MatrixInput
            label="Matriz A"
            matrix={matrixA}
            dimensions={dimensionsA}
            isSelected={selectedMatrixCell?.matrix === 'A'}
            selectedCell={selectedMatrixCell?.matrix === 'A' ? { row: selectedMatrixCell.row, col: selectedMatrixCell.col } : null}
            onSelectMatrix={() => {}}
            onSelectCell={(row, col) => {
              setSelectedMatrixCell({ matrix: 'A', row, col });
              setSelectedVectorCell(null);
              setSelectedScalar(false);
            }}
            onCellChange={(r, c, v) => handleMatrixCellChange('A', r, c, v)}
            errors={matrixErrorsA}
            onDimensionsChange={(rows, cols) => onDimensionsAChange(rows, cols)}
          />

          {needsTwoInputs && (
            <MatrixInput
              label="Matriz B"
              matrix={matrixB}
              dimensions={dimensionsB}
              isSelected={selectedMatrixCell?.matrix === 'B'}
              selectedCell={selectedMatrixCell?.matrix === 'B' ? { row: selectedMatrixCell.row, col: selectedMatrixCell.col } : null}
              onSelectMatrix={() => {}}
              onSelectCell={(row, col) => {
                setSelectedMatrixCell({ matrix: 'B', row, col });
                setSelectedVectorCell(null);
                setSelectedScalar(false);
              }}
              onCellChange={(r, c, v) => handleMatrixCellChange('B', r, c, v)}
              errors={matrixErrorsB}
              onDimensionsChange={(rows, cols) => onDimensionsBChange(rows, cols)}
            />
          )}
        </>
      )}
    </>
  );
}
