//import React from 'react'
//import './App.css'
//import MatrixOperateForm from './components/MatrixOperateForm'
//import DeterminantForm from './components/DeterminantForm'
//import ResultViewer from './components/ResultViewer'
//
//export default function App() {
//  return (
//    <div className="app-container">
//      <h1>Calculadora Álgebra (Frontend - TypeScript)</h1>
//      <div className="forms">
//        <MatrixOperateForm />
//        <DeterminantForm />
//      </div>
//      <ResultViewer />
//    </div>
//  )
//}

import { useState } from 'react';
import { LandingPage } from './components/LandingPage';
import { AlgebraicMethods } from './components/AlgebraicMethods';
import NumericMethods from './components/NumericMethods';

export default function App() {
  const [showCalculator, setShowCalculator] = useState(false);
  const [showNumeric, setShowNumeric] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900">
      {!showCalculator && !showNumeric ? (
        <LandingPage onStart={() => setShowCalculator(true)} onOpenNumeric={() => setShowNumeric(true)} />
      ) : showCalculator ? (
        <AlgebraicMethods onBack={() => setShowCalculator(false)} />
      ) : (
        <NumericMethods onBack={() => setShowNumeric(false)} />
      )}
    </div>
  );
}
