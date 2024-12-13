import React, { useEffect, useRef } from 'react';

interface AnimatedContainerProps {
  children: React.ReactNode;
  delay?: number;
}

const AnimatedContainer: React.FC<AnimatedContainerProps> = ({ 
  children, 
  delay = 0 
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.style.opacity = '0';
    container.style.transform = 'translateY(20px)';

    setTimeout(() => {
      container.style.transition = 'all 0.5s ease-out';
      container.style.opacity = '1';
      container.style.transform = 'translateY(0)';
    }, delay);
  }, [delay]);

  return (
    <div ref={containerRef} className="transform">
      {children}
    </div>
  );
};

export default AnimatedContainer;