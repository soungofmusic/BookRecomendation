import React from 'react';

interface GlowingButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
}

export const GlowingButton: React.FC<GlowingButtonProps> = ({
  children,
  onClick,
  disabled = false,
  loading = false,
  type = 'button',
  className = ''
}) => {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`
        relative w-full mt-6 px-6 py-3 
        rounded-lg font-medium text-white
        transition-all duration-300
        ${disabled 
          ? 'bg-gray-400 cursor-not-allowed' 
          : 'bg-gradient-to-r from-blue-500 via-blue-600 to-blue-500 animate-shimmerButton'
        }
        ${!disabled && !loading && 'hover:animate-buttonGlow hover:scale-105'}
        overflow-hidden
        ${className}
      `}
    >
      {loading ? (
        <div className="flex items-center justify-center space-x-2">
          <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
          <span>Finding Books...</span>
        </div>
      ) : (
        <span className="relative z-10">{children}</span>
      )}
      
      {/* Glow effect overlay */}
      {!disabled && !loading && (
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-20 animate-shimmer" />
      )}
    </button>
  );
};

export default GlowingButton;