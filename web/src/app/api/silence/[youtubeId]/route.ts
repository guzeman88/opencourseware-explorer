import { NextRequest, NextResponse } from "next/server";

// Filler words/sounds to always skip regardless of duration
const FILLER_RE = /^(uh+|um+|ah+|er+|erm+|hmm+|mhm+|mm+|eh+|huh|ugh|oh|wow|so,?|right,?|okay,?|like,?|well,?|now,?|actually,?)$/i;

interface Seg {
  utf8?: string;
  tOffsetMs?: number;
}

interface CaptionEvent {
  tStartMs: number;
  dDurationMs?: number;
  segs?: Seg[];
}

interface WordToken {
  text: string;
  startMs: number;
  endMs: number;
  isFiller: boolean;
}

/**
 * Fetch the YouTube page HTML and extract the first English caption track URL.
 */
async function fetchCaptionTrackUrl(videoId: string): Promise<string | null> {
  let html: string;
  try {
    const res = await fetch(`https://www.youtube.com/watch?v=${videoId}&hl=en`, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        Accept: "text/html,application/xhtml+xml",
      },
      next: { revalidate: 3600 },
    });
    if (!res.ok) return null;
    html = await res.text();
  } catch {
    return null;
  }

  const match = html.match(/"captionTracks":\s*(\[[\s\S]*?\])\s*,\s*"audioTracks"/);
  if (!match) return null;

  try {
    const tracks: Array<{ baseUrl?: string; languageCode?: string; kind?: string }> =
      JSON.parse(match[1]);
    if (!tracks.length) return null;
    // Prefer ASR (auto-generated) English captions — they include per-word tOffsetMs timing.
    // Manual captions rarely have word-level offsets so gaps within phrases won't be detected.
    const asrEn = tracks.find((t) => t.languageCode?.startsWith("en") && t.kind === "asr");
    const manualEn = tracks.find((t) => t.languageCode?.startsWith("en"));
    const en = asrEn ?? manualEn ?? tracks[0];
    return en?.baseUrl ?? null;
  } catch {
    return null;
  }
}

/**
 * Build a word-level timeline from json3 caption events.
 * Uses tOffsetMs within each event for word-level timing (ASR captions).
 * Falls back to event-level timing for manual captions.
 */
function buildWordTimeline(events: CaptionEvent[]): WordToken[] {
  const words: WordToken[] = [];

  for (const event of events) {
    const segs = event.segs ?? [];
    if (!segs.length) continue;
    const eventStart = event.tStartMs;
    const eventDur = event.dDurationMs ?? 1500;

    for (let i = 0; i < segs.length; i++) {
      const seg = segs[i];
      const raw = (seg.utf8 ?? "").replace(/\n/g, " ").trim();
      if (!raw) continue;

      const wordStartMs = eventStart + (seg.tOffsetMs ?? 0);

      // Estimate word end: next seg's offset, or event end
      let wordEndMs: number;
      if (i + 1 < segs.length) {
        const next = segs[i + 1];
        wordEndMs = next.tOffsetMs != null
          ? eventStart + next.tOffsetMs
          : wordStartMs + 350;
      } else {
        wordEndMs = eventStart + eventDur;
      }
      wordEndMs = Math.max(wordEndMs, wordStartMs + 50);

      // Strip punctuation for filler matching
      const cleaned = raw.replace(/[.,!?;:]+$/, "");
      words.push({
        text: cleaned,
        startMs: wordStartMs,
        endMs: wordEndMs,
        isFiller: FILLER_RE.test(cleaned),
      });
    }
  }

  return words.sort((a, b) => a.startMs - b.startMs);
}

// Minimum silence/gap duration to skip (ms). Tiny word gaps are ignored —
// they're natural speech rhythm and cause seek-chain explosions if included.
const MIN_GAP_MS = 200;

/**
 * Compute all segments to skip: filler words + inter-word gaps >= MIN_GAP_MS.
 * Merges adjacent/overlapping segments.
 */
function computeSegments(words: WordToken[]): [number, number][] {
  if (!words.length) return [];

  const raw: [number, number][] = [];

  for (let i = 0; i < words.length; i++) {
    const w = words[i];

    // Skip filler words entirely regardless of duration
    if (w.isFiller) {
      raw.push([w.startMs, w.endMs]);
      continue;
    }

    // Gap between end of previous real word and start of this one —
    // only include if long enough to be a real pause, not natural word spacing
    if (i > 0) {
      const prev = words[i - 1];
      const gap = w.startMs - prev.endMs;
      if (gap >= MIN_GAP_MS) {
        raw.push([prev.endMs, w.startMs]);
      }
    }
  }

  // Sort and merge overlapping/touching segments
  raw.sort((a, b) => a[0] - b[0]);
  const merged: [number, number][] = [];
  for (const [s, e] of raw) {
    if (s >= e) continue; // skip zero-length
    if (merged.length && s <= merged[merged.length - 1][1] + 50) {
      merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], e);
    } else {
      merged.push([s, e]);
    }
  }

  // Convert ms → seconds
  return merged.map(([s, e]) => [s / 1000, e / 1000]);
}

async function computeSilence(trackUrl: string): Promise<[number, number][] | null> {
  let data: { events?: CaptionEvent[] };
  try {
    const res = await fetch(`${trackUrl}&fmt=json3`, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
      },
    });
    if (!res.ok) return null;
    data = await res.json();
  } catch {
    return null;
  }

  const events = (data.events ?? []).filter(
    (e): e is CaptionEvent & { dDurationMs: number } =>
      typeof e.dDurationMs === "number" && Array.isArray(e.segs) && e.segs.length > 0
  );

  const words = buildWordTimeline(events);
  return computeSegments(words);
}

export async function GET(
  _req: NextRequest,
  { params }: { params: { youtubeId: string } }
) {
  const { youtubeId } = params;

  if (!youtubeId || !/^[A-Za-z0-9_-]{6,20}$/.test(youtubeId)) {
    return NextResponse.json({ error: "Invalid video ID" }, { status: 400 });
  }

  try {
    const trackUrl = await fetchCaptionTrackUrl(youtubeId);
    if (!trackUrl) {
      return NextResponse.json(
        { segments: [] },
        { headers: { "Cache-Control": "public, max-age=3600" } }
      );
    }

    const segments = await computeSilence(trackUrl);
    return NextResponse.json(
      { segments: segments ?? [] },
      {
        headers: {
          "Cache-Control": "no-store",
        },
      }
    );
  } catch {
    return NextResponse.json({ segments: [] });
  }
}
