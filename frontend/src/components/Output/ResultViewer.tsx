import React, { useEffect, useState } from 'react'

type ApiResult = {
  input?: any
  steps?: string[] | any[]
  result?: any
  properties?: any
}

export default function ResultViewer() {
  const [result, setResult] = useState<ApiResult | null>(null)

  useEffect(() => {
    function update() {
      const raw = localStorage.getItem('calc_last_result')
      if (!raw) {
        setResult(null)
        return
      }
      try {
        setResult(JSON.parse(raw))
      } catch (e) {
        console.error('Failed to parse cached result, clearing cache', e)
        localStorage.removeItem('calc_last_result')
        setResult(null)
      }
    }
    update()
    window.addEventListener('calc:updated', update)
    return () => window.removeEventListener('calc:updated', update)
  }, [])

  if (!result) return <div className="result-viewer">No hay resultados aún.</div>

  return (
    <div className="result-viewer">
      <h2>Resultado</h2>
      <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(result.result, null, 2)}</pre>

      <h3>Pasos</h3>
      {Array.isArray(result.steps) ? (
        <ol>
          {result.steps.map((s, i) => (
            <li key={i}>{typeof s === 'string' ? s : JSON.stringify(s)}</li>
          ))}
        </ol>
      ) : (
        <pre>{JSON.stringify(result.steps, null, 2)}</pre>
      )}

      {result.properties && (
        <div>
          <h3>Propiedades</h3>
          <pre>{JSON.stringify(result.properties, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
