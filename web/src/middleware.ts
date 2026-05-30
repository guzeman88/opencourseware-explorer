/**
 * Next.js Edge Middleware — server-side guard for /admin/* routes.
 *
 * Checks for the `ocw_session` cookie (httpOnly, set by the backend login
 * endpoint) or an Authorization Bearer header.  Because `ocw_session` is
 * httpOnly it cannot be read or forged by client-side JavaScript.
 *
 * NOTE: The middleware only performs a lightweight *presence* check.
 * Cryptographic signature verification happens on the backend for every
 * authenticated API call.
 */
import { NextRequest, NextResponse } from "next/server";

const ADMIN_LOGIN = "/admin/login";

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Only gate /admin/* paths (except the login page itself)
  if (!pathname.startsWith("/admin") || pathname === ADMIN_LOGIN) {
    return NextResponse.next();
  }

  // Prefer the httpOnly backend session cookie; fall back to Authorization header.
  const sessionToken = req.cookies.get("ocw_session")?.value;
  const authHeader = req.headers.get("authorization");
  const bearerToken = authHeader?.startsWith("Bearer ")
    ? authHeader.slice(7)
    : undefined;

  const hasToken = Boolean(sessionToken || bearerToken);

  if (!hasToken) {
    const loginUrl = req.nextUrl.clone();
    loginUrl.pathname = ADMIN_LOGIN;
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/:path*"],
};
