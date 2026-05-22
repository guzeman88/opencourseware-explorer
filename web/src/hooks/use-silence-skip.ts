import { useRef, useCallback } from "react";

/** [start_seconds, end_seconds] */
export type SilenceSegment = [number, number];

/**
 * How many seconds BEFORE a silence starts to trigger the seek.
 * YouTube iframe seeks take ~150–250 ms, so firing 350 ms early means
 * the seek lands right as the silence begins → zero audible gap.
 */
const LEAD_SECS = 0.35;

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

  /** Call from ReactPlayer's onSeek to reset state after a manual user seek. */
  const handleSeek = useCallback(() => {
    if (lockRef.current) return; // our own programmatic seek — ignore
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
      let next = segments.find(([s]) => s > cursor[1] && s <= landAt + 2.0);
      while (next) {
        landAt = next[1] + 0.05;
        cursor = next;
        next = segments.find(([s]) => s > cursor[1] && s <= landAt + 2.0);
      }

      lastLandRef.current = landAt;
      seekTo(landAt);

      // Release lock after seek completes (~250 ms)
      setTimeout(() => {
        lockRef.current = false;
      }, 250);
    },
    [enabled, segments]
  );

  return { handleProgress, handleSeek };
}
