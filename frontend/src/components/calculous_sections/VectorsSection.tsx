import React from 'react';
import { VectorInput } from '../inputs/VectorInput';
import EscalarInput from '../inputs/EscalarInput';

type Props = {
  vectorA: any;
  vectorB: any;
  vectorC?: any;
  dimensionVectorA: number;
  dimensionVectorB: number;
  dimensionVectorC?: number;
  selectedVectorCell: any;
  setSelectedVectorCell: (v:any)=>void;
  setSelectedMatrixCell: (v:any)=>void;
  setSelectedScalar: (v:boolean)=>void;
  selectedScalar?: boolean;
  handleVectorCellChange: (name:'A'|'B'|'C', idx:number, v:string)=>void;
  vectorErrorsA: Record<string,string>;
  vectorErrorsB: Record<string,string>;
  vectorErrorsC?: Record<string,string>;
  onDimensionVectorAChange: (d:number)=>void;
  onDimensionVectorBChange: (d:number)=>void;
  onDimensionVectorC?: (d:number)=>void;
  needsTwoInputs: boolean;
  showScalar1?: boolean;
  showScalar2?: boolean;
  scalarInput1?: string;
  scalarInput2?: string;
  setScalarInput1?: (v:string)=>void;
  setScalarInput2?: (v:string)=>void;
  scalarError1?: string|null;
  scalarError2?: string|null;
};

export default function VectorsSection(props: Props) {
  const {
    vectorA, vectorB, vectorC,
    dimensionVectorA, dimensionVectorB, dimensionVectorC,
    selectedVectorCell, setSelectedVectorCell, setSelectedMatrixCell, setSelectedScalar,
    handleVectorCellChange, vectorErrorsA, vectorErrorsB, vectorErrorsC,
    onDimensionVectorAChange, onDimensionVectorBChange, onDimensionVectorC,
    needsTwoInputs,
    showScalar1, showScalar2,
    scalarInput1, scalarInput2,
    setScalarInput1, setScalarInput2,
    scalarError1, scalarError2
  } = props;
  const { selectedScalar } = props as any;

  return (
    <>
      <VectorInput
        label="Vector A"
        vector={vectorA}
        dimension={dimensionVectorA}
        isSelected={selectedVectorCell?.vector === 'A'}
        selectedIndex={selectedVectorCell?.vector === 'A' ? selectedVectorCell.index : null}
        onSelectVector={() => {}}
        onSelectCell={(index) => {
          setSelectedVectorCell({ vector: 'A', index });
          setSelectedMatrixCell(null);
        }}
        onCellChange={(idx, v) => handleVectorCellChange('A', idx, v)}
        errors={vectorErrorsA}
        onDimensionChange={(dim) => onDimensionVectorAChange(dim)}
      />

      {needsTwoInputs && (
        <VectorInput
          label="Vector B"
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
          onDimensionChange={(dim) => onDimensionVectorBChange(dim)}
        />
      )}

      {vectorC && (
        <VectorInput
          label="Vector C"
          vector={vectorC}
          dimension={dimensionVectorC}
          isSelected={selectedVectorCell?.vector === 'C'}
          selectedIndex={selectedVectorCell?.vector === 'C' ? selectedVectorCell.index : null}
          onSelectVector={() => {}}
          onSelectCell={(index) => {
            setSelectedVectorCell({ vector: 'C', index });
            setSelectedMatrixCell(null);
            setSelectedScalar(false);
          }}
          onCellChange={(idx, v) => handleVectorCellChange('C', idx, v)}
          errors={vectorErrorsC}
          onDimensionChange={(dim) => onDimensionVectorC && onDimensionVectorC(dim)}
        />
      )}

      {showScalar1 && (
        <EscalarInput
          value={scalarInput1 ?? ''}
          onChange={setScalarInput1 ?? (()=>{})}
          onSelect={() => { setSelectedScalar(true); setSelectedVectorCell(null); setSelectedMatrixCell(null); }}
          onBlur={() => setSelectedScalar(false)}
          isSelected={selectedScalar}
          label="Escalar c"
        />
      )}
      {showScalar2 && (
        <EscalarInput
          value={scalarInput2 ?? ''}
          onChange={setScalarInput2 ?? (()=>{})}
          onSelect={() => { setSelectedScalar(true); setSelectedVectorCell(null); setSelectedMatrixCell(null); }}
          onBlur={() => setSelectedScalar(false)}
          isSelected={selectedScalar}
          label="Escalar d"
        />
      )}
    </>
  );
}
