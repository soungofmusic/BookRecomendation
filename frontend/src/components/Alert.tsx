// src/components/Alert.tsx
import React from 'react';

interface AlertProps {
  variant?: 'default' | 'destructive';
  children: React.ReactNode;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({ 
  variant = 'default',
  children,
  className = ''
}) => {
  const baseStyles = "rounded-lg p-4 mb-4 text-sm";
  const variantStyles = {
    default: "bg-blue-100 text-blue-800 border border-blue-200",
    destructive: "bg-red-100 text-red-800 border border-red-200"
  };

  return (
    <div className={`${baseStyles} ${variantStyles[variant]} ${className}`} role="alert">
      {children}
    </div>
  );
};

export const AlertDescription: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <div className="font-medium">{children}</div>;
};