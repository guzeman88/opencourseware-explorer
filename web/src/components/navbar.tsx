"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Search, GraduationCap, Menu, X, Bookmark, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/providers/auth-provider";
import { useAuthModal } from "@/providers/auth-modal-provider";

const navLinks = [
  { href: "/courses", label: "All Courses" },
  { href: "/universities", label: "Universities" },
  { href: "/subjects", label: "Subjects" },
  { href: "/roadmaps", label: "Roadmaps" },
  { href: "/library", label: "Library" },
];

export function Navbar({ onSignInClick }: { onSignInClick?: () => void }) {
  const pathname = usePathname();
  const router = useRouter();
  const mobileMenuRef = useRef<HTMLDivElement>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchVal, setSearchVal] = useState("");
  const { user, signOut } = useAuth();
  const { openAuthModal } = useAuthModal();
  const mobileMenuId = "mobile-navigation-menu";

  useEffect(() => {
    if (!menuOpen) return;

    function handlePointerDown(event: PointerEvent) {
      if (!mobileMenuRef.current?.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [menuOpen]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (searchVal.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchVal.trim())}`);
      setSearchVal("");
    }
  }

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/90 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="max-w-screen-2xl mx-auto px-4 md:px-8 flex h-16 items-center gap-4">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2 font-bold text-lg text-foreground shrink-0"
        >
          <GraduationCap className="h-6 w-6 text-primary" />
          <span className="hidden sm:block">The Commons</span>
        </Link>

        {/* Desktop nav links */}
        <div className="hidden md:flex items-center gap-1 ml-4">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                pathname.startsWith(link.href)
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
              )}
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Search */}
        <form
          onSubmit={handleSearch}
          className="flex-1 max-w-md ml-auto flex items-center gap-2"
        >
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
            <input
              type="search"
              value={searchVal}
              onChange={(e) => setSearchVal(e.target.value)}
              placeholder="Search courses..."
              className="w-full bg-secondary border border-border rounded-full pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary placeholder:text-muted-foreground"
              aria-label="Search courses"
            />
          </div>
        </form>

        {/* Auth */}
        {user ? (
          <div className="hidden md:flex items-center gap-2">
            <Link
              href="/library"
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                pathname.startsWith("/library")
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
              )}
            >
              <Bookmark className="h-4 w-4" />
            </Link>
            <button
              onClick={signOut}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
              title={`Signed in as ${user.email}`}
            >
              <span className="h-6 w-6 rounded-full bg-primary flex items-center justify-center text-[10px] font-bold text-primary-foreground">
                {user.email[0].toUpperCase()}
              </span>
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        ) : (
          <button
            onClick={openAuthModal}
            className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Sign in
          </button>
        )}

        {/* Mobile menu */}
        <div ref={mobileMenuRef} className="relative md:hidden">
          <button
            className={cn(
              "inline-flex h-10 w-10 items-center justify-center rounded-md text-muted-foreground transition-colors",
              "hover:bg-accent/60 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              menuOpen && "bg-accent text-foreground"
            )}
            onClick={() => setMenuOpen((v) => !v)}
            aria-label="Toggle menu"
            aria-controls={mobileMenuId}
            aria-expanded={menuOpen}
            aria-haspopup="dialog"
          >
            {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>

          {menuOpen && (
            <div
              id={mobileMenuId}
              role="dialog"
              aria-label="Site navigation"
              className="absolute right-0 top-[calc(100%+0.75rem)] z-50 w-[min(calc(100vw-2rem),18rem)] origin-top-right overflow-hidden rounded-lg border border-border bg-card p-2 text-card-foreground shadow-2xl shadow-black/40 animate-fade-in"
            >
              <div className="space-y-1">
                {navLinks.map((link) => {
                  const isActive = pathname.startsWith(link.href);

                  return (
                    <Link
                      key={link.href}
                      href={link.href}
                      onClick={() => setMenuOpen(false)}
                      className={cn(
                        "flex min-h-10 items-center rounded-md px-3 text-sm font-medium transition-colors",
                        isActive
                          ? "bg-accent text-accent-foreground"
                          : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
                      )}
                    >
                      {link.label}
                    </Link>
                  );
                })}
              </div>

              <div className="my-2 h-px bg-border" />

              {user ? (
                <button
                  onClick={() => {
                    signOut();
                    setMenuOpen(false);
                  }}
                  className="flex w-full min-h-10 items-center justify-between gap-3 rounded-md px-3 text-left text-sm font-medium text-muted-foreground transition-colors hover:bg-accent/60 hover:text-foreground"
                  title={`Signed in as ${user.email}`}
                >
                  <span className="min-w-0 truncate">{user.email}</span>
                  <LogOut className="h-4 w-4 shrink-0" />
                </button>
              ) : (
                <button
                  onClick={() => {
                    openAuthModal();
                    setMenuOpen(false);
                  }}
                  className="flex w-full min-h-10 items-center justify-center rounded-md bg-primary px-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
                >
                  Sign in
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
