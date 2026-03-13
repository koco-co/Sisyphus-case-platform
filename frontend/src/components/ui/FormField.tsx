'use client';

import type { ReactNode } from 'react';

interface FormFieldProps {
  label: string;
  required?: boolean;
  error?: string;
  children: ReactNode;
  className?: string;
}

export function FormField({
  label,
  required = false,
  error,
  children,
  className = '',
}: FormFieldProps) {
  return (
    <div className={`mb-4 ${className}`}>
      <label className="block text-[12.5px] font-medium text-text2 mb-1.5">
        {label}
        {required && <span className="text-red ml-0.5">*</span>}
      </label>
      {children}
      {error && <p className="text-[11px] text-red mt-1">{error}</p>}
    </div>
  );
}
