import React from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Calculator as CalcIcon, Triangle, Zap } from 'lucide-react';
import { Button } from './ui/button';
import { Tabs, TabsList, TabsTrigger } from './ui/tabs';
import { ErrorAcumuladoInputs } from './inputs/ErrorAcumuladoInputs';
import { ErrorAbsRelInputs } from './inputs/ErrorAbsRelInputs';
import PropagationErrorInputs from './inputs/PropagationErrorInputs';
import BisectionInputs from './inputs/BisectionInputs';
import FalsePositionInputs from './inputs/FalsePositionInputs';
import SecantInputs from './inputs/SecantInputs';
import NewtonRaphsonInputs from './inputs/NewtonRaphsonInputs';
import { OperationSelector } from './OperationSelector';

interface NumericMethodsProps {
  onBack?: () => void;
}

export function NumericMethods({ onBack }: NumericMethodsProps) {
  const [selectedOp, setSelectedOp] = React.useState<string>('acumulado');

  const errorOperations = [
    { id: 'acumulado', label: 'Error Acumulado', icon: CalcIcon, description: 'Cálculo del error acumulado por iteraciones' },
    { id: 'absoluto_relativo', label: 'Error Absoluto y Relativo', icon: Triangle, description: 'Cálculo de error absoluto y relativo' },
    { id: 'propagacion', label: 'Propagación de Error', icon: Zap, description: 'Propagación de errores mediante derivada' },
  ];
  const closedOperations = [
    { id: 'biseccion', label: 'Método de Bisección', icon: CalcIcon, description: 'Búsqueda de raíz por bisección' },
    { id: 'false_position', label: 'Método de Falsa Posición', icon: CalcIcon, description: 'Búsqueda de raíz por falsa posición' },
    
  ];
  const openOperations = [
    { id: 'newton_raphson', label: 'Newton-Raphson', icon: CalcIcon, description: 'Método de Newton-Raphson' },
    { id: 'secante', label: 'Método de Secante', icon: CalcIcon, description: 'Método de la secante' },
  ];
  const [topTab, setTopTab] = React.useState<string>('calculo_errores');
  return (
    <div className="min-h-screen relative overflow-hidden p-4 md:p-8">
      <div className="absolute inset-0 opacity-5" style={{
        backgroundImage: `linear-gradient(rgba(99, 102, 241, 0.4) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(99, 102, 241, 0.4) 1px, transparent 1px)`,
        backgroundSize: '40px 40px',
      }} />

      <motion.div className="relative z-10 mb-6" initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-4 flex items-center justify-between">
          <Button onClick={onBack} variant="ghost" className="text-blue-200 hover:text-blue-100 hover:bg-white/10">
            <ArrowLeft className="mr-2" size={20} />
            Volver
          </Button>
          <div className="flex items-center gap-3">
            <CalcIcon className="text-purple-300" size={24} />
            <h2 className="text-2xl bg-gradient-to-r from-blue-300 to-purple-300 bg-clip-text text-transparent">Métodos Numéricos</h2>
          </div>
          <div className="w-24" />
        </div>
      </motion.div>

      <div className="relative z-10 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-3 space-y-6">
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6">
              <div className="text-sm font-semibold text-blue-200 mb-4">Calculadora de Métodos Numéricos</div>

              <div className="mb-4">
                <Tabs value={topTab} onValueChange={(v) => setTopTab(v)} className="w-full">
                  <TabsList className="grid w-full mx-auto grid-cols-3 backdrop-blur-xl bg-white/5 border border-white/10 h-12 text-white">
                      <TabsTrigger value="calculo_errores" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-purple-600 text-base">
                        Cálculo de errores
                      </TabsTrigger>
                      <TabsTrigger value="metodos_cerrados" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-purple-600 text-base">
                        Métodos Cerrados
                      </TabsTrigger>
                      <TabsTrigger value="metodos_abiertos" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-purple-600 text-base">
                        Métodos Abiertos
                      </TabsTrigger>
                    </TabsList>
                </Tabs>
              </div>

              <div className="mb-4">
                {topTab === 'calculo_errores' && (
                  <OperationSelector operations={errorOperations} selectedOperation={selectedOp} onSelectOperation={(id) => setSelectedOp(id)} />
                )}

                {topTab === 'metodos_cerrados' && (
                  <OperationSelector operations={closedOperations} selectedOperation={selectedOp} onSelectOperation={(id) => setSelectedOp(id)} />
                )}
                {topTab === 'metodos_abiertos' && (
                  <OperationSelector operations={openOperations} selectedOperation={selectedOp} onSelectOperation={(id) => setSelectedOp(id)} />
                )}
              </div>

              {/* Render selected operation inputs */}
              <div className="mt-4">
                {selectedOp === 'acumulado' && (
                  <ErrorAcumuladoInputs onCalculate={(data) => { console.log('Error Acumulado', data); }} />
                )}

                {selectedOp === 'absoluto_relativo' && (
                  <ErrorAbsRelInputs onCalculate={(data) => { console.log('Error Abs/Rel', data); }} />
                )}

                {selectedOp === 'propagacion' && (
                  <React.Suspense fallback={<div>Cargando...</div>}>
                    <PropagationErrorInputs />
                  </React.Suspense>
                )}

                {selectedOp === 'biseccion' && (
                  <React.Suspense fallback={<div>Cargando...</div>}>
                    <BisectionInputs />
                  </React.Suspense>
                )}

                {selectedOp === 'false_position' && (
                  <React.Suspense fallback={<div>Cargando...</div>}>
                    <FalsePositionInputs />
                  </React.Suspense>
                )}
                {selectedOp === 'secante' && (
                  <React.Suspense fallback={<div>Cargando...</div>}>
                    <SecantInputs />
                  </React.Suspense>
                )}
                {selectedOp === 'newton_raphson' && (
                  <React.Suspense fallback={<div>Cargando...</div>}>
                    <NewtonRaphsonInputs />
                  </React.Suspense>
                )}
              </div>

              
            </motion.div>
          </div>

          {/* Right column removed for NumericMethods (no digital keyboard) */}
        </div>
      </div>
    </div>
  );
}

export default NumericMethods;
