'use client';

import { useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Shield, Github, Search, Brain, ShieldCheck, Terminal, BarChart3, AlertTriangle, CheckCircle, Clock, Activity, Folder, AlertCircle, XCircle, Minus } from 'lucide-react';

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
    for (const item of data?.results || []) {
      for (const f of item.findings || []) {
        r.push({
          file: item.file_path,
          severity: (f.severity || 'unknown').toUpperCase(),
          message: f.message || '',
          line: String(f.line ?? f.line_no ?? ''),
          confidence: typeof f.confidence === 'number' ? f.confidence : undefined,
        });
      }
    }
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
            <div className="flex items-center gap-2 mb-4">
              <Shield className="w-5 h-5"/>
              <div className="text-md font-semibold uppercase">Scan Summary</div>
            </div>
            <div className="mt-2">
              {data?.summary ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatCard 
                    icon={<BarChart3 className="w-6 h-6" />}
                    label="Files Scanned" 
                    value={`${data.summary.scanned_files ?? 0}`}
                    subtitle={`of ${data.summary.total_files ?? 0} total`}
                  />
                  <StatCard 
                    icon={rows.length > 0 ? <AlertTriangle className="w-6 h-6 text-orange-600" /> : <CheckCircle className="w-6 h-6 text-green-600" />}
                    label="Security Issues" 
                    value={`${data.summary.total_findings ?? 0}`}
                    subtitle={rows.length > 0 ? "found" : "clean"}
                  />
                  <StatCard 
                    icon={<Clock className="w-6 h-6" />}
                    label="Scan Time" 
                    value={`${data.summary.scan_duration ?? 0}s`}
                    subtitle="completed"
                  />
                  <StatCard 
                    icon={loading ? <Activity className="w-6 h-6 animate-pulse" /> : data ? <CheckCircle className="w-6 h-6 text-green-600" /> : <Minus className="w-6 h-6" />}
                    label="Status" 
                    value={loading ? 'Scanning' : data ? 'Complete' : 'Ready'}
                    subtitle={loading ? "in progress" : data ? "finished" : "to scan"}
                  />
                </div>
              ) : (
                <div className="text-center py-8">
                  <Shield className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                  <div className="text-sm text-gray-600">Ready to scan! Paste a GitHub URL above.</div>
                </div>
              )}
            </div>
          </div>

          {/* Findings - Beautiful Cards */}
          <div className="border border-black bg-white text-black p-6 rounded-2xl">
            <div className="flex items-center justify-between mb-4">
              <div className="text-md font-semibold uppercase">Security Findings</div>
              <div className="text-sm text-gray-600">{rows.length} total findings</div>
            </div>
            
            {!rows.length && (
              <div className="text-center py-12">
                <Shield className="w-16 h-16 mx-auto text-green-600 mb-4"/>
                <div className="text-lg font-semibold text-green-600">No vulnerabilities found!</div>
                <div className="text-sm text-gray-500 mt-1">Your repository looks secure.</div>
              </div>
            )}
            
            {!!rows.length && (
              <div className="space-y-6">
                {['CRITICAL','HIGH','MEDIUM','LOW','UNKNOWN'].map(sev => {
                  const items = bySeverity[sev] || [];
                  if (!items.length) return null;
                  
                  const severityColors = {
                    'CRITICAL': 'bg-red-100 border-red-500 text-red-800',
                    'HIGH': 'bg-orange-100 border-orange-500 text-orange-800', 
                    'MEDIUM': 'bg-yellow-100 border-yellow-500 text-yellow-800',
                    'LOW': 'bg-blue-100 border-blue-500 text-blue-800',
                    'UNKNOWN': 'bg-gray-100 border-gray-500 text-gray-800'
                  };
                  
                  const severityIcons = {
                    'CRITICAL': <XCircle className="w-4 h-4" />,
                    'HIGH': <AlertCircle className="w-4 h-4" />, 
                    'MEDIUM': <AlertTriangle className="w-4 h-4" />,
                    'LOW': <AlertTriangle className="w-4 h-4" />,
                    'UNKNOWN': <Minus className="w-4 h-4" />
                  };
                  
                  return (
                    <div key={sev} className="space-y-3">
                      <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full font-semibold text-sm ${severityColors[sev as keyof typeof severityColors]}`}>
                        <span>{severityIcons[sev as keyof typeof severityIcons]}</span>
                        {sev} ({items.length} findings)
                      </div>
                      
                      <div className="grid gap-4">
                        {items.map((it, i) => (
                          <div key={i} className="border border-gray-200 rounded-xl p-4 hover:shadow-md transition-shadow bg-gray-50">
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-2">
                                  <code className="bg-black text-white px-3 py-1 rounded-full text-xs font-mono">
                                    {it.file.split('/').pop()}:{it.line}
                                  </code>
                                  {it.confidence != null && (
                                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                                      {Math.round(it.confidence * 100)}% confidence
                                    </span>
                                  )}
                                </div>
                                <p className="text-sm text-gray-800 leading-relaxed">{it.message}</p>
                                <div className="flex items-center gap-1 text-xs text-gray-500 mt-2 font-mono truncate" title={it.file}>
                                  <Folder className="w-3 h-3 flex-shrink-0" />
                                  <span className="truncate">{it.file}</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
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

function StatCard({ icon, label, value, subtitle }: { icon: React.ReactNode; label: string; value: string; subtitle: string }) {
  return (
    <div className="border border-gray-200 bg-gray-50 p-4 text-center rounded-xl hover:shadow-md transition-shadow">
      <div className="flex justify-center mb-3">{icon}</div>
      <div className="text-xs uppercase font-semibold text-gray-600 mb-1">{label}</div>
      <div className="text-2xl font-extrabold text-gray-900">{value}</div>
      <div className="text-xs text-gray-500">{subtitle}</div>
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

