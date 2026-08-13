import React from 'react';

interface Props {
  latex?: string;
  className?: string;
}

export default function MathQuillRender({ latex = '', className }: Props) {
  const ref = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    let mounted = true;
    const loadAndRender = async () => {
      // Ensure MathQuill is available (load if necessary)
      if (!(window as any).MathQuill) {
        // load jQuery
        const jQueryScript = document.createElement('script');
        jQueryScript.src = 'https://code.jquery.com/jquery-3.6.0.min.js';
        document.head.appendChild(jQueryScript);
        await new Promise((r) => (jQueryScript.onload = r));

        const mathQuillCSS = document.createElement('link');
        mathQuillCSS.rel = 'stylesheet';
        mathQuillCSS.href = 'https://cdn.jsdelivr.net/npm/mathquill@0.10.1/build/mathquill.css';
        document.head.appendChild(mathQuillCSS);

        const mq = document.createElement('script');
        mq.src = 'https://cdn.jsdelivr.net/npm/mathquill@0.10.1/build/mathquill.min.js';
        document.head.appendChild(mq);
        await new Promise((r) => (mq.onload = r));
      }

      try {
        const MQ = (window as any).MathQuill.getInterface(2);
        if (ref.current) {
          // Clear previous content
          ref.current.innerHTML = '';
          // Static render
          const span = document.createElement('span');
          ref.current.appendChild(span);
          const sm = MQ.StaticMath(span);
          sm.latex(latex || '');
        }
      } catch (e) {
        // fallback: just set text
        if (ref.current) ref.current.textContent = latex;
      }
    };

    if (mounted) loadAndRender();
    return () => {
      mounted = false;
    };
  }, [latex]);

  return <div ref={ref} className={className} />;
}
