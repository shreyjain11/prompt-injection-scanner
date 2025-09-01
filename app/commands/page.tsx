'use client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function CommandsPage() {
  return (
    <main>
      <section>
        <div className="mx-auto max-w-6xl px-6 py-16 text-center">
          <div className="inline-block border border-black px-3 py-1 text-xs font-semibold">CLI Reference</div>
          <h1 className="mt-4 text-5xl md:text-6xl font-extrabold leading-[1.05] tracking-tight">PromptScan CLI</h1>
          <p className="mt-3 text-base max-w-2xl mx-auto">Install with pipx or pip, then run scans locally or on any public GitHub repo URL.</p>
          <div className="mt-6 flex items-center justify-center gap-3">
            <Button onClick={() => navigator.clipboard.writeText('pipx install prompt-scan')}>pipx install prompt-scan</Button>
            <Button variant="outline" onClick={() => navigator.clipboard.writeText('prompt-scan https://github.com/owner/repo')}>Copy quick start</Button>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-16">
        <div className="grid grid-cols-1 gap-6">
          <Card title="Installation">
            <ol className="list-decimal pl-6 space-y-2 text-sm">
              <li>Install with pipx (recommended): <Code>pipx install prompt-scan</Code></li>
              <li>Alternatively with pip (user): <Code>pip install --user prompt-scan</Code></li>
              <li>Verify install: <Code>prompt-scan --version</Code></li>
            </ol>
            <p className="text-sm mt-2">If <Code>prompt-scan</Code> is not found, ensure your PATH includes pipx binaries (run <Code>pipx ensurepath</Code> then restart the terminal).</p>
          </Card>

          <Card title="Quick start">
            <Code>prompt-scan https://github.com/owner/repo</Code>
            <p className="text-sm mt-2">Paste a public GitHub URL directly. The tool fetches the repo ZIP and scans it.</p>
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
    <div className="border border-black bg-white text-black p-6 rounded-2xl">
      <div className="text-md font-semibold">{title}</div>
      <div className="mt-2">{children}</div>
    </div>
  );
}

function Code({ children }: { children: React.ReactNode }) {
  return <code className="bg-black text-white px-2 py-1 rounded-full">{children}</code>;
}


