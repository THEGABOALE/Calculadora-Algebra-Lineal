import { useState, useEffect } from 'react';
import { motion, AnimatePresence, color } from 'framer-motion';
import { ArrowLeft, Plus, Minus, X as Multiply, RotateCw, Calculator as CalcIcon, Grid3x3Icon, Triangle, LineChart } from 'lucide-react';
import { GraphCalculator } from './GraphCalculator';
import DerivativeInputs from './general/DerivativeInputs';
import IntegralInputs from './general/IntegralInputs';
import { Button } from './ui/button';
import { DigitalKeyboard } from './DigitalKeyboard';
import { OperationSelector } from './OperationSelector';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import parseCellInput from '../utils/parseInput';
import { matrixOperate, matrixDeterminant, matrixReduce, vectorOperate, vectorCombination } from '../api/client';
import MatricesSection from './calculous_sections/MatricesSection';
import SystemEquationSection from './calculous_sections/SystemEquationSection';
import DeterminantSection from './calculous_sections/DeterminantSection';
import VectorsSection from './calculous_sections/VectorsSection';
import ResultSection from './calculous_sections/ResultSection';
import { fontFamily } from '@mui/system';

    // Map frontend operation ids to backend expected operation strings
    function mapMatrixOperation(opId: string) {
        const m: Record<string, string> = {
            // single-pair operations removed: use many-versions only
            scalar_mult: 'scalar',
            //scalar: 'scalar',
            transpose: 'transpose',
            inverse: 'inverse',
            sum_many: 'sum_many',
            sub_many: 'sub_many',
            matmul_chain: 'matmul_chain',
        };
        return m[opId] || opId;
    }

    function mapVectorOperation(opId: string) {
      const m: Record<string, string | null> = {
        add_vectores: 'add',
        sub_vectores: 'sub',
        dot: 'dot',
        scalar_vect: 'escalar',
        comb2: 'comb2',
        comb3: 'comb3',
        // 'linear_combination' handled separately
      };
      return m[opId] ?? null;
    }

interface CalculatorProps {
  onBack: () => void;
}

export type MatrixValue = (string | number)[][];
export type VectorValue = (string | number)[];

type InputMode = 'general' | 'matrix' | 'vector' | 'reduce' | 'determinant';

