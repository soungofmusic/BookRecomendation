import React from 'react';

interface BookSkeletonProps {
  className?: string;
}

const BookSkeleton: React.FC<BookSkeletonProps> = ({ className = '' }) => {
  return (
    <div 
      className={`bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition-shadow duration-200 ${className}`}
      role="status"
      aria-label="Loading book recommendation"
    >
      <div className="p-4 space-y-4">
        {/* Book Cover and Details Section */}
        <div className="flex gap-4">
          {/* Cover Skeleton */}
          <div 
            className="flex-shrink-0 w-24 h-36 bg-gradient-to-b from-gray-200 to-gray-300 
                     dark:from-gray-700 dark:to-gray-600 animate-pulse rounded"
            role="progressbar"
            aria-label="Loading book cover"
          />

          {/* Details Skeleton */}
          <div className="flex-1 space-y-2">
            {/* Title */}
            <div 
              className="h-6 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 
                       dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 
                       animate-pulse rounded w-3/4"
              role="progressbar"
              aria-label="Loading book title"
            />
            
            {/* Author */}
            <div 
              className="h-4 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 
                       dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 
                       animate-pulse rounded w-1/2"
              role="progressbar"
              aria-label="Loading author name"
            />
            
            {/* Year */}
            <div 
              className="h-4 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 
                       dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 
                       animate-pulse rounded w-1/4"
              role="progressbar"
              aria-label="Loading publication year"
            />
            
            {/* Score bar */}
            <div className="mt-2">
              <div 
                className="h-2 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 
                         dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 
                         animate-pulse rounded-full w-full"
                role="progressbar"
                aria-label="Loading similarity score"
              />
            </div>
          </div>
        </div>

        {/* Match Explanation Skeleton */}
        <div 
          className="p-3 bg-gradient-to-br from-indigo-50 to-purple-50 
                   dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg"
          role="progressbar"
          aria-label="Loading match explanation"
        >
          <div 
            className="h-4 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 
                     dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 
                     animate-pulse rounded w-1/3 mb-2"
          />
          <div className="space-y-2">
            <div 
              className="h-3 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 
                       dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 
                       animate-pulse rounded w-full"
            />
            <div 
              className="h-3 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 
                       dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 
                       animate-pulse rounded w-5/6"
            />
          </div>
        </div>

        {/* Why Read Skeleton */}
        <div 
          className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
          role="progressbar"
          aria-label="Loading reading recommendation"
        >
          <div 
            className="h-4 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 
                     dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 
                     animate-pulse rounded w-1/3 mb-2"
          />
          <div className="space-y-2">
            <div 
              className="h-3 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 
                       dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 
                       animate-pulse rounded w-full"
            />
            <div 
              className="h-3 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 
                       dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 
                       animate-pulse rounded w-4/5"
            />
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
              className="h-6 w-16 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 
                       dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 
                       animate-pulse rounded"
            />
          ))}
        </div>

        {/* Library Finder Skeleton */}
        <div 
          className="mt-2"
          role="progressbar"
          aria-label="Loading library finder"
        >
          <div 
            className="h-10 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 
                     dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 
                     animate-pulse rounded w-full"
          />
        </div>
      </div>
    </div>
  );
};

export default React.memo(BookSkeleton);