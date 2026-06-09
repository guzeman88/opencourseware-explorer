/**
 * Proxy for the Render API.
 * Public GET requests are cached at the hosting CDN edge while authenticated
 * requests and mutations always pass through uncached.
 *
 * The Node.js runtime avoids the shorter edge execution limit during a Render
 * cold start. Netlify-Vary keeps distinct filtered catalog queries isolated.
 */

// Always dynamic so the route is never pre-rendered into the Next.js build.
export const dynamic = "force-dynamic";

const UPSTREAM =
  process.env.API_UPSTREAM ??
  "https://opencourseware-api.onrender.com";

async function handler(
  req: Request,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const url = new URL(req.url);
  const { path } = await params;
  const upstream = `${UPSTREAM}/api/v1/${path.join("/")}${url.search}`;

  const fwdHeaders = new Headers(req.headers);
  fwdHeaders.delete("host");

  const hasBody = req.method !== "GET" && req.method !== "HEAD";

  // Buffer request bodies because forwarding the original stream can fail
  // when the Node.js runtime has not fully consumed it.
  let bodyBuffer: ArrayBuffer | undefined;
  if (hasBody) {
    try {
      bodyBuffer = await req.arrayBuffer();
    } catch {
      bodyBuffer = undefined;
    }
  }

  let upstreamRes: Response;
  try {
    upstreamRes = await fetch(upstream, {
      method: req.method,
      headers: fwdHeaders,
      body: bodyBuffer,
      signal: AbortSignal.timeout(25000),
    });
  } catch {
    return new Response(JSON.stringify({ error: "upstream_unavailable" }), {
      status: 503,
      headers: { "Content-Type": "application/json" },
    });
  }

  const resHeaders = new Headers(upstreamRes.headers);

  // Node.js fetch auto-decompresses gzip and brotli, so remove stale headers.
  resHeaders.delete("content-encoding");
  resHeaders.delete("content-length");

  const isPublicRead =
    req.method === "GET" &&
    upstreamRes.ok &&
    !req.headers.get("authorization") &&
    !req.headers.get("cookie")?.includes("ocw_session=");

  resHeaders.set(
    "Cache-Control",
    isPublicRead
      ? "public, s-maxage=3600, stale-while-revalidate=86400"
      : "no-store"
  );

  resHeaders.set(
    "Netlify-CDN-Cache-Control",
    isPublicRead
      ? "public, durable, s-maxage=3600, stale-while-revalidate=86400"
      : "no-store"
  );
  if (isPublicRead) {
    resHeaders.set("Netlify-Vary", "query");
  }

  return new Response(upstreamRes.body, {
    status: upstreamRes.status,
    statusText: upstreamRes.statusText,
    headers: resHeaders,
  });
}

export {
  handler as GET,
  handler as POST,
  handler as PUT,
  handler as PATCH,
  handler as DELETE,
};
