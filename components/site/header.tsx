'use client';

import { usePathname } from 'next/navigation';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { Navbar, NavBody, NavItems } from '@/components/ui/resizable-navbar';

export default function SiteHeader() {
  const pathname = usePathname();

  const navItems = [
    { name: "Home", link: "/" },
    { name: "CLI", link: "/commands" },
  ];

  return (
    <Navbar>
      <NavBody>
        <div className="flex items-center">
          <a href="/" className="font-extrabold tracking-tight text-black dark:text-white text-lg">PromptScan</a>
        </div>
        <NavItems items={navItems} />
        <div className="flex items-center">
          <ThemeToggle />
        </div>
      </NavBody>
    </Navbar>
  );
}


