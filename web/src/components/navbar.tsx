"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { Search, GraduationCap, Menu, X, Bookmark, LogOut, User, Server } from "lucide-react";
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
    <nav className="sticky top-0 z-50 w-full border-b border-white/[0.06] bg-background/85 backdrop-blur-xl supports-[backdrop-filter]:bg-background/70 pt-safe">
      <div className="max-w-screen-2xl mx-auto px-4 md:px-8 flex h-16 items-center gap-4">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2.5 font-bold text-lg shrink-0 group"
        >
          <div className="relative">
            <GraduationCap className="h-6 w-6 text-primary transition-transform duration-300 group-hover:scale-110" />
          </div>
          <span className="hidden sm:block tracking-tight gradient-text">The Commons</span>
        </Link>

        {/* Desktop nav links */}
        <div className="hidden md:flex items-center gap-0.5 ml-4">
          {navLinks.map((link) => {
            const isActive = pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "relative px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-150",
                  isActive
                    ? "text-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-white/[0.05]"
                )}
              >
                {link.label}
                {isActive && (
                  <span className="absolute bottom-0 left-3 right-3 h-[2px] rounded-full bg-primary" />
                )}
              </Link>
            );
          })}
          {user && (
            <Link
              href="/library"
              className={cn(
                "relative flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-150",
                pathname === "/library"
                  ? "text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/[0.05]"
              )}
            >
              <Bookmark className="h-3.5 w-3.5" />
              Library
              {pathname === "/library" && (
                <span className="absolute bottom-0 left-3 right-3 h-[2px] rounded-full bg-primary" />
              )}
            </Link>
          )}
        </div>

        {/* Search */}
        <form
          onSubmit={handleSearch}
          className="flex-1 max-w-md ml-auto flex items-center"
        >
          <div className="relative w-full group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none transition-colors duration-200 group-focus-within:text-primary" />
            <input
              type="search"
              value={searchVal}
              onChange={(e) => setSearchVal(e.target.value)}
              placeholder="Search courses..."
              className="w-full bg-white/[0.06] border border-white/[0.1] rounded-full pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/60 placeholder:text-muted-foreground transition-all duration-200 hover:border-white/[0.15]"
              aria-label="Search courses"
            />
          </div>
        </form>

        {/* Right side: auth */}
        <div className="hidden md:flex items-center gap-1.5">
          {user ? (
            <>
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen((v) => !v)}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/[0.06] transition-colors"
                >
                  <div className="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center">
                    <User className="h-3.5 w-3.5 text-primary" />
                  </div>
                  <span className="max-w-[100px] truncate">{user.email.split("@")[0]}</span>
                </button>
                {userMenuOpen && (
                  <div className="absolute right-0 top-full mt-2 glass border border-white/[0.1] rounded-xl shadow-2xl py-1.5 min-w-[170px] z-50 animate-slide-down">
                    {user.is_admin && (
                      <Link
                        href="/admin"
                        onClick={() => setUserMenuOpen(false)}
                        className="flex items-center gap-2.5 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-white/[0.06] transition-colors"
                      >
                        <Server className="h-4 w-4 text-primary" />
                        Admin Panel
                      </Link>
                    )}
                    <div className="my-1 border-t border-white/[0.06]" />
                    <button
                      onClick={() => { signOut(); setUserMenuOpen(false); }}
                      className="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-white/[0.06] transition-colors"
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
                className="px-3 py-1.5 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/[0.06] transition-colors"
              >
                Sign in
              </button>
              <button
                onClick={onSignInClick}
                className="px-4 py-1.5 rounded-full text-sm font-semibold bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-200 shadow-sm hover:shadow-[0_0_16px_hsl(var(--primary)/0.4)]"
              >
                Get Started
              </button>
            </>
          )}
        </div>

        {/* Mobile menu toggle */}
        <button
          className="md:hidden p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/[0.06] transition-colors"
          onClick={() => setMenuOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile nav */}
      {menuOpen && (
        <div className="md:hidden border-t border-white/[0.06] bg-background/95 backdrop-blur-xl px-4 py-3 space-y-0.5 animate-slide-down">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className={cn(
                "block px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                pathname.startsWith(link.href)
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/[0.05]"
              )}
            >
              {link.label}
            </Link>
          ))}
          {user ? (
            <>
              <Link
                href="/library"
                onClick={() => setMenuOpen(false)}
                className={cn(
                  "flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  pathname === "/library"
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-white/[0.05]"
                )}
              >
                <Bookmark className="h-4 w-4" />
                Library
              </Link>
              {user.is_admin && (
                <Link
                  href="/admin"
                  onClick={() => setMenuOpen(false)}
                  className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/[0.05] transition-colors"
                >
                  <Server className="h-4 w-4" />
                  Admin Panel
                </Link>
              )}
              <div className="pt-1 border-t border-white/[0.06] mt-1">
                <button
                  onClick={() => { signOut(); setMenuOpen(false); }}
                  className="w-full text-left flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/[0.05] transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  Sign out
                </button>
              </div>
            </>
          ) : (
            <div className="pt-1">
              <button
                onClick={() => { setMenuOpen(false); onSignInClick(); }}
                className="w-full text-center block px-3 py-2.5 rounded-full text-sm font-semibold bg-primary text-primary-foreground"
              >
                Sign in / Get Started
              </button>
            </div>
          )}
        </div>
      )}
    </nav>
  );
}


const navLinks = [
  { href: "/courses", label: "All Courses" },
  { href: "/universities", label: "Universities" },
  { href: "/subjects", label: "Subjects" },
  { href: "/roadmaps", label: "Roadmaps" },
];

