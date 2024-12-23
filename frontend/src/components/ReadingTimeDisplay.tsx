import React from 'react';

interface ReadingTimeProps {
  readingTime: {
    slow: { hours: number | null; minutes: number | null };
    average: { hours: number | null; minutes: number | null };
    fast: { hours: number | null; minutes: number | null };
  };
  pageCount?: number;  // Add this prop
}

const ReadingTimeDisplay = ({ readingTime, pageCount }: ReadingTimeProps) => {
  if (!readingTime?.average?.hours && !readingTime?.average?.minutes) {
    return null;
  }

  const formatTime = (hours: number | null, minutes: number | null) => {
    if (hours === null || minutes === null) return 'N/A';
    return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
  };

  return (
    <div className="bg-white/90 rounded-lg p-4 shadow-sm">
      <div className="mb-2 flex justify-between items-baseline">
        <h4 className="font-medium text-gray-800">📚 Reading Time Estimate</h4>
        {pageCount && (
          <span className="text-xs text-gray-500">
            {pageCount} pages
          </span>
        )}
      </div>
      
      <div className="space-y-2 text-sm">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Detailed reading:</span>
          <span className="font-medium">{formatTime(readingTime.slow.hours, readingTime.slow.minutes)}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Average pace:</span>
          <span className="font-medium">{formatTime(readingTime.average.hours, readingTime.average.minutes)}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Speed reading:</span>
          <span className="font-medium">{formatTime(readingTime.fast.hours, readingTime.fast.minutes)}</span>
        </div>
      </div>
      
      <div className="mt-3 text-xs text-gray-500">
        *Estimates based on genre and format
      </div>
    </div>
  );
};

export default ReadingTimeDisplay;