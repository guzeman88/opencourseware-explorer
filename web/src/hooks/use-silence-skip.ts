import { useRef, useCallback } from "react";

/** [start_seconds, end_seconds] */
export type SilenceSegment = [number, number];

/**
 * How many seconds BEFORE a silence starts to trigger the seek.
 * YouTube iframe seeks take ~150–250 ms, so firing 150 ms early means
 * the seek lands right as the silence begins → zero audible gap.
 * Segments are now >= 200 ms, so 150 ms lead won't fire before silence starts.
 */
const LEAD_SECS = 0.15;

/**
 * Hook that drives the hard-skip silence engine.
 *
 * Usage:
 *   const { handleProgress, handleSeek } = useSilenceSkip(video.silence_segments, enabled);
 *
 *   <ReactPlayer
 *     onProgress={(s) => handleProgress(s, (t) => playerRef.current?.seekTo(t, "seconds"))}
 *     onSeek={handleSeek}
 *     progressInterval={100}
 *   />
 */
export function useSilenceSkip(
  segments: SilenceSegment[] | null | undefined,
  enabled: boolean
) {
  const lockRef = useRef(false);
  const lastLandRef = useRef(-1);
  /**
   * Timestamp (ms) of the last programmatic seekTo() call.
   * YouTube's iframe fires onSeek 300–600 ms after seekTo() completes —
   * often long after the 250 ms lock expires — so we can't use lockRef here.
   * Instead we ignore any onSeek that arrives within 1 s of our own seek.
   */
  const lastSeekAtRef = useRef(0);

  /** Call from ReactPlayer's onSeek to reset state after a manual user seek. */
  const handleSeek = useCallback(() => {
    // Ignore the delayed onSeek event that YouTube fires after our own seekTo().
    if (Date.now() - lastSeekAtRef.current < 1000) return;
    lastLandRef.current = -1;
  }, []);

  /**
   * Call from ReactPlayer's onProgress.
   * seekTo receives the target time in seconds.
   */
  const handleProgress = useCallback(
    (
      { playedSeconds }: { playedSeconds: number },
      seekTo: (seconds: number) => void
    ) => {
      if (!enabled || !segments?.length || lockRef.current) return;

      // Find the next silence we haven't already jumped past
      const seg = segments.find(
        ([s, e]) =>
          playedSeconds >= s - LEAD_SECS &&
          playedSeconds < e &&
          e > lastLandRef.current
      );
      if (!seg) return;

      lockRef.current = true;

      // Chain consecutive silences that are very close together into one jump.
      // Handles clusters like [20.8, 23.5] → [24.3, 25.1] with only a 0.8s gap.
      let landAt = seg[1] + 0.05;
      let cursor: SilenceSegment = seg;
      // Small chain window — only merge segments that are essentially adjacent.
      // A large window (2 s) would chain ALL word-level segments, skipping the whole video.
      let next = segments.find(([s]) => s > cursor[1] && s <= landAt + 0.2);
      while (next) {
        landAt = next[1] + 0.05;
        cursor = next;
        next = segments.find(([s]) => s > cursor[1] && s <= landAt + 2.0);
      }

      lastLandRef.current = landAt;
      lastSeekAtRef.current = Date.now(); // record BEFORE calling seekTo
      seekTo(landAt);

      // Keep lock on for 500 ms — longer than YouTube's typical seek latency
      // (150–300 ms) so a rapid second progress tick can't re-trigger.
      setTimeout(() => {
        lockRef.current = false;
      }, 500);
    },
    [enabled, segments]
  );

  return { handleProgress, handleSeek };
}
