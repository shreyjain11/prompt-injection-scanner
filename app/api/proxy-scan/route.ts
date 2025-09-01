export const runtime = 'nodejs';

function getBase(): string | null {
  const env = process.env.API_BASE || process.env.NEXT_PUBLIC_API_BASE || '';
  const trimmed = env.replace(/\/$/, '');
  return trimmed ? trimmed : null;
}

async function forward(url: string, init?: RequestInit) {
  const res = await fetch(url, init);
  const text = await res.text();
  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    return new Response(JSON.stringify({ error: `Upstream returned non-JSON (status ${res.status})` }), {
      status: 502,
      headers: { 'content-type': 'application/json' },
    });
  }
  return new Response(text, {
    status: res.status,
    headers: { 'content-type': 'application/json' },
  });
}

export async function POST(req: Request) {
  const base = getBase();
  if (!base) {
    return Response.json({ error: 'API_BASE not configured. Set API_BASE or NEXT_PUBLIC_API_BASE to your deployed URL.' }, { status: 503 });
  }
  const endpoint = `${base}/api/scan`;
  const body = await req.text();
  return forward(endpoint, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body,
  });
}

export async function GET(req: Request) {
  const base = getBase();
  if (!base) {
    return Response.json({ error: 'API_BASE not configured. Set API_BASE or NEXT_PUBLIC_API_BASE to your deployed URL.' }, { status: 503 });
  }
  const { searchParams } = new URL(req.url);
  const url = searchParams.get('url') || '';
  const endpoint = `${base}/api/scan?url=${encodeURIComponent(url)}`;
  return forward(endpoint);
}


