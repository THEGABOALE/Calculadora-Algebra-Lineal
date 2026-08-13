import React from 'react';
import { MatrixInput } from '../inputs/MatrixInput';
import { VectorInput } from '../inputs/VectorInput';

type Props = {
  matrixA: any;
  dimensionsA: any;
  vectorB: any;
  dimensionVectorB: number;
  selectedMatrixCell: any;
  selectedVectorCell: any;
  selectedScalar: boolean;
  matrixErrorsA: Record<string,string>;
  vectorErrorsB: Record<string,string>;
  setSelectedMatrixCell: (v:any)=>void;
  setSelectedVectorCell: (v:any)=>void;
  setSelectedScalar: (v:boolean)=>void;
  handleMatrixCellChange: (m:'A'|'B', r:number, c:number, v:string)=>void;
  handleVectorCellChange: (name:'A'|'B', idx:number, v:string)=>void;
  onDimensionsAChange: (r:number,c:number)=>void;
  onDimensionBChange: (d:number)=>void;
};

export default function SystemEquationSection(props: Props) {
  const { matrixA, dimensionsA, vectorB, dimensionVectorB, selectedMatrixCell, selectedVectorCell, selectedScalar, matrixErrorsA, vectorErrorsB, setSelectedMatrixCell, setSelectedVectorCell, setSelectedScalar, handleMatrixCellChange, handleVectorCellChange, onDimensionsAChange, onDimensionBChange } = props;

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
          setSelectedVectorCell(null);
        }}
        onCellChange={(r, c, v) => handleMatrixCellChange('A', r, c, v)}
        errors={matrixErrorsA}
        onDimensionsChange={(rows, cols) => onDimensionsAChange(rows, cols)}
      />

      <VectorInput
        label="Vector B (términos independientes)"
        vector={vectorB}
        dimension={dimensionVectorB}
        isSelected={selectedVectorCell?.vector === 'B'}
        selectedIndex={selectedVectorCell?.vector === 'B' ? selectedVectorCell.index : null}
        onSelectVector={() => {}}
        onSelectCell={(index) => {
            setSelectedVectorCell({ vector: 'B', index });
            setSelectedMatrixCell(null);
            setSelectedScalar(false);
        }}
        onCellChange={(idx, v) => handleVectorCellChange('B', idx, v)}
        errors={vectorErrorsB}
        onDimensionChange={(dim) => onDimensionBChange(dim)}
      />
    </>
  );
}
