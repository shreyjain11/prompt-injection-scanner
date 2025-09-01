'use client';
import * as React from 'react';
import { cn } from '@/lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className, ...props }, ref) => {
  return (
    <input ref={ref} className={cn('w-full border border-black rounded-full px-4 py-2 text-sm bg-white text-black focus:outline-none focus:ring-2 focus:ring-black/50', className)} {...props} />
  );
});
Input.displayName = 'Input';


