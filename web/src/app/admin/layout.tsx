"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  GraduationCap,
  BookOpen,
  Play,
  LogOut,
  Menu,
  X,
  BarChart2,
  Clock,
  Scissors,
  GraduationCap as Logo,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/admin", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { href: "/admin/sources", label: "Sources", icon: BarChart2 },
  { href: "/admin/universities", label: "Universities", icon: GraduationCap },
  { href: "/admin/courses", label: "Courses", icon: BookOpen },
  { href: "/admin/pending-review", label: "Pending Review", icon: Clock },
  { href: "/admin/scraper", label: "Scraper Jobs", icon: Play },
  { href: "/admin/silence-test", label: "Silence Test", icon: Scissors },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("ocw_token");
    if (!token && pathname !== "/admin/login") {
      router.replace("/admin/login");
    } else {
      setAuthed(true);
    }
  }, [pathname, router]);

  function handleLogout() {
    localStorage.removeItem("ocw_token");
    router.push("/admin/login");
  }

  if (authed === null) return null;

  if (pathname === "/admin/login") return <>{children}</>;

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-60 flex flex-col transition-transform duration-300",
          "border-r border-white/[0.06] bg-card/60 backdrop-blur-xl",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
          "md:static md:translate-x-0"
        )}
      >
        {/* Sidebar header */}
        <div className="flex items-center justify-between px-5 h-16 border-b border-white/[0.06] shrink-0">
          <Link href="/" className="flex items-center gap-2.5 group">
            <Logo className="h-5 w-5 text-primary" />
            <div>
              <p className="font-bold text-sm leading-none tracking-tight">The Commons</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">Admin Panel</p>
            </div>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="md:hidden text-muted-foreground hover:text-foreground p-1 rounded-md hover:bg-white/[0.06] transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
          {navItems.map(({ href, label, icon: Icon, exact }) => {
            const isActive = exact ? pathname === href : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150",
                  isActive
                    ? "bg-primary/15 text-primary shadow-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-white/[0.05]"
                )}
              >
                <Icon className={cn("h-4 w-4 shrink-0", isActive ? "text-primary" : "")} />
                {label}
                {isActive && (
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
                )}
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t border-white/[0.06]">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/[0.05] w-full transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-white/[0.06] flex items-center px-4 gap-3 md:hidden bg-card/60 backdrop-blur-xl">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-muted-foreground hover:text-foreground p-1.5 rounded-md hover:bg-white/[0.06] transition-colors"
          >
            <Menu className="h-5 w-5" />
          </button>
          <span className="font-semibold text-sm">Admin Panel</span>
        </header>

        <main className="flex-1 p-4 md:p-8 max-w-7xl w-full">{children}</main>
      </div>
    </div>
  );
}
