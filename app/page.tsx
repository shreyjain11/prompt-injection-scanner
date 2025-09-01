'use client';

import { useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Shield, Github, Search, Brain, ShieldCheck, Terminal } from 'lucide-react';

type Finding = {
  severity?: string;
  rule_id?: string;
  id?: string;
  message?: string;
  line?: number | string;
  line_no?: number | string;
  confidence?: number;
};

type ResultItem = {
  file_path: string;
  findings: Finding[];
  language?: string;
};

type ScanPayload = {
  summary?: {
    total_files?: number;
    scanned_files?: number;
    total_findings?: number;
    scan_duration?: number;
  };
  results?: ResultItem[];
};

export default function HomePage() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ScanPayload | null>(null);

  const rows = useMemo(() => {
    const r: Array<{ file: string; severity: string; message: string; line: string; confidence?: number }> = [];
    console.log('Processing data:', data); // Debug log
    for (const item of data?.results || []) {
      console.log('Processing item:', item); // Debug log
      for (const f of item.findings || []) {
        console.log('Processing finding:', f); // Debug log
        r.push({
          file: item.file_path,
          severity: (f.severity || 'unknown').toUpperCase(),
          message: f.message || '',
          line: String(f.line ?? f.line_no ?? ''),
          confidence: typeof f.confidence === 'number' ? f.confidence : undefined,
        });
      }
    }
    console.log('Final rows:', r); // Debug log
    return r;
  }, [data]);

  const bySeverity = useMemo(() => {
    const g: Record<string, typeof rows> = {} as any;
    for (const x of rows) { (g[x.severity] ||= []).push(x); }
    return g;
  }, [rows]);

  async function scan() {
    if (!url) return;
    setLoading(true); setError(null); setData(null);
    const apiBase = (process.env.NEXT_PUBLIC_API_BASE || process.env.API_BASE || '').replace(/\/$/, '');

    async function tryRequest(endpoint: string, init?: RequestInit) {
      const res = await fetch(endpoint, init);
      const contentType = res.headers.get('content-type') || '';
      const text = await res.text();
      if (!contentType.includes('application/json')) {
        throw new Error(`API returned non-JSON (status ${res.status}).`);
      }
      let json: any;
      try { json = JSON.parse(text); } catch {
        throw new Error('Invalid JSON from API.');
      }
      if (!res.ok) {
        throw new Error(json?.error || `Request failed (${res.status})`);
      }
      return json as ScanPayload;
    }

    try {
      if (apiBase && !/^https?:\/\//i.test(apiBase)) {
        throw new Error('NEXT_PUBLIC_API_BASE must include protocol, e.g., https://your-app.vercel.app');
      }

      const attempts: Array<{ url: string; init?: RequestInit }> = [];
      if (apiBase) {
        attempts.push({ url: '/api/proxy-scan', init: { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }) } });
        attempts.push({ url: `/api/proxy-scan?url=${encodeURIComponent(url)}` });
      }
      attempts.push({ url: '/api/scan', init: { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }) } });
      attempts.push({ url: `/api/scan?url=${encodeURIComponent(url)}` });
      attempts.push({ url: '/api/scan/', init: { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }) } });
      attempts.push({ url: `/api/scan/?url=${encodeURIComponent(url)}` });
      if (apiBase) {
        const base = apiBase.replace(/\/$/, '');
        attempts.push({ url: `${base}/api/scan`, init: { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }) } });
        attempts.push({ url: `${base}/api/scan?url=${encodeURIComponent(url)}` });
        attempts.push({ url: `${base}/api/scan/`, init: { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }) } });
        attempts.push({ url: `${base}/api/scan/?url=${encodeURIComponent(url)}` });
      }

      let lastError: any = null;
      for (const a of attempts) {
        try {
          const json = await tryRequest(a.url, a.init);
          console.log('API Response:', json); // Debug log
          setData(json);
          return;
        } catch (e: any) { lastError = e; }
      }
      throw lastError || new Error('All scan endpoints failed');
    } catch (e: any) {
      const hint = 'Check your deployed API and set NEXT_PUBLIC_API_BASE (e.g., https://your-app.vercel.app).';
      setError(`${String(e.message || e)} ${hint}`);
    } finally { setLoading(false); }
  }

  return (
    <main>
      {/* Hero: black on white */}
      <section>
        <div className="mx-auto max-w-6xl px-6 py-16 text-center">
          <div className="inline-block border border-black px-3 py-1 text-xs font-semibold">Powered by heuristics</div>
          <h1 className="mt-4 text-6xl font-extrabold leading-[1.05] tracking-tight">PromptScan</h1>
          <p className="mt-3 text-base max-w-2xl mx-auto">Paste a public GitHub URL and get an incredibly accurate report of potential prompt injection risks.</p>
          <div className="mt-6 flex items-center justify-center gap-3">
            <a href="#scan" className="inline-flex items-center justify-center text-sm font-medium px-4 py-2 rounded-full bg-black text-white border border-black hover:brightness-95">Get Started</a>
            <a href="https://github.com" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 text-sm font-medium px-4 py-2 rounded-full bg-white text-black border border-black hover:bg-neutral-100"><Github className="w-4 h-4"/> GitHub</a>
          </div>
        </div>
      </section>

      {/* Scanner input on white card */}
      <section id="scan" className="mx-auto max-w-6xl px-6 py-10">
        <div className="border border-black bg-white text-black p-6 rounded-2xl">
          <div className="text-lg font-semibold flex items-center gap-2"><Shield className="w-4 h-4"/> Scan a Repository</div>
          <div className="mt-4 flex gap-3">
            <Input value={url} onChange={e => setUrl(e.target.value)} placeholder="https://github.com/owner/repo" />
            <Button onClick={scan}>Scan</Button>
          </div>
          {error && <div className="mt-3 border border-black p-3">Error: {error}</div>}
          {loading && (
            <div className="mt-3 flex items-center gap-3">
              <span className="inline-block h-4 w-4 border-2 border-black border-t-transparent animate-spin" />
              <span>Scanning…</span>
            </div>
          )}
        </div>
      </section>

      {/* Results */}
      <section className="mx-auto max-w-6xl px-6 pb-16">
        <div className="grid grid-cols-1 gap-6">
          {/* Summary card */}
          <div className="border border-black bg-white text-black p-6 rounded-2xl">
            <div className="text-md font-semibold uppercase">Summary</div>
            <div className="mt-2">
              {data?.summary ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <Stat label="Files" value={`${data.summary.scanned_files ?? 0}/${data.summary.total_files ?? 0}`} />
                  <Stat label="Findings" value={`${data.summary.total_findings ?? 0}`} />
                  <Stat label="Duration" value={`${data.summary.scan_duration ?? 0}s`} />
                  <Stat label="Status" value={loading ? 'Scanning' : data ? 'Complete' : 'Idle'} />
                </div>
              ) : (
                <div className="text-sm">No results yet. Paste a GitHub URL and run a scan.</div>
              )}
            </div>
          </div>

          {/* Findings grouped by severity */}
          <div className="border border-black bg-white text-black p-6 rounded-2xl">
            <div className="text-md font-semibold uppercase">Findings</div>
            {!rows.length && <div className="mt-2 text-sm">No findings.</div>}
            {!!rows.length && (
              <div className="mt-3 space-y-4">
                {['CRITICAL','HIGH','MEDIUM','LOW','UNKNOWN'].map(sev => {
                  const items = bySeverity[sev] || [];
                  if (!items.length) return null;
                  return (
                    <div key={sev}>
                      <div className="inline-block border border-black px-2 py-1 text-xs font-semibold">{sev} · {items.length}</div>
                      <ul className="mt-2 divide-y divide-black border border-black">
                        {items.map((it, i) => (
                          <li key={i} className="flex flex-wrap gap-3 p-3">
                            <code className="bg-black text-white px-2 py-1">{it.file}:{it.line}</code>
                            <span className="flex-1">{it.message}</span>
                            {it.confidence != null && <span className="border border-black px-2 py-1 text-xs">c={it.confidence.toFixed(2)}</span>}
                          </li>
                        ))}
                      </ul>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* What it does - info cards */}
      <section className="mx-auto max-w-6xl px-6 pb-24">
        <h2 className="text-2xl font-extrabold tracking-tight mb-4">What PromptScan Does</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <InfoCard icon={<Search className="w-5 h-5"/>} title="Static scan of your repo" desc="Parses files, respects .gitignore, and analyzes only relevant code paths."/>
          <InfoCard icon={<Brain className="w-5 h-5"/>} title="Context‑aware heuristics" desc="Understands logging/UI contexts vs dangerous code to reduce false positives."/>
          <InfoCard icon={<ShieldCheck className="w-5 h-5"/>} title="Confidence + strict" desc="Scores each finding and supports strict mode with tunable thresholds."/>
          <InfoCard icon={<Terminal className="w-5 h-5"/>} title="CLI & Web" desc="Run via prompt-scan in the terminal or paste a URL here for the same engine."/>
          <InfoCard icon={<Shield className="w-5 h-5"/>} title="Language coverage" desc="Targets Python/JS/TS first, with a rules engine that’s easy to extend."/>
          <InfoCard icon={<Github className="w-5 h-5"/>} title="GitHub friendly" desc="Fetches public repos over HTTPS ZIP, no tokens required for scanning."/>
        </div>
      </section>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-black p-3 text-center rounded-xl">
      <div className="text-xs uppercase font-semibold">{label}</div>
      <div className="text-xl font-extrabold">{value}</div>
    </div>
  );
}

function InfoCard({ icon, title, desc }: { icon: React.ReactNode; title: string; desc: string }) {
  return (
    <div className="border border-black bg-white p-5 rounded-xl transition-transform hover:-translate-y-[1px]">
      <div className="flex items-center gap-2 font-semibold">{icon} {title}</div>
      <p className="text-sm mt-2">{desc}</p>
    </div>
  );
}

