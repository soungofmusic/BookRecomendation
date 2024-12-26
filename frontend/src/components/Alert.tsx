// components/Alert.tsx
import React from 'react';

interface AlertProps {
  variant?: 'default' | 'destructive';
  children: React.ReactNode;
  className?: string;
}

interface AlertDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({ 
  children, 
  className = '', 
  variant = 'default' 
}) => {
  const baseStyles = "relative w-full rounded-lg border p-4";
  const variantStyles = variant === 'destructive' 
    ? "border-red-500/50 bg-red-50 text-red-700 dark:border-red-500/30 dark:bg-red-900/30 dark:text-red-200"
    : "border-gray-200 dark:border-gray-800";

  return (
    <div className={`${baseStyles} ${variantStyles} ${className}`}>
      {children}
    </div>
  );
};

export const AlertDescription: React.FC<AlertDescriptionProps> = ({ 
  children,
  className = ''
}) => {
  return (
    <div className={`text-sm ${className}`}>
      {children}
    </div>
  );
};