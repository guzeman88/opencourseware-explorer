import Link from "next/link";
import { GraduationCap, Home, Search, BookOpen } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[calc(100vh-8rem)] flex flex-col items-center justify-center px-4 text-center">
      {/* Big number */}
      <div className="relative mb-6">
        <span className="text-[10rem] font-black leading-none text-primary/10 select-none">
          404
        </span>
        <div className="absolute inset-0 flex items-center justify-center">
          <GraduationCap className="h-20 w-20 text-primary/40" />
        </div>
      </div>

      <h1 className="text-3xl font-bold mb-3">Page not found</h1>
      <p className="text-muted-foreground max-w-md mb-10 text-base">
        The course or page you&apos;re looking for doesn&apos;t exist, was moved, or
        the link you followed may be broken.
      </p>

      {/* Quick-nav buttons */}
      <div className="flex flex-wrap gap-3 justify-center">
        <Link
          href="/"
          className="inline-flex items-center gap-2 bg-primary text-primary-foreground hover:bg-primary/90 px-5 py-2.5 rounded-lg font-medium text-sm transition-colors"
        >
          <Home className="h-4 w-4" />
          Go home
        </Link>
        <Link
          href="/courses"
          className="inline-flex items-center gap-2 bg-secondary hover:bg-secondary/80 text-secondary-foreground px-5 py-2.5 rounded-lg font-medium text-sm transition-colors"
        >
          <BookOpen className="h-4 w-4" />
          All Courses
        </Link>
        <Link
          href="/search"
          className="inline-flex items-center gap-2 bg-secondary hover:bg-secondary/80 text-secondary-foreground px-5 py-2.5 rounded-lg font-medium text-sm transition-colors"
        >
          <Search className="h-4 w-4" />
          Search
        </Link>
      </div>
    </div>
  );
}
