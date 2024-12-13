import React from 'react';

const BookLoader: React.FC = () => {
  return (
    <div className="relative w-48 h-64 mx-auto perspective-1000">
      {/* Book spine */}
      <div className="absolute left-0 w-8 h-full bg-gradient-to-r from-blue-600 to-blue-700 
                    rounded-l-lg transform-gpu animate-pulse shadow-lg" />
      
      {/* Book pages */}
      {[...Array(5)].map((_, i) => (
        <div
          key={i}
          className="absolute left-8 w-full h-full bg-white rounded-r-lg shadow-md
                     origin-left transform-gpu"
          style={{
            animation: `turnPage 1.5s ease-in-out ${i * 0.15}s infinite`,
            transformOrigin: 'left',
            zIndex: 5 - i,
          }}
        />
      ))}
      
      {/* Book cover */}
      <div className="absolute left-8 w-full h-full bg-gradient-to-br from-blue-500 to-purple-600 
                    rounded-r-lg shadow-xl">
        <div className="p-6 space-y-3">
          <div className="h-4 bg-white/30 rounded animate-pulse" />
          <div className="h-3 bg-white/20 rounded w-3/4 animate-pulse" />
          <div className="h-3 bg-white/20 rounded w-1/2 animate-pulse" />
        </div>
      </div>
    </div>
  );
};

export default BookLoader;