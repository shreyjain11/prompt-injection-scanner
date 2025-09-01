'use client';
import * as React from 'react';
import { cn } from '@/lib/utils';

type Variant = 'default' | 'ghost' | 'outline';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(({ className, variant = 'default', ...props }, ref) => {
  const base = 'inline-flex items-center justify-center text-sm font-medium px-4 py-2 transition-colors transition-transform duration-150';
  const rounded = 'rounded-full';
  const styles: Record<Variant, string> = {
    default: 'bg-black text-white border border-black hover:brightness-95 hover:-translate-y-[1px]',
    ghost: 'bg-transparent text-black border border-black hover:bg-black hover:text-white hover:-translate-y-[1px]',
    outline: 'bg-white text-black border border-black hover:bg-neutral-100 hover:-translate-y-[1px]',
  };
  return (
    <button ref={ref} className={cn(base, rounded, styles[variant], className)} {...props} />
  );
});
Button.displayName = 'Button';


