  import { motion, useScroll, useTransform } from 'framer-motion';
import { Calculator, Grid3x3, Triangle, ArrowRight, Brain, Shield, TrendingUp } from 'lucide-react';
import { Button } from './ui/button';
import { useRef } from 'react';


interface LandingPageProps {
  onStart: () => void;
  onOpenNumeric?: () => void;
}

export function LandingPage({ onStart, onOpenNumeric }: LandingPageProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"]
  });

  const y = useTransform(scrollYProgress, [0, 1], [0, 100]);
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);

  return (
    <div ref={containerRef} className="relative min-h-screen overflow-hidden">
      {/* Sophisticated background */}
      <div className="absolute inset-0">
        {/* Gradient mesh */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-blue-950/50 to-slate-950" />
        
        {/* Subtle grid */}
        <div 
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(rgba(99, 102, 241, 0.5) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(99, 102, 241, 0.5) 1px, transparent 1px)`,
            backgroundSize: '60px 60px',
          }}
        />

        {/* Ambient light effects */}
        <motion.div
          className="absolute top-0 right-0 w-[600px] h-[600px] bg-blue-500/10 rounded-full blur-[120px]"
          animate={{
            scale: [1, 1.1, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
        <motion.div
          className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-purple-500/10 rounded-full blur-[120px]"
          animate={{
            scale: [1.1, 1, 1.1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: 'easeInOut',
            delay: 2,
          }}
        />
      </div>

      {/* Main content */}
      <div className="relative z-10 min-h-screen flex flex-col">
        {/* Header */}
        <motion.header
          className="px-8 py-6"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-2">
                <Calculator className="text-blue-400" size={24} />
              </div>
              <span className="text-xl text-white">Munguia Core</span>
            </div>
            <nav className="hidden md:flex items-center gap-8 text-sm text-gray-400">
              <a href="https://github.com/SteMt323/AlgebraLineal.git" target='blank' className="hover:text-white transition-colors">Repositorio</a>
              
            </nav>
          </div>
        </motion.header>

        {/* Hero Section */}
        <div className="flex-1 flex items-center px-8 py-20">
          <div className="max-w-7xl mx-auto w-full">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
              {/* Left Column - Content */}
              <motion.div
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8 }}
                style={{ y, opacity }}
              >
                
                

                {/* Main Heading */}
                <motion.h1
                  className="text-5xl md:text-7xl mb-6 text-white tracking-tight"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                >
                  &lt;Álgebra Lineal
                  <span className="block mt-2 bg-gradient-to-r from-blue-400 via-purple-400 to-blue-400 bg-clip-text text-transparent">
                    &nbsp;&nbsp;&nbsp;Munguia Core&gt;
                  </span>
                </motion.h1>

                {/* Description */}
                <motion.p
                  className="text-xl text-gray-400 mb-8 leading-relaxed max-w-xl"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                >
                  Calculadora del curso de Algebra Lineal. Resuelve y aprende paso a paso.
                </motion.p>

                {/* CTA Buttons */}
                <motion.div
                  className="flex flex-wrap gap-4"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                >
                  <Button
                    onClick={onStart}
                    size="lg"
                    className="group relative bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white border-0 px-8 py-6 text-lg shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 transition-all"
                  >
                    <span className="flex items-center gap-3">
                      Calculadora Algebra
                    </span>
                  </Button>
                  <Button
                    onClick={() => { if (typeof onOpenNumeric === 'function') onOpenNumeric(); }}
                    variant="outline"
                    size="lg"
                    className="backdrop-blur-xl bg-white/5 border-white/10 text-white hover:bg-white/10 px-8 py-6 text-lg"
                  >
                    Métodos Numéricos
                  </Button>
                </motion.div>

                {/* Stats */}
                <motion.div
                  className="grid grid-cols-3 gap-8 mt-12 pt-12 border-t border-white/10"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.6 }}
                >
                  {[
                    { value: '8+', label: 'Operaciones' },
                    { value: '6x6', label: 'Matrices' },
                    { value: '100%', label: 'Precisión' },
                  ].map((stat, i) => (
                    <div key={i}>
                      <div className="text-3xl text-white mb-1">{stat.value}</div>
                      <div className="text-sm text-gray-400">{stat.label}</div>
                    </div>
                  ))}
                </motion.div>
              </motion.div>

              {/* Right Column - Visual */}
              <motion.div
                className="relative hidden lg:block"
                initial={{ opacity: 0, x: 30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8, delay: 0.2 }}
              >
                {/* Main Card */}
                <div className="relative">
                  {/* Glow effect */}
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20 blur-3xl rounded-3xl" />
                  
                  {/* Calculator Preview */}
                  <div className="relative backdrop-blur-2xl bg-gradient-to-br from-white/10 to-white/5 border border-white/20 rounded-2xl p-8 shadow-2xl">
                    {/* Matrix visualization */}
                    <div className="space-y-6">
                      <div className="flex items-center gap-3 mb-6">
                        <Grid3x3 className="text-blue-400" size={24} />
                        <span className="text-white">Vista Previa</span>
                      </div>
                      
                      {/* Sample Matrix */}
                      <div className="backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl p-6">
                        <div className="grid grid-cols-3 gap-3">
                          {[...Array(9)].map((_, i) => (
                            <motion.div
                              key={i}
                              className="backdrop-blur-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/20 rounded-lg h-16 flex items-center justify-center text-white"
                              initial={{ opacity: 0, scale: 0.8 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ delay: 0.8 + i * 0.05 }}
                            >
                              {Math.floor(Math.random() * 10)}
                            </motion.div>
                          ))}
                        </div>
                      </div>

                      {/* Operation indicator */}
                      <div className="flex items-center justify-center">
                        <div className="backdrop-blur-lg bg-purple-500/20 border border-purple-400/30 rounded-lg px-4 py-2">
                          <span className="text-purple-300">det(A) = 42</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Floating elements */}
                  <motion.div
                    className="absolute -top-6 -right-6 backdrop-blur-xl bg-white/10 border border-white/20 rounded-xl p-4"
                    animate={{ y: [0, -10, 0] }}
                    transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                  >
                    <Triangle className="text-purple-400" size={24} />
                  </motion.div>
                  
                  <motion.div
                    className="absolute -bottom-6 -left-6 backdrop-blur-xl bg-white/10 border border-white/20 rounded-xl p-4"
                    animate={{ y: [0, 10, 0] }}
                    transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
                  >
                    <Calculator className="text-blue-400" size={24} />
                  </motion.div>
                </div>
              </motion.div>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <motion.div
          className="px-8 pb-20"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                {
                  icon: Grid3x3,
                  title: 'Operaciones Matriciales',
                  description: 'Suma, resta, multiplicación, determinantes, inversas y más.',
                  color: 'blue',
                },
                {
                  icon: Triangle,
                  title: 'Cálculo Vectorial',
                  description: 'Operaciones escenciales, productos escalares.',
                  color: 'purple',
                },
                {
                  icon: Brain,
                  title: 'Resolución Paso a Paso',
                  description: 'Aprende paso a paso la resolución de problemas.',
                  color: 'pink',
                },
              ].map((feature, i) => (
                <motion.div
                  key={i}
                  className="group backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-8 hover:bg-white/10 hover:border-white/20 transition-all duration-300"
                  whileHover={{ y: -4 }}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.8 + i * 0.1 }}
                >
                  <div className={`inline-flex backdrop-blur-lg bg-${feature.color}-500/10 border border-${feature.color}-400/20 rounded-xl p-3 mb-4`}>
                    <feature.icon className={`text-${feature.color}-300`} size={24} />
                  </div>
                  <h3 className="text-xl text-white mb-3">{feature.title}</h3>
                  <p className="text-gray-400 leading-relaxed">{feature.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Footer */}
        <motion.footer
          className="px-8 py-6 border-t border-white/10"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
        >
          <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-gray-500">
            <p>© 2025 Calculadora. Programa desarrollado en el curso de Algebra Lineal UAM.</p>
            <div className="flex gap-6">
              <a href="#" className="hover:text-gray-300 transition-colors">Términos</a>
              <a href="#" className="hover:text-gray-300 transition-colors">Privacidad</a>
              <a href="#" className="hover:text-gray-300 transition-colors">Contacto</a>
            </div>
          </div>
        </motion.footer>
      </div>
    </div>
  );
}