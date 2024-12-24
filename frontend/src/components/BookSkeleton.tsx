import React from 'react';

const BookSkeleton = () => {
  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4">
        {/* Book Cover and Details Section */}
        <div className="flex gap-4">
          {/* Cover Skeleton */}
          <div className="flex-shrink-0 w-24 h-36 bg-skeleton-gradient bg-skeleton animate-skeletonLoading rounded" />

          {/* Details Skeleton */}
          <div className="flex-1">
            {/* Title */}
            <div className="h-6 bg-skeleton-gradient bg-skeleton animate-skeletonLoading rounded w-3/4 mb-2" />
            {/* Author */}
            <div className="h-4 bg-skeleton-gradient bg-skeleton animate-skeletonLoading rounded w-1/2 mb-2" />
            {/* Year */}
            <div className="h-4 bg-skeleton-gradient bg-skeleton animate-skeletonLoading rounded w-1/4" />
            {/* Score bar */}
            <div className="mt-2">
              <div className="h-2 bg-skeleton-gradient bg-skeleton animate-skeletonLoading rounded-full w-full" />
            </div>
          </div>
        </div>

        {/* Match Explanation Skeleton */}
        <div className="mt-4 p-3 rounded-lg">
          <div className="h-4 bg-skeleton-gradient bg-skeleton animate-skeletonLoading rounded w-1/3 mb-2" />
          <div className="space-y-2">
            <div className="h-3 bg-skeleton-gradient bg-skeleton animate-skeletonLoading rounded w-full" />
            <div className="h-3 bg-skeleton-gradient bg-skeleton animate-skeletonLoading rounded w-5/6" />
          </div>
        </div>

        {/* Why Read Skeleton */}
        <div className="mt-4 p-3 rounded-lg">
          <div className="h-4 bg-skeleton-gradient bg-skeleton animate-skeletonLoading rounded w-1/3 mb-2" />
          <div className="space-y-2">
            <div className="h-3 bg-skeleton-gradient bg-skeleton animate-skeletonLoading rounded w-full" />
            <div className="h-3 bg-skeleton-gradient bg-skeleton animate-skeletonLoading rounded w-4/5" />
          </div>
        </div>

        {/* Genres Skeleton */}
        <div className="mt-3 flex gap-1">
          {[1, 2, 3].map((i) => (
            <div 
              key={i} 
              className="h-6 w-16 bg-skeleton-gradient bg-skeleton animate-skeletonLoading rounded"
            />
          ))}
        </div>

        {/* Library Finder Skeleton */}
        <div className="mt-4">
          <div className="h-10 bg-skeleton-gradient bg-skeleton animate-skeletonLoading rounded w-full" />
        </div>
      </div>
    </div>
  );
};

export default BookSkeleton;