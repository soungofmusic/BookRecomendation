import React from 'react';

export const AnimatedBook: React.FC = () => {
  return (
    <div className="w-36 h-48 perspective-1000 mx-auto">
      <div className="relative w-full h-full animate-float">
        {/* Book cover with gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-500 rounded-r-lg rounded-l-sm shadow-xl">
          {/* Book spine with enhanced details */}
          <div className="absolute left-0 top-0 w-4 h-full bg-blue-700 rounded-l-sm">
            <div className="h-full w-full bg-gradient-to-r from-blue-800 to-blue-700">
              {/* Spine decorative elements */}
              <div className="absolute inset-0 flex flex-col justify-between py-4">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className="w-full h-0.5 bg-blue-400/20"
                  />
                ))}
              </div>
            </div>
          </div>
          
          {/* Cover title placeholder */}
          <div className="absolute inset-0 flex flex-col items-center justify-center p-4">
            <div className="w-16 h-1 bg-blue-300/30 rounded-full mb-2" />
            <div className="w-12 h-1 bg-blue-300/20 rounded-full" />
          </div>
          
          {/* Animated pages with more realistic effect */}
          {[...Array(7)].map((_, i) => (
            <div
              key={i}
              className="absolute inset-0 bg-gradient-to-r from-gray-50 to-white rounded-r-sm origin-left transform-gpu animate-turnPage"
              style={{
                animationDelay: `${i * 0.15}s`,
                transformStyle: 'preserve-3d',
                backfaceVisibility: 'hidden',
              }}
            >
              {/* Page content with more varied lines */}
              <div className="p-4 space-y-2">
                {[...Array(5)].map((_, j) => (
                  <div
                    key={j}
                    className="h-0.5 bg-gray-200/80 rounded-full"
                    style={{ 
                      width: `${Math.random() * 20 + 60}%`,
                      opacity: 0.5 + Math.random() * 0.5
                    }}
                  />
                ))}
              </div>
              {/* Page edge shadow */}
              <div className="absolute right-0 top-0 bottom-0 w-1 bg-gradient-to-l from-gray-200 to-transparent" />
            </div>
          ))}
        </div>
        
        {/* Book shadow */}
        <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 w-4/5 h-4 bg-blue-500/10 rounded-full blur-sm animate-shadow" />
      </div>
    </div>
  );
};

export default AnimatedBook;