"use client";

import { useRef, useState } from "react";
import dynamic from "next/dynamic";
import { SkipForward, Gauge, Puzzle, Clock, Info, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";

const ReactPlayer = dynamic(() => import("react-player/youtube"), {
  ssr: false,
  loading: () => (
    <div className="aspect-video bg-black flex items-center justify-center rounded-lg">
      <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  ),
});

const VIDEO_ID = "Cx5Z-OslNWE";
const VIDEO_URL = `https://www.youtube.com/watch?v=${VIDEO_ID}`;
const POSTER = `https://img.youtube.com/vi/${VIDEO_ID}/maxresdefault.jpg`;
const VIDEO_DURATION = 424; // seconds

// Generated with: ffmpeg -i audio.wav -af "silencedetect=n=-40dB:d=0.8" -f null -
// Source: Linear Algebra 18.06SC — Lecture 1 (Cx5Z-OslNWE)
const SILENCE: [number, number][] = [
  [14.62, 15.99],
  [37.78, 38.64],
  [44.99, 45.83],
  [55.83, 56.76],
  [79.81, 81.09],
  [88.01, 88.95],
  [107.02, 107.94],
  [131.08, 132.09],
  [136.47, 137.45],
  [236.97, 237.92],
  [273.29, 274.22],
  [321.75, 322.65],
  [325.60, 326.51],
  [339.41, 340.59],
  [363.64, 364.55],
  [366.51, 367.36],
  [414.84, 424.00],
];

const TOTAL_SILENCE_S = Math.round(SILENCE.reduce((a, [s, e]) => a + (e - s), 0));
const SILENCE_PCT = ((TOTAL_SILENCE_S / VIDEO_DURATION) * 100).toFixed(1);

// ── Option A – Hard Skip ──────────────────────────────────────────────────────
function OptionA() {
  const playerRef = useRef<any>(null);
  const [playing, setPlaying] = useState(false);
  const [saved, setSaved] = useState(0);
  const [skips, setSkips] = useState(0);
  const [inSilence, setInSilence] = useState(false);
  const lockRef = useRef(false);

  function handleProgress({ playedSeconds }: { playedSeconds: number }) {
    if (lockRef.current) return;
    const seg = SILENCE.find(([s, e]) => playedSeconds >= s && playedSeconds < e - 0.05);
    const nowInSilence = !!seg;
    setInSilence(nowInSilence);
    if (seg && playerRef.current) {
      lockRef.current = true;
      const skip = seg[1] - playedSeconds;
      setSaved((v) => parseFloat((v + skip).toFixed(1)));
      setSkips((v) => v + 1);
      playerRef.current.seekTo(seg[1] + 0.05, "seconds");
      setTimeout(() => { lockRef.current = false; }, 600);
    }
  }

  return (
    <OptionCard
      letter="A"
      icon={<SkipForward className="h-5 w-5" />}
      title="Hard Skip"
      description="Silence timestamps pre-computed with FFmpeg. During playback, onProgress fires every 200ms and seeks past any silent segment instantly."
      accentColor="text-blue-400"
      badgeColor="bg-blue-500/20 border-blue-500/30"
      stats={[
        { label: "Time saved", value: `${saved.toFixed(1)}s` },
        { label: "Skips made", value: skips },
        { label: "Status", value: inSilence ? "⏩ jumping…" : "▶ playing" },
      ]}
    >
      <ReactPlayer
        ref={playerRef}
        url={VIDEO_URL}
        width="100%"
        height="100%"
        style={{ aspectRatio: "16/9" }}
        controls
        playing={playing}
        light={!playing && POSTER}
        onClickPreview={() => setPlaying(true)}
        onProgress={handleProgress}
        progressInterval={200}
        config={{ playerVars: { modestbranding: 1, rel: 0 } } as any}
      />
    </OptionCard>
  );
}

// ── Option C – Speed Ramp ─────────────────────────────────────────────────────
const RAMP_SPEED = 5;

function OptionC() {
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [inSilence, setInSilence] = useState(false);
  const [silenceEnteredAt, setSilenceEnteredAt] = useState<number | null>(null);
  const [savedApprox, setSavedApprox] = useState(0);

  function handleProgress({ playedSeconds }: { playedSeconds: number }) {
    const silence = SILENCE.some(([s, e]) => playedSeconds >= s && playedSeconds < e);
    if (silence && !inSilence) {
      setInSilence(true);
      setSpeed(RAMP_SPEED);
      setSilenceEnteredAt(playedSeconds);
    } else if (!silence && inSilence) {
      setInSilence(false);
      setSpeed(1);
      if (silenceEnteredAt !== null) {
        // wall-clock time saved ≈ duration_played / speed * (speed - 1)
        const silenceDuration = playedSeconds - silenceEnteredAt;
        const wallSaved = silenceDuration * (1 - 1 / RAMP_SPEED);
        setSavedApprox((v) => parseFloat((v + wallSaved).toFixed(1)));
        setSilenceEnteredAt(null);
      }
    }
  }

  return (
    <OptionCard
      letter="C"
      icon={<Gauge className="h-5 w-5" />}
      title="Speed Ramp"
      description={`Silent segments play at ${RAMP_SPEED}× speed instead of being cut — inspired by Jumpcutter. Feels more natural than a hard jump.`}
      accentColor="text-amber-400"
      badgeColor="bg-amber-500/20 border-amber-500/30"
      stats={[
        { label: "Current speed", value: `${speed}×` },
        { label: "Wall-time saved ≈", value: `${savedApprox.toFixed(1)}s` },
        { label: "Status", value: inSilence ? `🚀 ${RAMP_SPEED}× speed` : "▶ 1× normal" },
      ]}
    >
      <ReactPlayer
        url={VIDEO_URL}
        width="100%"
        height="100%"
        style={{ aspectRatio: "16/9" }}
        controls
        playing={playing}
        playbackRate={speed}
        light={!playing && POSTER}
        onClickPreview={() => setPlaying(true)}
        onProgress={handleProgress}
        progressInterval={100}
        config={{ playerVars: { modestbranding: 1, rel: 0 } } as any}
      />
    </OptionCard>
  );
}

// ── Option D – Browser Extension ──────────────────────────────────────────────
const EXTENSIONS = [
  {
    name: "Silence Remover",
    store: "Chrome Web Store",
    url: "https://chromewebstore.google.com/detail/silence-remover/aghkoafplblodgbbkkkmfbkepkjakbao",
    note: "Detects silence in the browser tab's audio and skips it in real-time. Works on any site.",
  },
  {
    name: "jumpcutter.me",
    store: "Web App",
    url: "https://jumpcutter.me",
    note: "Upload or paste a YouTube URL — produces a downloadable edited video file.",
  },
  {
    name: "Auto Speed (by Lexx)",
    store: "Chrome Web Store",
    url: "https://chromewebstore.google.com/detail/auto-speed/omegleonceafjhbimfpbpnihgfijmlbg",
    note: "Automatically speeds up YouTube when no speech is detected using the Web Audio API on the page's own tab context.",
  },
];

function OptionD() {
  const [playing, setPlaying] = useState(false);

  return (
    <OptionCard
      letter="D"
      icon={<Puzzle className="h-5 w-5" />}
      title="Browser Extension"
      description="No app modifications needed. Extensions hook into the tab's audio context (allowed because they share the same origin as the page) and detect silence in real-time."
      accentColor="text-emerald-400"
      badgeColor="bg-emerald-500/20 border-emerald-500/30"
      stats={[
        { label: "App changes", value: "None" },
        { label: "Works on", value: "Any YouTube" },
        { label: "Setup", value: "Install once" },
      ]}
    >
      <ReactPlayer
        url={VIDEO_URL}
        width="100%"
        height="100%"
        style={{ aspectRatio: "16/9" }}
        controls
        playing={playing}
        light={!playing && POSTER}
        onClickPreview={() => setPlaying(true)}
        config={{ playerVars: { modestbranding: 1, rel: 0 } } as any}
      />
      <div className="mt-4 space-y-2">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Compatible extensions
        </p>
        {EXTENSIONS.map((ext) => (
          <a
            key={ext.name}
            href={ext.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-start gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition-colors group"
          >
            <ExternalLink className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0 group-hover:text-foreground" />
            <div className="min-w-0">
              <p className="text-sm font-medium group-hover:text-foreground">
                {ext.name}
                <span className="ml-2 text-xs text-muted-foreground font-normal">
                  ({ext.store})
                </span>
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">{ext.note}</p>
            </div>
          </a>
        ))}
      </div>
    </OptionCard>
  );
}

// ── Shared card wrapper ────────────────────────────────────────────────────────
interface StatItem {
  label: string;
  value: string | number;
}

interface OptionCardProps {
  letter: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  accentColor: string;
  badgeColor: string;
  stats: StatItem[];
  children: React.ReactNode;
}

function OptionCard({
  letter,
  icon,
  title,
  description,
  accentColor,
  badgeColor,
  stats,
  children,
}: OptionCardProps) {
  return (
    <div className="rounded-xl border border-white/10 overflow-hidden bg-card">
      {/* Header */}
      <div className="flex items-start gap-4 p-5 border-b border-white/10 bg-white/5">
        <div className={cn("flex items-center justify-center w-10 h-10 rounded-lg border font-bold text-lg shrink-0", badgeColor, accentColor)}>
          {letter}
        </div>
        <div className="flex-1 min-w-0">
          <div className={cn("flex items-center gap-2 font-semibold text-base", accentColor)}>
            {icon}
            Option {letter} — {title}
          </div>
          <p className="text-sm text-muted-foreground mt-1 leading-relaxed">{description}</p>
        </div>
      </div>

      {/* Player + stats */}
      <div className="p-5 space-y-4">
        {/* Live stats */}
        <div className="grid grid-cols-3 gap-3">
          {stats.map((s) => (
            <div key={s.label} className="rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-center">
              <p className="text-xs text-muted-foreground">{s.label}</p>
              <p className={cn("text-sm font-semibold mt-0.5 tabular-nums", accentColor)}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* Video */}
        <div className="rounded-xl overflow-hidden bg-black border border-white/10">
          {children}
        </div>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
const TABS = [
  { id: "A", label: "Option A — Hard Skip" },
  { id: "C", label: "Option C — Speed Ramp" },
  { id: "D", label: "Option D — Extension" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function SilenceTestPage() {
  const [activeTab, setActiveTab] = useState<TabId>("A");

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Silence Removal — Test Lab</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Three approaches tested on the same video:{" "}
          <span className="text-white/80 font-medium">Linear Algebra 18.06SC — Lecture 1</span>
          {" "}(Cx5Z-OslNWE)
        </p>
      </div>

      {/* Analysis summary */}
      <div className="rounded-xl border border-white/10 bg-white/5 p-4">
        <div className="flex items-center gap-2 text-sm font-medium mb-3">
          <Info className="h-4 w-4 text-primary" />
          FFmpeg silencedetect analysis — <code className="text-xs bg-white/10 px-1.5 py-0.5 rounded">-40dB threshold, 0.8s min duration</code>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Video length", value: "7m 04s" },
            { label: "Silent segments", value: `${SILENCE.length}` },
            { label: "Total silence", value: `${TOTAL_SILENCE_S}s` },
            { label: "% silent", value: `${SILENCE_PCT}%` },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <p className="text-xs text-muted-foreground">{s.label}</p>
              <p className="text-lg font-bold text-primary mt-0.5">{s.value}</p>
            </div>
          ))}
        </div>
        <details className="mt-3">
          <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground select-none">
            Show all {SILENCE.length} silent segments
          </summary>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {SILENCE.map(([s, e], i) => (
              <span key={i} className="text-xs bg-white/10 rounded px-2 py-0.5 font-mono">
                {s.toFixed(1)}s → {e.toFixed(1)}s ({(e - s).toFixed(1)}s)
              </span>
            ))}
          </div>
        </details>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-white/5 border border-white/10 rounded-lg p-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-white/10"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Active panel */}
      {activeTab === "A" && <OptionA />}
      {activeTab === "C" && <OptionC />}
      {activeTab === "D" && <OptionD />}

      {/* Bottom note */}
      <div className="rounded-lg border border-white/10 bg-white/5 p-4 text-xs text-muted-foreground space-y-1">
        <p><span className="text-white/60 font-medium">Option A</span> — Best for eliminating dead air completely. Timestamps computed once per video, stored in DB alongside the video record.</p>
        <p><span className="text-white/60 font-medium">Option C</span> — More natural feel; no hard jump. Silence still plays but compressed. Works with same timestamps as A.</p>
        <p><span className="text-white/60 font-medium">Option D</span> — Zero app complexity. Users install an extension once and it works everywhere, not just here.</p>
      </div>
    </div>
  );
}
