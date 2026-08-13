import axios from 'axios'

const API_BASE = (import.meta.env.VITE_API_BASE as string) || 'http://localhost:8000'

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
})

export type MatrixPayload = {
  operation?: string
  A?: number[][]
  B?: number[][]
  scalar?: number
  matrices?: number[][][]
}

export async function matrixOperate(payload: MatrixPayload) {
  const res = await client.post('api/v1/matrix/operate', payload)
  return res.data
}

export async function matrixDeterminant(payload: { method: string; A: number[][] }) {
  const res = await client.post('api/v1/matrix/determinant', payload)
  return res.data
}

export async function matrixReduce(payload: { method: string; A?: number[][]; b?: number[]; Ab?: number[][]; options?: any }) {
  const res = await client.post('api/v1/matrix/reduce', payload)
  return res.data
}

export async function vectorOperate(payload: { operation: string; vectors: Record<string, number[]>; scalars?: Record<string, number>; options?: any }) {
  const res = await client.post('api/v1/vectors/operate', payload)
  return res.data
}

export async function vectorCombination(payload: { A: number[][]; b: number[]; options?: any }) {
  const res = await client.post('api/v1/vectors/combination', payload)
  return res.data
}

export async function errorAcumulado(payload: {
  initial_amount: string
  iterations: number
  mode: 'trunc' | 'round'
  rate: string
  approx_decimals: number
  interest_display_decimals?: number
}) {
  const res = await client.post('api/v1/numeric/error-accumulation', payload)
  return res.data
}

export async function errorAbsRel(payload: { true_value: string; approx_value: string; decimals_display?: number }) {
  const res = await client.post('api/v1/numeric/abs-rel-error', payload)
  return res.data
}

export async function errorPropagation(payload: { function_latex: string; x0: string; delta_x: string; angle_mode?: string }) {
  const res = await client.post('api/v1/numeric/propagation-error', payload)
  return res.data
}

export async function bisectionMethod(payload: { function_latex: string; xi: number; xu: number; tolerance: number; max_iter?: number }) {
  const res = await client.post('api/v1/numeric/bisection-method', payload)
  return res.data
}

export async function falsePositionMethod(payload: { function_latex: string; xi: number; xu: number; tolerance: number; max_iterations?: number }) {
  const res = await client.post('api/v1/numeric/false-position', payload)
  return res.data
}

export async function newtonRaphsonMethod(payload: { function_latex: string; x0: number; tolerance: number; max_iterations?: number; derivate_mode?: string }) {
  const res = await client.post('api/v1/numeric/newton-raphson', payload)
  return res.data
}

export async function secantMethod(payload: { function_latex: string; x0: number; x1: number; tolerance: number; max_iterations?: number; angle_mode?: string }) {
  const res = await client.post('api/v1/numeric/secant', payload)
  return res.data
}

export async function derivativeMethod(payload: { latex: string; variable?: string }) {
  const body: any = { function_latex: payload.latex };
  // variable is optional; backend infers variable from latex
  const res = await client.post('api/v1/calculus/derivate', body);
  return res.data;
}

export async function integralMethod(payload: { latex: string; variable?: string }) {
  const body: any = { function_latex: payload.latex };
  const res = await client.post('api/v1/calculus/integral', body);
  return res.data;
}

export default client
