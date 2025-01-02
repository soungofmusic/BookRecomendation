// components/ClearButton.tsx
import React from 'react';

interface ClearButtonProps {
  onClick: () => void;
  disabled?: boolean;
}

const ClearButton: React.FC<ClearButtonProps> = ({ onClick, disabled }) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg 
                 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600
                 text-gray-600 dark:text-gray-300 
                 transition-all duration-200 ease-in-out
                 disabled:opacity-50 disabled:cursor-not-allowed
                 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400
                 transform hover:scale-105 active:scale-95"
      aria-label="Clear all books"
    >
      <span className="text-lg font-medium leading-none mr-1">×</span>
      <span className="text-sm">Clear All</span>
    </button>
  );
};

export default ClearButton;