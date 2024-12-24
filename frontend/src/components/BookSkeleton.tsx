import React from 'react';

const BookSkeleton = () => {
  return (
    <div className="bg-white rounded-lg shadow animate-pulse">
      <div className="p-4">
        <div className="flex gap-4">
          {/* Book Cover Skeleton */}
          <div className="flex-shrink-0 w-24 h-36 bg-gray-200 rounded" />

          {/* Book Details Skeleton */}
          <div className="flex-1">
            <div className="h-6 bg-gray-200 rounded w-3/4 mb-2" />
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
            <div className="h-4 bg-gray-200 rounded w-1/4" />
            <div className="mt-2">
              <div className="h-2 bg-gray-200 rounded-full w-full" />
            </div>
          </div>
        </div>

        {/* Match Explanation Skeleton */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-2" />
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 rounded w-full" />
            <div className="h-3 bg-gray-200 rounded w-5/6" />
          </div>
        </div>

        {/* Why Read Section Skeleton */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-2" />
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 rounded w-full" />
            <div className="h-3 bg-gray-200 rounded w-4/5" />
          </div>
        </div>

        {/* Genres Skeleton */}
        <div className="mt-3 flex flex-wrap gap-1">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-6 bg-gray-200 rounded w-16" />
          ))}
        </div>
      </div>
    </div>
  );
};

export default BookSkeleton;