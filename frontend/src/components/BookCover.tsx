import React, { useState } from 'react';

interface BookCoverProps {
  id: string;
  title: string;
  size?: 'small' | 'medium' | 'large';
  className?: string;
}

const BookCover: React.FC<BookCoverProps> = ({ 
  id, 
  title, 
  size = 'medium',
  className = '' 
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  const coverSizes = {
    small: { width: 'w-24', height: 'h-36' },
    medium: { width: 'w-32', height: 'h-48' },
    large: { width: 'w-40', height: 'h-60' }
  };

  const getCoverUrl = (bookId: string, size: string) => {
    const workId = bookId.replace('/works/', '');
    const sizeFlag = size === 'large' ? 'L' : size === 'medium' ? 'M' : 'S';
    return `https://covers.openlibrary.org/b/olid/${workId}-${sizeFlag}.jpg`;
  };

  // Create gradient background for fallback
  const gradientColors = [
    ['from-blue-500 to-blue-600', 'text-white'],
    ['from-purple-500 to-purple-600', 'text-white'],
    ['from-green-500 to-green-600', 'text-white'],
    ['from-rose-500 to-rose-600', 'text-white'],
  ];

  // Use title's first character to consistently select a gradient
  const colorIndex = title.charCodeAt(0) % gradientColors.length;
  const [gradientColor, textColor] = gradientColors[colorIndex];

  return (
    <div className={`relative ${coverSizes[size].width} ${coverSizes[size].height} ${className}`}>
      {/* Loading Skeleton */}
      {isLoading && !hasError && (
        <div className="absolute inset-0 bg-gray-200 rounded-lg animate-pulse">
          <div className="absolute inset-0 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 animate-shimmer" />
        </div>
      )}

      {/* Actual Cover Image */}
      <img
        src={getCoverUrl(id, size)}
        alt={title}
        className={`
          absolute inset-0 w-full h-full object-cover rounded-lg shadow-md
          transition-opacity duration-300
          ${isLoading ? 'opacity-0' : 'opacity-100'}
        `}
        loading="lazy"
        onLoad={() => setIsLoading(false)}
        onError={() => {
          setIsLoading(false);
          setHasError(true);
        }}
      />

      {/* Fallback Design */}
      {hasError && (
        <div className={`
          absolute inset-0 rounded-lg shadow-md overflow-hidden
          bg-gradient-to-br ${gradientColor}
        `}>
          <div className="absolute inset-0 flex flex-col items-center justify-center p-4">
            <span className={`text-4xl font-bold ${textColor}`}>
              {title[0]}
            </span>
            <span className={`text-xs mt-2 text-center ${textColor} opacity-90`}>
              {title.length > 20 ? `${title.slice(0, 20)}...` : title}
            </span>
          </div>
          {/* Decorative elements */}
          <div className="absolute top-0 right-0 w-16 h-16 -mr-8 -mt-8 bg-white/10 rounded-full" />
          <div className="absolute bottom-0 left-0 w-12 h-12 -ml-6 -mb-6 bg-white/10 rounded-full" />
        </div>
      )}
    </div>
  );
};

export default BookCover;