import React from 'react';
import { MatrixInput } from '../inputs/MatrixInput';

type Props = {
  matrixA: any;
  dimensionsA: any;
  selectedMatrixCell: any;
  matrixErrorsA: Record<string,string>;
  setSelectedMatrixCell: (v:any)=>void;
  handleMatrixCellChange: (m:'A'|'B', r:number, c:number, v:string)=>void;
  onDimensionsAChange: (r:number,c:number)=>void;
};

export default function DeterminantSection(props: Props) {
  const { matrixA, dimensionsA, selectedMatrixCell, matrixErrorsA, setSelectedMatrixCell, handleMatrixCellChange, onDimensionsAChange } = props;

  return (
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
          // keep vector selection unchanged for determinant
        }}
        onCellChange={(r, c, v) => handleMatrixCellChange('A', r, c, v)}
        errors={matrixErrorsA}
        onDimensionsChange={(rows, cols) => onDimensionsAChange(rows, cols)}
      />
    </>
  );
}
