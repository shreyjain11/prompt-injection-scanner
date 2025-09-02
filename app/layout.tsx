import './globals.css';
import { Inter, Space_Grotesk } from 'next/font/google';
import { ThemeProvider } from 'next-themes';
import type { Metadata } from 'next';
import SiteHeader from '@/components/site/header';

export const metadata: Metadata = {
  title: 'PromptScan - Prompt Injection Scanner',
  description: 'Scan public GitHub repos for prompt injection vulnerabilities. Open source and free forever.',
  icons: {
    icon: '/favicon.ico',
  },
};

const inter = Inter({ subsets: ['latin'] });
const spaceGrotesk = Space_Grotesk({ subsets: ['latin'], variable: '--font-grotesk' });

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`bg-white text-black ${inter.className} ${spaceGrotesk.variable}`}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem={true} disableTransitionOnChange>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}


