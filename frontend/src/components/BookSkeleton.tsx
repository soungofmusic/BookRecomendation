import React from 'react';

interface BookSkeletonProps {
  className?: string;
}

const BookSkeleton: React.FC<BookSkeletonProps> = ({ className = '' }) => {
  return (
    <div 
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg hover:shadow-xl 
                transition-all duration-300 animate-fadeIn ${className}`}
      role="status"
      aria-label="Loading book recommendation"
    >
      <div className="p-4 space-y-4">
        {/* Book Cover and Details Section */}
        <div className="flex gap-4">
          {/* Cover Skeleton */}
          <div 
            className="flex-shrink-0 w-24 h-36 bg-skeleton-gradient bg-skeleton 
                     animate-skeletonLoading rounded overflow-hidden"
            role="progressbar"
            aria-label="Loading book cover"
          >
            <div className="w-full h-full bg-shimmer-gradient animate-shimmer" />
          </div>

          {/* Details Skeleton */}
          <div className="flex-1 space-y-2">
            {/* Title */}
            <div 
              className="h-6 bg-skeleton-gradient bg-skeleton animate-skeletonLoading 
                       rounded w-3/4 overflow-hidden"
              role="progressbar"
              aria-label="Loading book title"
            >
              <div className="w-full h-full bg-shimmer-gradient animate-shimmer" />
            </div>
            
            {/* Author */}
            <div 
              className="h-4 bg-skeleton-gradient bg-skeleton animate-skeletonLoading 
                       rounded w-1/2 overflow-hidden"
              role="progressbar"
              aria-label="Loading author name"
            >
              <div className="w-full h-full bg-shimmer-gradient animate-shimmer" />
            </div>
            
            {/* Year */}
            <div 
              className="h-4 bg-skeleton-gradient bg-skeleton animate-skeletonLoading 
                       rounded w-1/4 overflow-hidden"
              role="progressbar"
              aria-label="Loading publication year"
            >
              <div className="w-full h-full bg-shimmer-gradient animate-shimmer" />
            </div>
            
            {/* Score bar */}
            <div className="mt-2">
              <div 
                className="h-2 bg-skeleton-gradient bg-skeleton animate-skeletonLoading 
                         rounded-full w-full overflow-hidden"
                role="progressbar"
                aria-label="Loading similarity score"
              >
                <div className="w-full h-full bg-shimmer-gradient animate-shimmer" />
              </div>
            </div>
          </div>
        </div>

        {/* Match Explanation Skeleton */}
        <div 
          className="p-3 bg-gradient-to-br from-indigo-50/80 to-purple-50/80 
                   dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg"
          role="progressbar"
          aria-label="Loading match explanation"
        >
          <div className="space-y-2">
            <div 
              className="h-4 bg-skeleton-gradient bg-skeleton animate-skeletonLoading 
                       rounded w-1/3 mb-2 overflow-hidden"
            >
              <div className="w-full h-full bg-shimmer-gradient animate-shimmer" />
            </div>
            <div 
              className="h-3 bg-skeleton-gradient bg-skeleton animate-skeletonLoading 
                       rounded w-full overflow-hidden"
            >
              <div className="w-full h-full bg-shimmer-gradient animate-shimmer" />
            </div>
            <div 
              className="h-3 bg-skeleton-gradient bg-skeleton animate-skeletonLoading 
                       rounded w-5/6 overflow-hidden"
            >
              <div className="w-full h-full bg-shimmer-gradient animate-shimmer" />
            </div>
          </div>
        </div>

        {/* Why Read Skeleton */}
        <div 
          className="p-3 bg-gray-50/80 dark:bg-gray-700/30 rounded-lg"
          role="progressbar"
          aria-label="Loading reading recommendation"
        >
          <div className="space-y-2">
            <div 
              className="h-4 bg-skeleton-gradient bg-skeleton animate-skeletonLoading 
                       rounded w-1/3 mb-2 overflow-hidden"
            >
              <div className="w-full h-full bg-shimmer-gradient animate-shimmer" />
            </div>
            <div 
              className="h-3 bg-skeleton-gradient bg-skeleton animate-skeletonLoading 
                       rounded w-full overflow-hidden"
            >
              <div className="w-full h-full bg-shimmer-gradient animate-shimmer" />
            </div>
            <div 
              className="h-3 bg-skeleton-gradient bg-skeleton animate-skeletonLoading 
                       rounded w-4/5 overflow-hidden"
            >
              <div className="w-full h-full bg-shimmer-gradient animate-shimmer" />
            </div>
          </div>
        </div>

        {/* Genres Skeleton */}
        <div 
          className="flex flex-wrap gap-2"
          role="progressbar"
          aria-label="Loading genre tags"
        >
          {Array.from({ length: 3 }).map((_, i) => (
            <div 
              key={i}
              className="h-6 w-16 bg-skeleton-gradient bg-skeleton animate-skeletonLoading 
                       rounded overflow-hidden"
            >
              <div className="w-full h-full bg-shimmer-gradient animate-shimmer" />
            </div>
          ))}
        </div>

        {/* Library Finder Skeleton */}
        <div 
          className="mt-2"
          role="progressbar"
          aria-label="Loading library finder"
        >
          <div 
            className="h-10 bg-skeleton-gradient bg-skeleton animate-skeletonLoading 
                     rounded w-full overflow-hidden"
          >
            <div className="w-full h-full bg-shimmer-gradient animate-shimmer" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default React.memo(BookSkeleton);