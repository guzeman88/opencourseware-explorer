"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { Search, BookOpen, GraduationCap, Menu, X, Bookmark, LogOut, User, Server } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/providers/auth-provider";

const navLinks = [
  { href: "/courses", label: "All Courses" },
  { href: "/universities", label: "Universities" },
  { href: "/subjects", label: "Subjects" },
  { href: "/roadmaps", label: "Roadmaps" },
];

interface NavbarProps {
  onSignInClick: () => void;
}

export function Navbar({ onSignInClick }: NavbarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, signOut } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [searchVal, setSearchVal] = useState("");

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (searchVal.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchVal.trim())}`);
      setSearchVal("");
    }
  }

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/90 backdrop-blur supports-[backdrop-filter]:bg-background/60 pt-safe">
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
          {user && (
            <Link
              href="/library"
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                pathname === "/library"
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
              )}
            >
              <Bookmark className="h-4 w-4" />
              Library
            </Link>
          )}
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

        {/* Right side: auth */}
        <div className="hidden md:flex items-center gap-1">
          {user ? (
            <>
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen((v) => !v)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
                >
                  <User className="h-4 w-4" />
                  <span className="max-w-[120px] truncate">{user.email.split("@")[0]}</span>
                </button>
                {userMenuOpen && (
                  <div className="absolute right-0 top-full mt-1 bg-card border border-border rounded-lg shadow-xl py-1 min-w-[160px] z-50">
                    {user.is_admin && (
                      <Link
                        href="/admin"
                        onClick={() => setUserMenuOpen(false)}
                        className="flex items-center gap-2 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-accent/50"
                      >
                        <Server className="h-4 w-4" />
                        Backend
                      </Link>
                    )}
                    <button
                      onClick={() => { signOut(); setUserMenuOpen(false); }}
                      className="w-full flex items-center gap-2 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-accent/50"
                    >
                      <LogOut className="h-4 w-4" />
                      Sign out
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <button
                onClick={onSignInClick}
                className="px-3 py-1.5 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
              >
                Sign in
              </button>
              <button
                onClick={onSignInClick}
                className="px-3 py-1.5 rounded-md text-sm font-semibold bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                Sign up
              </button>
            </>
          )}
        </div>

        {/* Mobile menu toggle */}
        <button
          className="md:hidden p-2 rounded-md text-muted-foreground hover:text-foreground"
          onClick={() => setMenuOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile nav */}
      {menuOpen && (
        <div className="md:hidden border-t border-border bg-background px-4 py-3 space-y-1">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className="block px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent/50"
            >
              {link.label}
            </Link>
          ))}
          {user ? (
            <>
              <Link
                href="/library"
                onClick={() => setMenuOpen(false)}
                className="block px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent/50"
              >
                Library
              </Link>
              {user.is_admin && (
                <Link
                  href="/admin"
                  onClick={() => setMenuOpen(false)}
                  className="block px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent/50"
                >
                  Backend
                </Link>
              )}
              <button
                onClick={() => { signOut(); setMenuOpen(false); }}
                className="w-full text-left block px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent/50"
              >
                Sign out
              </button>
            </>
          ) : (
            <button
              onClick={() => { setMenuOpen(false); onSignInClick(); }}
              className="w-full text-left block px-3 py-2 rounded-md text-sm font-semibold text-primary hover:bg-accent/50"
            >
              Sign in / Sign up
            </button>
          )}
        </div>
      )}
    </nav>
  );
}
