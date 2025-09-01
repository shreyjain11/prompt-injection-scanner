'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function SiteHeader() {
  const pathname = usePathname();
  const isCLI = pathname?.startsWith('/commands');

  const base = 'inline-flex items-center justify-center text-sm font-medium px-4 py-2 rounded-full transition-colors transition-transform duration-150 border';
  const active = 'bg-black text-white border-black';
  const inactive = 'bg-white text-black border-black hover:bg-neutral-100';

  return (
    <header>
      <div className="mx-auto max-w-6xl px-6 h-14 flex items-center justify-between">
        <Link href="/" className="font-extrabold tracking-tight">PromptScan</Link>
        <nav className="flex items-center gap-2">
          <Link href="/" aria-current={!isCLI ? 'page' : undefined} className={`${base} ${!isCLI ? active : inactive}`}>Home</Link>
          <Link href="/commands" aria-current={isCLI ? 'page' : undefined} className={`${base} ${isCLI ? active : inactive}`}>CLI</Link>
        </nav>
      </div>
    </header>
  );
}


