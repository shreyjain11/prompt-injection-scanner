'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ThemeToggle } from '@/components/ui/theme-toggle';

export default function SiteHeader() {
  const pathname = usePathname();
  const isCLI = pathname?.startsWith('/commands');

  const base = 'inline-flex items-center justify-center text-sm font-medium px-4 py-2 rounded-full transition-colors transition-transform duration-150 border';
  const active = 'bg-black text-white border-black dark:bg-white dark:text-black dark:border-white';
  const inactive = 'bg-white text-black border-black hover:bg-neutral-100 dark:bg-gray-800 dark:text-white dark:border-white dark:hover:bg-gray-700';

  return (
    <header className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-black/10 dark:border-white/10">
      <div className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between">
        <Link href="/" className="font-extrabold tracking-tight text-black dark:text-white">PromptScan</Link>
        <div className="flex items-center gap-3">
          <nav className="flex items-center gap-2">
            <Link href="/" aria-current={!isCLI ? 'page' : undefined} className={`${base} ${!isCLI ? active : inactive}`}>Home</Link>
            <Link href="/commands" aria-current={isCLI ? 'page' : undefined} className={`${base} ${isCLI ? active : inactive}`}>CLI</Link>
          </nav>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}


