/**
 * Proxy for Railway API.
 * Routes /api/v1/* → Railway backend with Vercel CDN caching for GET requests.
 * This turns 100+ slow browser→Railway round-trips into fast Vercel edge hits.
 *
 * Note: using Node.js runtime (not edge) to avoid the 15s edge execution limit
 * in local dev and to support Railway cold-start latency in production.
 * Vercel CDN still caches based on Cache-Control headers with either runtime.
 */

const UPSTREAM =
  process.env.API_UPSTREAM ??
  "https://opencourseware-api.onrender.com";

async function handler(
  req: Request,
  { params }: { params: { path: string[] } }
) {
  const url = new URL(req.url);
  const upstream = `${UPSTREAM}/api/v1/${params.path.join("/")}${url.search}`;

  // Forward all headers except host
  const fwdHeaders = new Headers(req.headers);
  fwdHeaders.delete("host");

  const hasBody = req.method !== "GET" && req.method !== "HEAD";

  // Buffer the body first — passing req.body (ReadableStream) directly to fetch
  // can fail in some Node.js versions when the stream hasn't been fully consumed.
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

  // Node.js fetch (undici) auto-decompresses gzip/br, so the body is already
  // plain text — remove Content-Encoding so the browser doesn't try to decompress again.
  resHeaders.delete("content-encoding");
  resHeaders.delete("content-length"); // length changed after decompression

  // Cache public GET reads at Vercel's CDN edge for 5 min (stale-while-revalidate for 1 hr)
  // Never cache authenticated requests or mutations
  const isPublicRead =
    req.method === "GET" &&
    upstreamRes.ok &&
    !req.headers.get("authorization");

  resHeaders.set(
    "Cache-Control",
    isPublicRead
      // s-maxage=3600: Vercel CDN serves from cache for 1 hour (no Railway hit).
      // stale-while-revalidate=86400: stale cache served while revalidating
      // in background — users never wait for Railway cold starts.
      ? "public, s-maxage=3600, stale-while-revalidate=86400"
      : "no-store"
  );

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
