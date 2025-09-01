'use client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { CheckCircle } from 'lucide-react';
import { useState } from 'react';

export default function CommandsPage() {
  const [copied, setCopied] = useState<string | null>(null);

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopied(label);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <main className="bg-gray-50 dark:bg-gray-900 min-h-screen">
      <section className="pt-24 pb-16">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <div className="inline-block border border-gray-300 dark:border-gray-600 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm px-4 py-2 text-xs font-semibold text-gray-700 dark:text-gray-300 rounded-full">CLI Reference</div>
          <h1 className="mt-6 text-6xl md:text-7xl font-extrabold leading-[1.05] tracking-tight bg-gradient-to-br from-black to-gray-600 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">PromptScan CLI</h1>
          <p className="mt-4 text-lg max-w-3xl mx-auto text-gray-700 dark:text-gray-300 leading-relaxed">Install with pipx or pip, then run scans locally or on any public GitHub repo URL.</p>
          
          {/* Copy notification */}
          {copied && (
            <div className="mt-4 inline-flex items-center gap-2 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 px-4 py-2 rounded-full text-sm font-medium">
              <CheckCircle className="w-4 h-4" />
              Copied {copied}!
            </div>
          )}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-16">
        <div className="grid grid-cols-1 gap-6">
          <Card title="Installation">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Code>pipx install prompt-scan</Code>
                <button 
                  onClick={() => copyToClipboard('pipx install prompt-scan', 'install command')}
                  className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 px-2 py-1 rounded-full hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
                >
                  Copy
                </button>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Recommended: Install with pipx for isolated environment.</p>
              <p className="text-sm text-gray-500 dark:text-gray-500">Alternative: <Code>pip install --user prompt-scan</Code></p>
            </div>
          </Card>

          <Card title="Quick start">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Code>prompt-scan https://github.com/owner/repo</Code>
                <button 
                  onClick={() => copyToClipboard('prompt-scan https://github.com/owner/repo', 'quick start')}
                  className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 px-2 py-1 rounded-full hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
                >
                  Copy
                </button>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Paste a public GitHub URL directly. The tool fetches the repo ZIP and scans it.</p>
            </div>
          </Card>

          <Card title="Scan a local folder">
            <Code>prompt-scan scan ./path/to/project</Code>
            <p className="text-sm mt-2">Scans locally, respecting .gitignore and language filters.</p>
          </Card>

          <Card title="Output formats">
            <ul className="list-disc pl-6 space-y-2 text-sm">
              <li><Code>--output cli</Code> Human-readable (default)</li>
              <li><Code>--output json</Code> JSON to stdout (pipe to files or tools)</li>
              <li><span className="opacity-60">--output html</span> Coming soon</li>
            </ul>
            <p className="text-sm mt-2">Example: <Code>prompt-scan &lt;url&gt; --output json &gt; results.json</Code></p>
          </Card>

          <Card title="Filtering & thresholds">
            <ul className="list-disc pl-6 space-y-2 text-sm">
              <li><Code>-s high -s critical</Code> Only include selected severities.</li>
              <li><Code>--min-confidence 0.4</Code> Suppress low-confidence findings.</li>
              <li><Code>--strict</Code> Stricter filtering (higher thresholds, doc/test suppression).</li>
            </ul>
          </Card>

          <Card title="Performance & UX">
            <ul className="list-disc pl-6 space-y-2 text-sm">
              <li><Code>--parallel 8</Code> Increase workers for faster scans.</li>
              <li><Code>--no-progress</Code> Clean stdout (useful with JSON or CI).</li>
              <li><Code>--no-cache</Code> Disable caching for fresh scans.</li>
              <li><Code>--verbose</Code> Extra logs for debugging.</li>
            </ul>
          </Card>

          <Card title="Index a repository">
            <Code>prompt-scan index ./path --out index.json</Code>
            <p className="text-sm mt-2">Create a JSON index of scannable files (useful for cache/debug).</p>
          </Card>

          <Card title="List rules">
            <Code>prompt-scan rules</Code>
            <p className="text-sm mt-2">Show available rules and languages loaded from YAML.</p>
          </Card>

          <Card title="Benchmark & tuning">
            <ul className="list-disc pl-6 space-y-2 text-sm">
              <li><Code>prompt-scan bench --manifest src/benchmarks/manifest.yaml</Code> Run suite.</li>
              <li><Code>prompt-scan bench --tune</Code> Auto-suggest confidence thresholds (beta).</li>
              <li>Constraints: <Code>--min-precision 0.9 --min-recall 0.6</Code></li>
            </ul>
          </Card>

          <Card title="Examples">
            <ul className="list-disc pl-6 space-y-2 text-sm">
              <li>Scan a popular repo: <Code>prompt-scan https://github.com/octocat/Hello-World</Code></li>
              <li>Local scan with filters: <Code>prompt-scan scan . -s high -s critical --min-confidence 0.3</Code></li>
            </ul>
          </Card>
        </div>
      </section>
    </main>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-black dark:text-white p-8 rounded-2xl shadow-sm">
      <div className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">{title}</div>
      <div>{children}</div>
    </div>
  );
}

function Code({ children }: { children: React.ReactNode }) {
  return <code className="bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-1 rounded-lg font-mono text-sm border border-gray-200 dark:border-gray-600">{children}</code>;
}


