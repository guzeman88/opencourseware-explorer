import { useQuery } from "@tanstack/react-query";

/**
 * Fetch silence segments for a YouTube video on-demand via the /api/silence route.
 * This computes gaps from YouTube captions (≥0.3s) server-side, no database needed.
 * Results are cached client-side for 24 hours.
 */
export function useDynamicSilence(youtubeId: string | null | undefined) {
  return useQuery<[number, number][] | null>({
    queryKey: ["silence-dynamic-v5", youtubeId],
    queryFn: async () => {
      if (!youtubeId) return null;
      const res = await fetch(`/api/silence/${encodeURIComponent(youtubeId)}?v=5`);
      if (!res.ok) return null;
      const data = await res.json();
      const segs = data?.segments;
      return Array.isArray(segs) && segs.length > 0
        ? (segs as [number, number][])
        : null;
    },
    enabled: !!youtubeId,
    staleTime: 0,
    gcTime: 5 * 60 * 1000,
    retry: false,
  });
}
