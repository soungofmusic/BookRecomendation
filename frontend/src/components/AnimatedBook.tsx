import React from 'react';

export const AnimatedBook: React.FC = () => {
  return (
    <div className="w-36 h-48 perspective-1000 mx-auto">
      <div className="relative w-full h-full animate-float">
        {/* Enhanced outline wrapper with multiple layers */}
        <div className="absolute -inset-1 bg-blue-400 rounded-r-lg rounded-l-sm blur-[1px] opacity-50" />
        <div className="absolute -inset-0.5 bg-blue-300 rounded-r-lg rounded-l-sm opacity-60" />
        
        {/* Book cover with enhanced gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600 via-blue-500 to-indigo-500 rounded-r-lg rounded-l-sm shadow-xl">
          {/* Enhanced book spine with stronger colors */}
          <div className="absolute left-0 top-0 w-4 h-full bg-blue-800 rounded-l-sm">
            <div className="h-full w-full bg-gradient-to-r from-blue-900 to-blue-800">
              {/* Enhanced spine decorative elements */}
              <div className="absolute inset-0 flex flex-col justify-between py-4">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className="w-full h-0.5 bg-blue-300/40"
                  />
                ))}
              </div>
            </div>
          </div>
          
          {/* Enhanced cover title placeholder */}
          <div className="absolute inset-0 flex flex-col items-center justify-center p-4">
            <div className="w-16 h-1 bg-blue-200/50 rounded-full mb-2" />
            <div className="w-12 h-1 bg-blue-200/40 rounded-full" />
          </div>
          
          {/* Enhanced animated pages */}
          {[...Array(7)].map((_, i) => (
            <div
              key={i}
              className="absolute inset-0 bg-gradient-to-r from-gray-50 to-white rounded-r-sm origin-left transform-gpu animate-turnPage shadow-lg"
              style={{
                animationDelay: `${i * 0.15}s`,
                transformStyle: 'preserve-3d',
                backfaceVisibility: 'hidden',
              }}
            >
              {/* Enhanced page content with darker lines */}
              <div className="p-4 space-y-2">
                {[...Array(5)].map((_, j) => (
                  <div
                    key={j}
                    className="h-0.5 bg-gray-300 rounded-full"
                    style={{ 
                      width: `${Math.random() * 20 + 60}%`,
                      opacity: 0.7 + Math.random() * 0.3
                    }}
                  />
                ))}
              </div>
              {/* Enhanced page edge shadow */}
              <div className="absolute right-0 top-0 bottom-0 w-1 bg-gradient-to-l from-gray-300 to-transparent" />
            </div>
          ))}
        </div>
        
        {/* Enhanced book shadow */}
        <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 w-4/5 h-4 bg-blue-500/20 rounded-full blur-sm animate-shadow" />
      </div>
    </div>
  );
};

export default AnimatedBook;