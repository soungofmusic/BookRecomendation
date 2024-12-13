import React from 'react';

const LoadingBook: React.FC = () => {
  return (
    <div className="w-full h-32 relative animate-pulse">
      {/* Book spine */}
      <div className="absolute left-0 w-4 h-full bg-gradient-to-r from-blue-400 to-blue-500 
                    rounded-l transform-gpu rotate-3d-spine shadow-lg" />
      
      {/* Book cover */}
      <div className="absolute left-4 w-full h-full bg-gradient-to-br from-blue-500 to-purple-500 
                    rounded-r transform-gpu rotate-3d-cover shadow-xl">
        {/* Loading lines */}
        <div className="p-4 space-y-2">
          <div className="h-4 bg-white/20 rounded w-3/4 animate-shimmer" />
          <div className="h-3 bg-white/20 rounded w-1/2 animate-shimmer" />
        </div>
      </div>
    </div>
  );
};

export default LoadingBook;