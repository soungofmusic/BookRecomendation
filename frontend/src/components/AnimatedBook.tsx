import React from 'react';

export const AnimatedBook: React.FC = () => {
  return (
    <div className="w-32 h-40 perspective-1000 mx-auto">
      <div className="relative w-full h-full animate-float">
        {/* Book cover */}
        <div className="absolute inset-0 bg-blue-500 rounded-r-lg rounded-l-sm shadow-lg">
          {/* Book spine details */}
          <div className="absolute left-0 top-0 w-3 h-full bg-blue-600 rounded-l-sm">
            <div className="h-full w-full bg-gradient-to-r from-blue-700 to-blue-600"></div>
          </div>
          
          {/* Animated pages */}
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="absolute inset-0 bg-white rounded-r-sm origin-left transform-gpu animate-turnPage"
              style={{
                animationDelay: `${i * 0.1}s`,
                transformStyle: 'preserve-3d',
              }}
            >
              {/* Page content lines */}
              <div className="p-4 space-y-2">
                {[...Array(4)].map((_, j) => (
                  <div
                    key={j}
                    className="h-1 bg-gray-200 rounded-full"
                    style={{ width: `${80 - j * 15}%` }}
                  ></div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AnimatedBook;