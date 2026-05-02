import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDuration(seconds: number): string {
  if (!seconds) return "";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) {
    return `${h}h ${m}m`;
  }
  return `${m}m ${s}s`;
}

export function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toString();
}

export function levelLabel(level: string): string {
  const map: Record<string, string> = {
    undergraduate: "Undergraduate",
    graduate: "Graduate",
    professional: "Professional",
    other: "General",
  };
  return map[level] ?? level;
}

export function levelColor(level: string): string {
  const map: Record<string, string> = {
    undergraduate: "bg-blue-500/20 text-blue-300",
    graduate: "bg-purple-500/20 text-purple-300",
    professional: "bg-amber-500/20 text-amber-300",
    other: "bg-gray-500/20 text-gray-300",
  };
  return map[level] ?? "bg-gray-500/20 text-gray-300";
}

export function sourceLabel(sourceKey: string): string {
  const map: Record<string, string> = {
    mit_ocw: "MIT OCW",
    yale_ocw: "Yale",
    stanford: "Stanford",
    nptel: "NPTEL",
    berkeley: "UC Berkeley",
    harvard: "Harvard",
  };
  return map[sourceKey] ?? sourceKey.toUpperCase();
}

export function thumbnailUrl(course: {
  thumbnail_url?: string | null;
  youtube_playlist_id?: string | null;
  source_key?: string | null;
}): string | null {
  if (course.thumbnail_url) return course.thumbnail_url;
  return null;
}

/** Gradient pair [from, to] for each source_key */
export function universityGradient(source_key: string | null | undefined): [string, string] {
  const map: Record<string, [string, string]> = {
    mit_ocw:      ["#8b0000", "#1a0000"],
    stanford:     ["#8c1515", "#2e0505"],
    yale:         ["#00356b", "#001228"],
    harvard:      ["#a41034", "#320010"],
    berkeley:     ["#003262", "#fdb515"],
    nptel:        ["#0047ab", "#001433"],
    khan:         ["#14bf96", "#084d3c"],
    crashcourse:  ["#2980b9", "#0d2b45"],
    "3b1b":       ["#1a1a2e", "#16213e"],
    freecodecamp: ["#0a0a23", "#1b1b32"],
    gatech:       ["#b3a369", "#003057"],
    simons:       ["#5b2d8e", "#1a0d2e"],
  };
  return map[source_key ?? ""] ?? ["#1e3a5f", "#0a1628"];
}