export function AlgebraicMethods({ onBack }: CalculatorProps) {
  const [inputMode, setInputMode] = useState<InputMode>('general');
  
  // Matrix state
  const [matrixA, setMatrixA] = useState<MatrixValue>([[0, 0], [0, 0]]);
  const [matrixB, setMatrixB] = useState<MatrixValue>([[0, 0], [0, 0]]);
  const [dimensionsA, setDimensionsA] = useState({ rows: 2, cols: 2 });
  const [dimensionsB, setDimensionsB] = useState({ rows: 2, cols: 2 });
  const [selectedMatrixCell, setSelectedMatrixCell] = useState<{ 
    matrix: 'A' | 'B'; 
    row: number; 
    col: number 
  } | null>(null);
  
  // Vector state
  const [vectorA, setVectorA] = useState<VectorValue>([0, 0, 0]);
  const [vectorB, setVectorB] = useState<VectorValue>([0, 0, 0]);
  const [vectorC, setVectorC] = useState<VectorValue>([0, 0, 0]);
  const [dimensionVectorA, setDimensionVectorA] = useState(3);
  const [dimensionVectorB, setDimensionVectorB] = useState(3);
  const [dimensionVectorC, setDimensionVectorC] = useState(3);
  const [selectedVectorCell, setSelectedVectorCell] = useState<{ 
    vector: 'A' | 'B' | 'C'; 
    index: number 
  } | null>(null);

  // scalar selection state (for EscalarInput)
  const [selectedScalar, setSelectedScalar] = useState<boolean>(false);

  const [operation, setOperation] = useState<string>('sum_many');
  const [manyCount, setManyCount] = useState<number>(2);
  const [manyMatrices, setManyMatrices] = useState<MatrixValue[]>(() => {
    return [
      Array(2).fill(0).map(() => Array(2).fill(0)),
      Array(2).fill(0).map(() => Array(2).fill(0)),
    ];
  });
  const [manyMatricesErrors, setManyMatricesErrors] = useState<Record<string, string>[]>([]);

  // scalar input for scalar multiplication (string so parser can accept pi, fractions...)
  const [scalarInput, setScalarInput] = useState<string>('1');
  const [scalarInput2, setScalarInput2] = useState<string>('1');
  const [scalarError, setScalarError] = useState<string | null>(null);
  const [scalarError2, setScalarError2] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<any | null>(null);

  // Clear any cached API result when opening the calculator
  useEffect(() => {
    localStorage.removeItem('calc_last_result');
    setLastResult(null);
    window.dispatchEvent(new Event('calc:updated'));
  }, []);

  // when operation changes, clear scalar selection and cached results
  useEffect(() => {
    if (operation !== 'scalar_mult') setSelectedScalar(false);
    setLastResult(null);
    localStorage.removeItem('calc_last_result');
    window.dispatchEvent(new Event('calc:updated'));
  }, [operation]);

  const handleKeyPress = (value: string) => {
    // Prefer writing to a selected scalar if present
    if (selectedScalar) {
      const currentValue = String(scalarInput);
      if (value === 'backspace') {
        setScalarInput(currentValue.length > 1 ? currentValue.slice(0, -1) : '0');
      } else if (value === 'clear') {
        setScalarInput('0');
      } else if (value === '+/-') {
        setScalarInput(currentValue.startsWith('-') ? currentValue.slice(1) : '-' + currentValue);
      } else {
        setScalarInput(currentValue === '0' ? value : currentValue + value);
      }
      return;
    }

    // Prefer writing to a selected vector cell if present (covers vector mode and reduce's vector B)
    if (selectedVectorCell) {
      const { vector: vectorName, index } = selectedVectorCell;
      const vector = vectorName === 'A' ? vectorA : vectorB;
      const setVector = vectorName === 'A' ? setVectorA : setVectorB;

      const newVector = vector.map((val, i) => {
        if (i === index) {
          const currentValue = String(val);
          if (value === 'backspace') {
            return currentValue.length > 1 ? currentValue.slice(0, -1) : '0';
          } else if (value === 'clear') {
            return '0';
          } else if (value === '+/-') {
            return currentValue.startsWith('-') ? currentValue.slice(1) : '-' + currentValue;
          } else {
            return currentValue === '0' ? value : currentValue + value;
          }
        }
        return val;
      });

      setVector(newVector);
      return;
    }

    // Otherwise write to selected matrix cell (covers matrix/reduce/determinant)
    if (selectedMatrixCell) {
      const { matrix: matrixName, row, col } = selectedMatrixCell;
      const matrix = matrixName === 'A' ? matrixA : matrixB;
      const setMatrix = matrixName === 'A' ? setMatrixA : setMatrixB;

      const newMatrix = matrix.map((r, i) =>
        r.map((c, j) => {
          if (i === row && j === col) {
            const currentValue = String(c);
            if (value === 'backspace') {
              return currentValue.length > 1 ? currentValue.slice(0, -1) : '0';
            } else if (value === 'clear') {
              return '0';
            } else if (value === '+/-') {
              return currentValue.startsWith('-') ? currentValue.slice(1) : '-' + currentValue;
            } else {
              return currentValue === '0' ? value : currentValue + value;
            }
          }
          return c;
        })
      );

      setMatrix(newMatrix);
    }
  };

  const handleMatrixCellChange = (matrixName: 'A' | 'B', row: number, col: number, newValue: string) => {
    const setter = matrixName === 'A' ? setMatrixA : setMatrixB;
    const matrix = matrixName === 'A' ? matrixA : matrixB;
    const newMatrix = matrix.map((r, i) => r.map((c, j) => (i === row && j === col ? newValue : c)));
    // validate
    const parse = parseCellInput(newValue);
    const key = `${row}-${col}`;
    if (matrixName === 'A') {
      if (!parse.valid) {
        setMatrixErrorsA((prev) => ({ ...prev, [key]: parse.error }));
      } else {
        setMatrixErrorsA((prev) => {
          const copy = { ...prev };
          delete copy[key];
          return copy;
        });
      }
    } else {
      if (!parse.valid) {
        setMatrixErrorsB((prev) => ({ ...prev, [key]: parse.error }));
      } else {
        setMatrixErrorsB((prev) => {
          const copy = { ...prev };
          delete copy[key];
          return copy;
        });
      }
    }

    setter(newMatrix);
  };

  // Many-matrices handlers
  const manyOps = ['sum_many', 'sub_many', 'matmul_chain'];

  const clampManyCount = (n: number) => Math.max(2, Math.min(6, n));

  const handleManyCountChange = (n: number) => {
    const next = clampManyCount(n);
    setManyCount(next);
    setManyMatrices((prev) => {
      const copy = [...prev];
      if (next > copy.length) {
        for (let i = copy.length; i < next; i++) {
          copy.push(Array(2).fill(0).map(() => Array(2).fill(0)));
        }
      } else if (next < copy.length) {
        copy.length = next;
      }
      return copy;
    });
    setManyMatricesErrors((prev) => {
      const copy = [...prev];
      if (next > copy.length) {
        for (let i = copy.length; i < next; i++) copy.push({});
      } else if (next < copy.length) copy.length = next;
      return copy;
    });
  };

  const handleManyMatrixCellChange = (idx: number, row: number, col: number, newValue: string) => {
    setManyMatrices((prev) => {
      const copy = prev.map((m) => m.map((r) => [...r]));
      const matrix = copy[idx];
      matrix[row][col] = newValue;
      return copy;
    });

    // validate
    const parsed = parseCellInput(newValue);
    setManyMatricesErrors((prev) => {
      const copy = prev.length ? prev.map((p) => ({ ...p })) : Array(manyCount).fill({}).map(() => ({}));
      const key = `${row}-${col}`;
      if (!parsed.valid) {
        copy[idx] = { ...(copy[idx] || {}), [key]: parsed.error || 'Invalid' };
      } else {
        if (!copy[idx]) copy[idx] = {};
        const c = { ...copy[idx] };
        delete c[key];
        copy[idx] = c;
      }
      return copy;
    });
  };

  const handleVectorCellChange = (vectorName: 'A' | 'B' | 'C', index: number, newValue: string) => {
    const setter = vectorName === 'A' ? setVectorA : (vectorName === 'B' ? setVectorB : setVectorC);
    const vector = vectorName === 'A' ? vectorA : (vectorName === 'B' ? vectorB : vectorC);
    const newVector = vector.map((v, i) => (i === index ? newValue : v));
    const parse = parseCellInput(newValue);
    const key = String(index);
    if (vectorName === 'A') {
      if (!parse.valid) setVectorErrorsA((prev) => ({ ...prev, [key]: parse.error }));
      else setVectorErrorsA((prev) => { const copy = { ...prev }; delete copy[key]; return copy; });
    } else if (vectorName === 'B') {
      if (!parse.valid) setVectorErrorsB((prev) => ({ ...prev, [key]: parse.error }));
      else setVectorErrorsB((prev) => { const copy = { ...prev }; delete copy[key]; return copy; });
    } else {
      if (!parse.valid) setVectorErrorsC((prev) => ({ ...prev, [key]: parse.error }));
      else setVectorErrorsC && setVectorErrorsC((prev:any) => { const copy = { ...prev }; delete copy[key]; return copy; });
    }

    setter(newVector);
  };

  // validation error maps
  const [matrixErrorsA, setMatrixErrorsA] = useState<Record<string, string>>({});
  const [matrixErrorsB, setMatrixErrorsB] = useState<Record<string, string>>({});
  const [vectorErrorsA, setVectorErrorsA] = useState<Record<string, string>>({});
  const [vectorErrorsB, setVectorErrorsB] = useState<Record<string, string>>({});
  const [vectorErrorsC, setVectorErrorsC] = useState<Record<string, string>>({});

  // calculate handler (extracted from previous inline onClick)
  const handleCalculate = async () => {
    setSubmitError(null);
    setLoading(true);
    try {
      const parseMatrix = (m: MatrixValue) => {
        const A: number[][] = [];
        const errors: Record<string, string> = {};
        m.forEach((row, i) => {
          const r: number[] = [];
          row.forEach((cell, j) => {
            const parsed = parseCellInput(String(cell));
            const key = `${i}-${j}`;
            if (!parsed.valid) {
              errors[key] = parsed.error || 'Invalid';
              r.push(NaN);
            } else r.push(parsed.value ?? NaN);
          });
          A.push(r);
        });
        return { A, errors };
      };

      const parseVector = (v: VectorValue) => {
        const out: number[] = [];
        const errors: Record<string, string> = {};
        v.forEach((cell, i) => {
          const parsed = parseCellInput(String(cell));
          const key = String(i);
          if (!parsed.valid) {
            errors[key] = parsed.error || 'Invalid';
            out.push(NaN);
          } else out.push(parsed.value ?? NaN);
        });
        return { out, errors };
      };

      if (inputMode === 'matrix') {
        if (operation === 'determinant') {
          const { A, errors } = parseMatrix(matrixA);
          if (Object.keys(errors).length) {
            setMatrixErrorsA(errors);
            setSubmitError('Hay entradas inválidas en la matriz A.');
            setLoading(false);
            return;
          }
          const res = await matrixDeterminant({ method: 'cofactors', A });
          localStorage.setItem('calc_last_result', JSON.stringify(res));
          setLastResult(res);
          window.dispatchEvent(new Event('calc:updated'));
          setLoading(false);
          return;
        }

        if (manyOps.includes(operation)) {
          const matricesParsed: number[][][] = [];
          const allErrors: Record<string, string>[] = [];
          let anyErr = false;
          manyMatrices.forEach((m, mi) => {
            const parsedRes = parseMatrix(m);
            matricesParsed.push(parsedRes.A);
            allErrors.push(parsedRes.errors);
            if (Object.keys(parsedRes.errors).length) anyErr = true;
          });
          if (anyErr) {
            setManyMatricesErrors(allErrors);
            setSubmitError('Hay entradas inválidas en una o más matrices.');
            setLoading(false);
            return;
          }
          const payload: any = { operation: mapMatrixOperation(operation), matrices: matricesParsed };
          const res = await matrixOperate(payload);
          localStorage.setItem('calc_last_result', JSON.stringify(res));
          setLastResult(res);
          window.dispatchEvent(new Event('calc:updated'));
          setLoading(false);
          return;
        }

        const { A, errors: errA } = parseMatrix(matrixA);
        let payload: any = { operation: mapMatrixOperation(operation) };
        if (Object.keys(errA).length) {
          setMatrixErrorsA(errA);
          setSubmitError('Hay entradas inválidas en la matriz A.');
          setLoading(false);
          return;
        }
        payload.A = A;

        if (operation === 'scalar_mult') {
          const parsedScalar = parseCellInput(scalarInput);
          if (!parsedScalar.valid) {
            setScalarError(parsedScalar.error || 'Invalid scalar');
            setSubmitError('Escalar inválido');
            setLoading(false);
            return;
          }
          payload.scalar = parsedScalar.value ?? 0;
        }

        if (needsTwoInputs) {
          const { A: B, errors: errB } = parseMatrix(matrixB);
          if (Object.keys(errB).length) {
            setMatrixErrorsB(errB);
            setSubmitError('Hay entradas inválidas en la matriz B.');
            setLoading(false);
            return;
          }
          payload.B = B;
        }

        const res = await matrixOperate(payload);
        localStorage.setItem('calc_last_result', JSON.stringify(res));
        setLastResult(res);
        window.dispatchEvent(new Event('calc:updated'));
        setLoading(false);
        return;
      }

      if (inputMode === 'determinant') {
        const { A, errors } = parseMatrix(matrixA);
        if (Object.keys(errors).length) {
          setMatrixErrorsA(errors);
          setSubmitError('Hay entradas inválidas en la matriz A.');
          setLoading(false);
          return;
        }
        const res = await matrixDeterminant({ method: operation || 'cofactors', A });
        localStorage.setItem('calc_last_result', JSON.stringify(res));
        setLastResult(res);
        window.dispatchEvent(new Event('calc:updated'));
        setLoading(false);
        return;
      }

      if (inputMode === 'reduce') {
        const { A, errors: errA } = parseMatrix(matrixA);
        const { out: b, errors: errb } = parseVector(vectorB);
        if (Object.keys(errA).length) {
          setMatrixErrorsA(errA);
          setSubmitError('Hay entradas inválidas en la matriz A.');
          setLoading(false);
          return;
        }
        if (Object.keys(errb).length) {
          setVectorErrorsB(errb);
          setSubmitError('Hay entradas inválidas en el vector B.');
          setLoading(false);
          return;
        }
        const res = await matrixReduce({ method: operation === 'gauss_jordan' ? 'gauss-jordan' : 'gauss', A, b });
        localStorage.setItem('calc_last_result', JSON.stringify(res));
        setLastResult(res);
        window.dispatchEvent(new Event('calc:updated'));
        setLoading(false);
        return;
      }

      if (inputMode === 'vector') {
        if (operation === 'linear_combination') {
          const { A, errors: errA } = parseMatrix(matrixA);
          const { out: b, errors: errb } = parseVector(vectorB);
          if (Object.keys(errA).length) {
            setMatrixErrorsA(errA);
            setSubmitError('Hay entradas inválidas en la matriz A.');
            setLoading(false);
            return;
          }
          if (Object.keys(errb).length) {
            setVectorErrorsB(errb);
            setSubmitError('Hay entradas inválidas en el vector B.');
            setLoading(false);
            return;
          }
          const res = await vectorCombination({ A, b });
          localStorage.setItem('calc_last_result', JSON.stringify(res));
          setLastResult(res);
          window.dispatchEvent(new Event('calc:updated'));
          setLoading(false);
          return;
        }

        const { out: u, errors: errU } = parseVector(vectorA);
        const { out: v, errors: errV } = parseVector(vectorB);
        if (Object.keys(errU).length) {
          setVectorErrorsA(errU);
          setSubmitError('Hay entradas inválidas en el vector A.');
          setLoading(false);
          return;
        }
        if (needsTwoInputs && Object.keys(errV).length) {
          setVectorErrorsB(errV);
          setSubmitError('Hay entradas inválidas en el vector B.');
          setLoading(false);
          return;
        }

        const op = mapVectorOperation(operation);
        if (!op) {
          setSubmitError('Operación de vectores no soportada por el backend.');
          setLoading(false);
          return;
        }

        // Build payload depending on operation requirements
        const payload: any = { operation: op };

        if (op === 'escalar') {
          // scalar multiplication: vectors.u and scalars.c
          payload.vectors = { u };
          const parsedScalar = parseCellInput(scalarInput);
          if (!parsedScalar.valid) {
            setScalarError(parsedScalar.error || 'Escalar inválido');
            setSubmitError('Escalar inválido');
            setLoading(false);
            return;
          }
          payload.scalars = { c: parsedScalar.value ?? 0 };
        } else if (op === 'comb2') {
          // c*u + d*v -> vectors.u, vectors.v and scalars.c, scalars.d
          payload.vectors = { u, v };
          const parsedC = parseCellInput(scalarInput);
          const parsedD = parseCellInput(scalarInput2);
          if (!parsedC.valid) {
            setScalarError(parsedC.error || 'Escalar c inválido');
            setSubmitError('Escalar c inválido');
            setLoading(false);
            return;
          }
          if (!parsedD.valid) {
            setScalarError2(parsedD.error || 'Escalar d inválido');
            setSubmitError('Escalar d inválido');
            setLoading(false);
            return;
          }
          payload.scalars = { c: parsedC.value ?? 0, d: parsedD.value ?? 0 };
        } else if (op === 'comb3') {
          // u + c*v + d*w -> vectors.u, v, w and scalars.c, d
          const { out: w, errors: errW } = parseVector(vectorC);
          if (Object.keys(errW).length) {
            setVectorErrorsC(errW);
            setSubmitError('Hay entradas inválidas en el vector C.');
            setLoading(false);
            return;
          }
          payload.vectors = { u, v, w };
          const parsedC = parseCellInput(scalarInput);
          const parsedD = parseCellInput(scalarInput2);
          if (!parsedC.valid) {
            setScalarError(parsedC.error || 'Escalar c inválido');
            setSubmitError('Escalar c inválido');
            setLoading(false);
            return;
          }
          if (!parsedD.valid) {
            setScalarError2(parsedD.error || 'Escalar d inválido');
            setSubmitError('Escalar d inválido');
            setLoading(false);
            return;
          }
          payload.scalars = { c: parsedC.value ?? 0, d: parsedD.value ?? 0 };
        } else if (op === 'dot') {
          // dot expects vectors 'v' and 'w' in backend
          payload.vectors = { v: u, w: v };
        } else {
          // default add/sub: backend expects 'u' and 'v'
          payload.vectors = { u, v };
        }

        const res = await vectorOperate(payload);
        localStorage.setItem('calc_last_result', JSON.stringify(res));
        setLastResult(res);
        window.dispatchEvent(new Event('calc:updated'));
        setLoading(false);
        return;
      }
    } catch (e: any) {
      console.error(e);
      setSubmitError(e?.message || 'Error en la petición');
      setLoading(false);
    }
  };

  // Matrix operations mapped to backend implementations in algebra/algorithms/matrix/matrix_operations.py
  const matrixOperations = [
    { id: 'sum_many', label: 'A + B + ..', icon: Plus, description: 'Suma de varias matrices' },
    { id: 'sub_many', label: 'A - B + ..', icon: Minus, description: 'Resta de varias matrices' },
    { id: 'matmul_chain', label: 'A · B · ...', icon: Multiply, description: 'Cadena de multiplicaciones' },
    { id: 'scalar_mult', label: 'k · A', icon: Multiply, description: 'Multiplicación escalar' },
    { id: 'transpose', label: 'Aᵀ', icon: RotateCw, description: 'Transponer A', single: true },
    { id: 'inverse', label: 'A⁻¹', icon: Grid3x3Icon, description: 'Matriz inversa', single: true },
  ];

  // Vector operations (from algebra/algorithms/vectors)
  const vectorOperations = [
    { id: 'add_vectores', label: 'A + B', icon: Plus, description: 'Suma de vectores' },
    { id: 'sub_vectores', label: 'A - B', icon: Minus, description: 'Resta de vectores' },
    { id: 'dot', label: 'A · B', icon: Multiply, description: 'Producto escalar' },
    { id: 'scalar_vect', label: 'k · A', icon: Multiply, description: 'Multiplicación escalar', single: true },
    { id: 'comb2', label: 'c·u + d·v', icon: Plus, description: 'Combinación lineal (2 vectores)' },
    { id: 'comb3', label: 'u + c·v + d·w', icon: Plus, description: 'Combinación lineal (3 vectores)' },
    { id: 'linear_combination', label: 'Combinación lineal (Ax = b)', icon: Plus, description: 'Verificar/obtener combinación lineal' },
  ];

  // Reduction methods (sistema de ecuaciones)
  const reduceOperations = [
    { id: 'gauss', label: 'Eliminación Gauss', icon: Grid3x3Icon, description: 'Eliminación gaussiana (forward/backward)', single: false },
    { id: 'gauss_jordan', label: 'Gauss-Jordan', icon: RotateCw, description: 'Eliminación Gauss-Jordan (forma reducida)', single: false },
  ];

  // Determinant calculation methods (match docs: Gauss, Gauss-Jordan, Cramer)
  const determinantMethods = [
    { id: 'sarrus', label: 'Sarrus-Method', icon: Grid3x3Icon, description: 'Cálculo de determinante por método de Sarrus', single: true },
    { id: 'cofactors', label: 'Cofactors-Method', icon: RotateCw, description: 'Cálculo del determinante por expansión de Cofactores', single: true },
    { id: 'cramer', label: 'Cramer', icon: CalcIcon, description: 'Cálculo por regla de Cramer (sólo para sistemas cuadrados)', single: true },
  ];

  const generalOperations = [
    { id: 'graficadora', label: 'Graficadora', icon: LineChart, description: 'Graficadora de funciones', single: true },
    { id: 'derivadas', label: 'Derivadas', icon: Triangle, description: 'Cálculo de derivadas', single: true },
    { id: 'integrales', label: 'Integrales', icon: Triangle, description: 'Cálculo de integrales', single: true },
  ];

  const getOperationsForMode = (mode: InputMode) => {
    if (mode === 'general') return generalOperations;
    if (mode === 'matrix') return matrixOperations;
    if (mode === 'vector') return vectorOperations;
    if (mode === 'reduce') return reduceOperations;
    if (mode === 'determinant') return determinantMethods;
  };

  const currentOperations = getOperationsForMode(inputMode);
  const selectedOperation = currentOperations.find(op => op.id === operation);

  // when operation changes, clear scalar selection unless scalar_mult is active
  useEffect(() => {
    if (operation !== 'scalar_mult') setSelectedScalar(false);
  }, [operation]);

  let needsTwoInputs: boolean;
  if (inputMode === 'reduce') {
    // systems: always need matrix A and vector b
    needsTwoInputs = true;
  } else if (inputMode === 'determinant') {
    // determinant: only matrix A
    needsTwoInputs = false;
  } else {
    needsTwoInputs = !selectedOperation?.single;
  }

  // Render the appropriate inputs inside AnimatePresence to avoid complex nested ternaries in JSX
  const renderInputs = () => {
    if (inputMode === 'general') {
        return (
          <motion.div
            key="general-inputs"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="grid grid-cols-1 gap-6"
          >
            <div>
              {operation === 'graficadora' && <GraphCalculator />}
              {operation === 'derivadas' && <DerivativeInputs />}
              {operation === 'integrales' && <IntegralInputs />}
            </div>
          </motion.div>
        );
      }
    if (inputMode === 'matrix') {
      return (
        <motion.div
          key="matrix-inputs"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6"
        >
          <MatricesSection
            operation={operation}
            manyOps={manyOps}
            manyMatrices={manyMatrices}
            manyCount={manyCount}
            matrixA={matrixA}
            matrixB={matrixB}
            dimensionsA={dimensionsA}
            dimensionsB={dimensionsB}
            selectedMatrixCell={selectedMatrixCell}
            selectedVectorCell={selectedVectorCell}
            selectedScalar={selectedScalar}
            matrixErrorsA={matrixErrorsA}
            matrixErrorsB={matrixErrorsB}
            manyMatricesErrors={manyMatricesErrors}
            setSelectedMatrixCell={setSelectedMatrixCell}
            setSelectedVectorCell={setSelectedVectorCell}
            setSelectedScalar={setSelectedScalar}
            handleMatrixCellChange={handleMatrixCellChange}
            handleManyMatrixCellChange={handleManyMatrixCellChange}
            onDimensionsAChange={(r,c) => { setDimensionsA({ rows: r, cols: c }); const newMatrix = Array(r).fill(0).map(() => Array(c).fill(0)); setMatrixA(newMatrix); setMatrixErrorsA({}); setSelectedMatrixCell(null); }}
            onDimensionsBChange={(r,c) => { setDimensionsB({ rows: r, cols: c }); const newMatrix = Array(r).fill(0).map(() => Array(c).fill(0)); setMatrixB(newMatrix); setMatrixErrorsB({}); setSelectedMatrixCell(null); }}
            onManyDimensionsChange={(idx,r,c) => setManyMatrices((prev) => { const copy = prev.map((m) => m.map((r) => [...r])); const newM = Array(r).fill(0).map(() => Array(c).fill(0)); copy[idx] = newM; return copy; })}
            scalarInput={scalarInput}
            setScalarInput={setScalarInput}
            setScalarError={setScalarError}
            setManyCount={handleManyCountChange}
          />
        </motion.div>
      );
    }

    if (inputMode === 'vector') {
      // Multiplicación escalar
      if (operation === 'scalar_vect') {
        return (
          <motion.div
            key="vector-inputs-scalar"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="grid grid-cols-1 md:grid-cols-2 gap-6"
          >
            <VectorsSection
              vectorA={vectorA}
              vectorB={vectorB}
              dimensionVectorB={dimensionVectorB}
              vectorErrorsB={vectorErrorsB}
              onDimensionVectorBChange={(d) => { setDimensionVectorB(d); const newVector = Array(d).fill(0); setVectorB(newVector); setVectorErrorsB({}); setSelectedVectorCell(null); }}
              dimensionVectorA={dimensionVectorA}
              selectedVectorCell={selectedVectorCell}
              setSelectedVectorCell={setSelectedVectorCell}
              setSelectedMatrixCell={setSelectedMatrixCell}
              setSelectedScalar={setSelectedScalar}
              selectedScalar={selectedScalar}
              handleVectorCellChange={handleVectorCellChange}
              vectorErrorsA={vectorErrorsA}
              onDimensionVectorAChange={(d) => { setDimensionVectorA(d); const newVector = Array(d).fill(0); setVectorA(newVector); setVectorErrorsA({}); setSelectedVectorCell(null); }}
              needsTwoInputs={false}
              showScalar1={true}
              scalarInput1={scalarInput}
              setScalarInput1={setScalarInput}
            />
          </motion.div>
        );
      }

      // Combinación lineal de 2 vectores
      if (operation === 'comb2') {
        return (
          <motion.div
            key="vector-inputs-comb2"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="grid grid-cols-1 md:grid-cols-2 gap-6"
          >
            <VectorsSection
              vectorA={vectorA}
              vectorB={vectorB}
              dimensionVectorA={dimensionVectorA}
              dimensionVectorB={dimensionVectorB}
              selectedVectorCell={selectedVectorCell}
              setSelectedVectorCell={setSelectedVectorCell}
              setSelectedMatrixCell={setSelectedMatrixCell}
              setSelectedScalar={setSelectedScalar}
              selectedScalar={selectedScalar}
              handleVectorCellChange={handleVectorCellChange}
              vectorErrorsA={vectorErrorsA}
              vectorErrorsB={vectorErrorsB}
              onDimensionVectorAChange={(d) => { setDimensionVectorA(d); const newVector = Array(d).fill(0); setVectorA(newVector); setVectorErrorsA({}); setSelectedVectorCell(null); }}
              onDimensionVectorBChange={(d) => { setDimensionVectorB(d); const newVector = Array(d).fill(0); setVectorB(newVector); setVectorErrorsB({}); setSelectedVectorCell(null); }}
              needsTwoInputs={true}
              showScalar1={true}
              showScalar2={true}
              scalarInput1={scalarInput}
              setScalarInput1={setScalarInput}
              scalarInput2={scalarInput2}
              setScalarInput2={setScalarInput2}
            />
          </motion.div>
        );
      }

      // Combinación lineal de 3 vectores
      if (operation === 'comb3') {
        // Por ahora vectorC es igual a vectorB, pero debería tener su propio estado si se requiere
        return (
          <motion.div
            key="vector-inputs-comb3"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="grid grid-cols-1 md:grid-cols-2 gap-6"
          >
            <VectorsSection
              vectorA={vectorA}
              vectorB={vectorB}
              vectorC={vectorC}
              dimensionVectorA={dimensionVectorA}
              dimensionVectorB={dimensionVectorB}
              dimensionVectorC={dimensionVectorC}
              selectedVectorCell={selectedVectorCell}
              setSelectedVectorCell={setSelectedVectorCell}
              setSelectedMatrixCell={setSelectedMatrixCell}
              setSelectedScalar={setSelectedScalar}
              selectedScalar={selectedScalar}
              handleVectorCellChange={handleVectorCellChange}
              vectorErrorsA={vectorErrorsA}
              vectorErrorsB={vectorErrorsB}
              vectorErrorsC={vectorErrorsC}
              onDimensionVectorAChange={(d) => { setDimensionVectorA(d); const newVector = Array(d).fill(0); setVectorA(newVector); setVectorErrorsA({}); setSelectedVectorCell(null); }}
              onDimensionVectorBChange={(d) => { setDimensionVectorB(d); const newVector = Array(d).fill(0); setVectorB(newVector); setVectorErrorsB({}); setSelectedVectorCell(null); }}
              onDimensionVectorC={(d) => { setDimensionVectorC(d); const newVector = Array(d).fill(0); setVectorC(newVector); setVectorErrorsC({}); setSelectedVectorCell(null); }}
              needsTwoInputs={true}
              showScalar1={true}
              showScalar2={true}
              scalarInput1={scalarInput}
              setScalarInput1={setScalarInput}
              scalarInput2={scalarInput2}
              setScalarInput2={setScalarInput2}
            />
          </motion.div>
        );
      }

      // Producto escalar, suma, resta usan el render original
      if (operation === 'linear_combination') {
        // Ax = b: mostrar matriz A y vector b
        return (
          <motion.div
            key="system-equation-inputs"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="grid grid-cols-1 md:grid-cols-2 gap-6"
          >
            <SystemEquationSection
              matrixA={matrixA}
              dimensionsA={dimensionsA}
              vectorB={vectorB}
              dimensionVectorB={dimensionVectorB}
              selectedMatrixCell={selectedMatrixCell}
              selectedVectorCell={selectedVectorCell}
              selectedScalar={selectedScalar}
              matrixErrorsA={matrixErrorsA}
              vectorErrorsB={vectorErrorsB}
              setSelectedMatrixCell={setSelectedMatrixCell}
              setSelectedVectorCell={setSelectedVectorCell}
              setSelectedScalar={setSelectedScalar}
              handleMatrixCellChange={handleMatrixCellChange}
              handleVectorCellChange={handleVectorCellChange}
              onDimensionsAChange={(r,c) => { setDimensionsA({ rows: r, cols: c }); const newMatrix = Array(r).fill(0).map(() => Array(c).fill(0)); setMatrixA(newMatrix); setMatrixErrorsA({}); setSelectedMatrixCell(null); }}
              onDimensionBChange={(d) => { setDimensionVectorB(d); const newVector = Array(d).fill(0); setVectorB(newVector); setVectorErrorsB({}); setSelectedVectorCell(null); }}
            />
          </motion.div>
        );
      }

      return (
        <motion.div
          key="vector-inputs"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6"
        >
          <VectorsSection
            vectorA={vectorA}
            vectorB={vectorB}
            dimensionVectorA={dimensionVectorA}
            dimensionVectorB={dimensionVectorB}
            selectedVectorCell={selectedVectorCell}
            setSelectedVectorCell={setSelectedVectorCell}
            setSelectedMatrixCell={setSelectedMatrixCell}
            setSelectedScalar={setSelectedScalar}
            selectedScalar={selectedScalar}
            handleVectorCellChange={handleVectorCellChange}
            vectorErrorsA={vectorErrorsA}
            vectorErrorsB={vectorErrorsB}
            onDimensionVectorAChange={(d) => { setDimensionVectorA(d); const newVector = Array(d).fill(0); setVectorA(newVector); setVectorErrorsA({}); setSelectedVectorCell(null); }}
            onDimensionVectorBChange={(d) => { setDimensionVectorB(d); const newVector = Array(d).fill(0); setVectorB(newVector); setVectorErrorsB({}); setSelectedVectorCell(null); }}
            needsTwoInputs={needsTwoInputs}
          />
        </motion.div>
      );
    }

    if (inputMode === 'reduce') {
      return (
        <motion.div
          key="reduce-inputs"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6"
        >
          <SystemEquationSection
            matrixA={matrixA}
            dimensionsA={dimensionsA}
            vectorB={vectorB}
            dimensionVectorB={dimensionVectorB}
            selectedMatrixCell={selectedMatrixCell}
            selectedVectorCell={selectedVectorCell}
            selectedScalar={selectedScalar}
            matrixErrorsA={matrixErrorsA}
            vectorErrorsB={vectorErrorsB}
            setSelectedMatrixCell={setSelectedMatrixCell}
            setSelectedVectorCell={setSelectedVectorCell}
            setSelectedScalar={setSelectedScalar}
            handleMatrixCellChange={handleMatrixCellChange}
            handleVectorCellChange={handleVectorCellChange}
            onDimensionsAChange={(r,c) => { setDimensionsA({ rows: r, cols: c }); const newMatrix = Array(r).fill(0).map(() => Array(c).fill(0)); setMatrixA(newMatrix); setMatrixErrorsA({}); setSelectedMatrixCell(null); }}
            onDimensionBChange={(d) => { setDimensionVectorB(d); const newVector = Array(d).fill(0); setVectorB(newVector); setVectorErrorsB({}); setSelectedVectorCell(null); }}
          />
        </motion.div>
      );
    }

    // determinant
    return (
      <motion.div
        key="determinant-inputs"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
        className="grid grid-cols-1 md:grid-cols-1 gap-6"
      >
        <DeterminantSection
          matrixA={matrixA}
          dimensionsA={dimensionsA}
          selectedMatrixCell={selectedMatrixCell}
          matrixErrorsA={matrixErrorsA}
          setSelectedMatrixCell={setSelectedMatrixCell}
          handleMatrixCellChange={handleMatrixCellChange}
          onDimensionsAChange={(r,c) => { setDimensionsA({ rows: r, cols: c }); const newMatrix = Array(r).fill(0).map(() => Array(c).fill(0)); setMatrixA(newMatrix); setSelectedMatrixCell(null); }}
        />
      </motion.div>
    );
  };

  return (
    <div className="min-h-screen relative overflow-hidden p-4 md:p-8">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage: `linear-gradient(rgba(99, 102, 241, 0.4) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(99, 102, 241, 0.4) 1px, transparent 1px)`,
            backgroundSize: '40px 40px',
          }}
          animate={{
            backgroundPosition: ['0px 0px', '40px 40px'],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: 'linear',
          }}
        />

        {/* Glowing orbs */}
        <motion.div
          className="absolute top-20 left-20 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl"
          animate={{
            x: [0, 50, 0],
            y: [0, 30, 0],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
        <motion.div
          className="absolute bottom-20 right-20 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl"
          animate={{
            x: [0, -50, 0],
            y: [0, -30, 0],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: 'easeInOut',
            delay: 1,
          }}
        />
      </div>

      {/* Header */}
      <motion.div
        className="relative z-10 mb-6"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-4 flex items-center justify-between">
          <Button
            onClick={onBack}
            variant="ghost"
            className="text-blue-200 hover:text-blue-100 hover:bg-white/10"
          >
            <ArrowLeft className="mr-2" size={20} />
            Volver
          </Button>
          <div className="flex items-center gap-3">
            <CalcIcon className="text-purple-300" size={24} />
            <h2 className="text-2xl bg-gradient-to-r from-blue-300 to-purple-300 bg-clip-text text-transparent">
              MunguiaCore
            </h2>
          </div>
          <div className="w-24" />
        </div>
      </motion.div>

      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Mode Selector */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
          
        >
            <Tabs 
            value={inputMode} 
            onValueChange={(v) => {
                const mode = v as InputMode;
                setInputMode(mode);
                const ops = getOperationsForMode(mode);
                setOperation(ops[0]?.id ?? ''); // Reset operation to first available for the mode
              setSelectedMatrixCell(null);
              setSelectedVectorCell(null);
              setSelectedScalar(false);
              // Clear previous result cache when switching modes
              setLastResult(null);
              localStorage.removeItem('calc_last_result');
              window.dispatchEvent(new Event('calc:updated'));
            }}
            className="w-full"
          > 

            <TabsList className="grid w-full mx-auto grid-cols-5 backdrop-blur-xl bg-white/5 border border-white/10 h-14 text-white">
              <TabsTrigger 
                value="general" 
                className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-purple-600 text-base"
              >
                <LineChart className="w-5 h-5 mr-2" />
                Calculadora General
              </TabsTrigger>

              <TabsTrigger 
                value="matrix" 
                className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-purple-600 text-base"
              >
                <Grid3x3Icon className="w-5 h-5 mr-2" />
                Matrices
              </TabsTrigger>

              <TabsTrigger 
                value="reduce" 
                className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-purple-600 data-[state=active]:to-pink-600 text-base"
              >
                <Triangle className="w-5 h-5 mr-2" />
                Sistema de Ecuaciones
              </TabsTrigger>

              <TabsTrigger 
                value="determinant" 
                className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-purple-600 text-base"
              >
                <Triangle className="w-5 h-5 mr-2" />
                Determinantes
              </TabsTrigger>

              <TabsTrigger 
                value="vector" 
                className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-purple-600 data-[state=active]:to-pink-600 text-base"
              >
                <Triangle className="w-5 h-5 mr-2" />
                Vectores
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Inputs */}
          <div className="lg:col-span-2 space-y-6">
            {/* Operation Selector */}
            <OperationSelector
              operations={currentOperations}
              selectedOperation={operation}
              onSelectOperation={setOperation}
            />

            {/* Inputs */}
            <AnimatePresence mode="wait">{renderInputs()}</AnimatePresence>

            {/* scalar-multiplication UI is handled inside the animated inputs branch above */}

            {/* Result Preview - hide for general (Graph) mode */}
            {inputMode !== 'general' && (
              <motion.div
                className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <div className="flex items-center justify-between mb-4">
                  <Button
                    className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                    onClick={handleCalculate}
                  >
                    {loading ? 'Calculando...' : 'Calcular'}
                  </Button>
                </div>
                <div className="backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl p-6 min-h-32 flex items-center justify-center">
                  <div className="w-full">
                    {submitError && <p className="text-red-400 mb-2">{submitError}</p>}
                    <p className="text-purple-300/50 text-center mb-3">
                      {selectedOperation ? `Operación seleccionada: ${selectedOperation.description}` : 'Selecciona una operación y presiona calcular'}
                    </p>

                    <ResultSection lastResult={lastResult} />
                  </div>
                </div>
              </motion.div>
            )}

            {/* end Left Column */}
          </div>

          {/* Right Column - Keyboard (hidden in general/Graph mode) */}
          {inputMode !== 'general' && (
            <div className="lg:col-span-1">
                <DigitalKeyboard
                  onKeyPress={handleKeyPress}
                  // scalar has highest priority for keyboard input
                  selectedCell={selectedScalar ? { scalar: true } : (selectedVectorCell ?? selectedMatrixCell)}
                />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}