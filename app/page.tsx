'use client';

import { useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Shield, Github, Search, Brain, ShieldCheck, Terminal, BarChart3, AlertTriangle, CheckCircle, Clock, Activity, Folder, AlertCircle, XCircle, Minus } from 'lucide-react';
import { AuroraBackground } from '@/components/ui/aurora-background';

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
    <div>
      {/* Hero with Aurora Background */}
      <AuroraBackground>
        <section className="relative z-10">
          <div className="mx-auto max-w-6xl px-6 py-32 text-center">
            <div className="inline-block border border-black/20 bg-white/80 backdrop-blur-sm px-4 py-2 text-xs font-semibold rounded-full">Powered by heuristics</div>
            <h1 className="mt-6 text-7xl font-extrabold leading-[1.05] tracking-tight bg-gradient-to-br from-black to-gray-600 bg-clip-text text-transparent">PromptScan</h1>
            <p className="mt-4 text-lg max-w-2xl mx-auto text-gray-700 leading-relaxed">Paste a public GitHub URL and get an incredibly accurate report of potential prompt injection risks.</p>
            <div className="mt-8 flex items-center justify-center gap-4">
              <a href="#scan" className="inline-flex items-center justify-center text-sm font-medium px-6 py-3 rounded-full bg-black text-white border border-black hover:brightness-95 hover:scale-105 transition-all duration-200 shadow-lg">Get Started</a>
              <a href="https://github.com" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 text-sm font-medium px-6 py-3 rounded-full bg-white/80 backdrop-blur-sm text-black border border-black/20 hover:bg-white hover:shadow-lg transition-all duration-200"><Github className="w-4 h-4"/> GitHub</a>
            </div>
          </div>
        </section>
      </AuroraBackground>

      {/* Scanner input on white card */}
      <main className="bg-gray-50 min-h-screen">
        <section id="scan" className="mx-auto max-w-6xl px-6 py-16">
          <div className="border border-gray-200 bg-white text-black p-8 rounded-3xl shadow-xl">
            <div className="text-xl font-semibold flex items-center gap-3 mb-6"><Shield className="w-6 h-6 text-blue-600"/> Scan a Repository</div>
            <div className="flex gap-4">
              <Input 
                value={url} 
                onChange={e => setUrl(e.target.value)} 
                placeholder="https://github.com/owner/repo" 
                className="flex-1 h-12 px-4 border-gray-300 rounded-xl focus:border-blue-500 focus:ring-blue-500"
              />
              <Button 
                onClick={scan}
                className="h-12 px-8 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors"
              >
                {loading ? <Activity className="w-4 h-4 animate-spin mr-2" /> : null}
                Scan
              </Button>
            </div>
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl">
                <div className="flex items-center gap-2 text-red-800">
                  <AlertCircle className="w-4 h-4" />
                  <span className="font-medium">Error:</span>
                </div>
                <p className="text-red-700 mt-1 text-sm">{error}</p>
              </div>
            )}
            {loading && (
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-xl">
                <div className="flex items-center gap-3 text-blue-800">
                  <Activity className="w-5 h-5 animate-spin" />
                  <span className="font-medium">Scanning repository...</span>
                </div>
                <p className="text-blue-700 text-sm mt-1">This may take a few moments depending on repository size.</p>
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
        <h2 className="text-3xl font-extrabold tracking-tight mb-8 text-center text-gray-900">What PromptScan Does</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <InfoCard icon={<Search className="w-6 h-6 text-blue-600"/>} title="Static scan of your repo" desc="Parses files, respects .gitignore, and analyzes only relevant code paths."/>
          <InfoCard icon={<Brain className="w-6 h-6 text-purple-600"/>} title="Context‑aware heuristics" desc="Understands logging/UI contexts vs dangerous code to reduce false positives."/>
          <InfoCard icon={<ShieldCheck className="w-6 h-6 text-green-600"/>} title="Confidence + strict" desc="Scores each finding and supports strict mode with tunable thresholds."/>
          <InfoCard icon={<Terminal className="w-6 h-6 text-gray-600"/>} title="CLI & Web" desc="Run via prompt-scan in the terminal or paste a URL here for the same engine."/>
          <InfoCard icon={<Shield className="w-6 h-6 text-red-600"/>} title="Language coverage" desc="Targets Python/JS/TS first, with a rules engine that's easy to extend."/>
          <InfoCard icon={<Github className="w-6 h-6 text-gray-800"/>} title="GitHub friendly" desc="Fetches public repos over HTTPS ZIP, no tokens required for scanning."/>
        </div>
      </section>
    </main>
    </div>
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
    <div className="border border-gray-200 bg-white p-6 rounded-2xl hover:shadow-lg transition-all duration-300 hover:-translate-y-1 group">
      <div className="flex items-center gap-3 font-semibold text-gray-900 mb-3">
        <div className="p-2 bg-gray-50 rounded-lg group-hover:scale-110 transition-transform">
          {icon}
        </div>
        <span className="text-lg">{title}</span>
      </div>
      <p className="text-gray-600 leading-relaxed">{desc}</p>
    </div>
  );
}

