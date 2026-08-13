import React from 'react';
import katex from 'katex';

interface Props {
  children: string;
  className?: string;
}

export function BlockMath({ children, className }: Props) {
  const html = React.useMemo(() => {
    try {
      return katex.renderToString(children || '', { throwOnError: false, displayMode: true });
    } catch (e) {
      return children;
    }
  }, [children]);

  return <div className={className} dangerouslySetInnerHTML={{ __html: html }} />;
}

export default BlockMath;
