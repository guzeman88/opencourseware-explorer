"use client";

import { useCourse } from "@/hooks/use-courses";
import { useSilenceSkip } from "@/hooks/use-silence-skip";
import { useDynamicSilence } from "@/hooks/use-dynamic-silence";
import { CourseDetailSkeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { levelLabel, levelColor, formatDuration, thumbnailUrl, cn } from "@/lib/utils";
import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import {
  Play,
  ExternalLink,
  FileText,
  CheckSquare,
  Clock,
  Eye,
  ChevronDown,
  GraduationCap,
  ListVideo,
  Youtube,
  Scissors,
  Bookmark,
  ArrowLeft,
} from "lucide-react";
import { useLibraryStatus, useLibraryToggle } from "@/hooks/use-library";
import { useAuth } from "@/providers/auth-provider";
import { useAuthModal } from "@/providers/auth-modal-provider";
import dynamic from "next/dynamic";

const ReactPlayer = dynamic(() => import("react-player/youtube"), {
  ssr: false,
  loading: () => (
    <div className="aspect-video bg-black/80 rounded-xl flex items-center justify-center">
      <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  ),
});

/** Extract a YouTube playlist ID from any URL that contains ?list= or &list= */
function extractPlaylistId(url?: string | null): string | null {
  if (!url) return null;
  const m = url.match(/[?&]list=([A-Za-z0-9_-]+)/);
  return m?.[1] ?? null;
}

function SaveDetailButton({ courseId }: { courseId: string }) {
  const { token } = useAuth();
  const { openAuthModal } = useAuthModal();
  const { data: saved } = useLibraryStatus(courseId);
  const toggle = useLibraryToggle(courseId);

  if (!token) {
    return (
      <button
        onClick={openAuthModal}
        title="Save to library"
        className="shrink-0 mt-1 p-1.5 rounded-full text-white/50 hover:text-white transition-colors"
      >
        <Bookmark className="h-5 w-5" />
      </button>
    );
  }

  return (
    <button
      onClick={() => toggle.mutate(saved ?? false)}
      title={saved ? "Remove from library" : "Save to library"}
      className={cn(
        "shrink-0 mt-1 p-1.5 rounded-full transition-colors",
        saved ? "text-primary" : "text-white/50 hover:text-white"
      )}
    >
      <Bookmark className={cn("h-5 w-5", saved && "fill-current")} />
    </button>
  );
}

interface CoursePageProps {
  params: { id: string };
}

export default function CoursePage({ params }: CoursePageProps) {
  const router = useRouter();
  const { data: course, isLoading, error } = useCourse(params.id);
  const [activeVideoIndex, setActiveVideoIndex] = useState(0);
  const [showAllVideos, setShowAllVideos] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [skipSilence, setSkipSilence] = useState(false);
  const playerRef = useRef<any>(null);

  // Derive silence data before any early returns (Rules of Hooks)
  const activeVideo = course?.videos[activeVideoIndex];
  const dbSilenceSegments = activeVideo?.silence_segments ?? null;
  const activeYoutubeId = activeVideo?.youtube_id ?? null;

  // Fetch silence dynamically from YouTube captions (0.3s threshold, no DB needed).
  // This is the primary source; DB data is the fallback when dynamic fetch hasn't resolved yet.
  const { data: dynamicSegments } = useDynamicSilence(activeYoutubeId);
  const silenceSegments =
    dynamicSegments !== undefined ? dynamicSegments : dbSilenceSegments;

  const hasSilenceData = !!(silenceSegments && silenceSegments.length > 0);
  const { handleProgress, handleSeek } = useSilenceSkip(silenceSegments, skipSilence);

  if (isLoading) {
    return (
      <div className="max-w-screen-xl mx-auto px-4 md:px-8 py-8">
        <CourseDetailSkeleton />
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-muted-foreground">
        <p className="text-base font-semibold text-white/70">Course not found</p>
        <p className="text-sm">
          {error instanceof Error ? error.message : "No course exists with this ID."}
        </p>
      </div>
    );
  }

  // Resolve the best available playlist ID: stored field → extracted from source_url
  const resolvedPlaylistId =
    course.youtube_playlist_id ?? extractPlaylistId(course.source_url);

  const videoUrl = activeVideo
    ? `https://www.youtube.com/watch?v=${activeVideo.youtube_id}`
    : resolvedPlaylistId
    ? `https://www.youtube.com/playlist?list=${resolvedPlaylistId}`
    : null;

  // Use light-mode (click-to-play poster) only for single videos, not playlists
  // (react-player can't auto-fetch a playlist thumbnail)
  const isPlaylist = !activeVideo && !!resolvedPlaylistId;

  // Fallback: YouTube search for courses with no direct video link
  const youtubeSearchUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(
    `${course.title} ${course.university_name} lectures`
  )}`;
  const youtubeDirectUrl = resolvedPlaylistId
    ? `https://www.youtube.com/playlist?list=${resolvedPlaylistId}`
    : null;

  // Poster image: prefer stored thumbnail, fall back to YouTube thumbnail of first video
  const poster =
    thumbnailUrl(course) ??
    (course.videos[0]?.youtube_id
      ? `https://img.youtube.com/vi/${course.videos[0].youtube_id}/maxresdefault.jpg`
      : null);

  // Thumbnail for the active video (for sidebar)
  const videoThumb = (ytId: string) =>
    `https://img.youtube.com/vi/${ytId}/mqdefault.jpg`;

  const displayedVideos = showAllVideos
    ? course.videos
    : course.videos.slice(0, 15);

  return (
    <div className="min-h-screen">
      {/* ── Hero banner ─────────────────────────────────────────── */}
      <div className="relative w-full bg-black/90 border-b border-white/10">
        {poster && (
          <div className="absolute inset-0 overflow-hidden">
            <Image
              src={poster}
              alt=""
              fill
              className="object-cover opacity-20 blur-xl scale-110"
              unoptimized
            />
          </div>
        )}
        <div className="relative max-w-screen-xl mx-auto px-4 md:px-8 py-8 md:py-12">
          {/* Back button */}
          <button
            onClick={() => router.back()}
            className="flex items-center gap-1.5 text-sm text-white/60 hover:text-white transition-colors mb-5"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </button>
          <div className="flex flex-col md:flex-row gap-6 md:gap-10 items-start">
            {/* Info */}
            <div className="flex-1 space-y-3">
              <div className="flex items-start gap-3">
                <h1 className="flex-1 text-2xl md:text-4xl font-bold leading-tight tracking-tight">
                  {course.title}
                </h1>
                <SaveDetailButton courseId={course.id} />
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <span className={cn("px-2.5 py-0.5 rounded-full text-xs font-semibold", levelColor(course.level))}>
                  {levelLabel(course.level)}
                </span>
                {course.subjects.slice(0, 3).map((s) => (
                  <Badge key={s.id} variant="secondary" className="text-xs">
                    {s.name}
                  </Badge>
                ))}
              </div>

              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                <span className="font-semibold text-white/90 flex items-center gap-1.5">
                  <GraduationCap className="h-4 w-4 text-primary" />
                  {course.university_name}
                </span>
                {course.source_url && (
                  <a href={course.source_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-white/50 hover:text-white/80 transition-colors text-xs">
                    <ExternalLink className="h-3 w-3" />
                    Course Page
                  </a>
                )}
                {course.instructor && <span>by <span className="text-white/80">{course.instructor}</span></span>}
                {course.year && (
                  <span>{course.semester ? `${course.semester} ` : ""}{course.year}</span>
                )}
                {course.course_number && <span>#{course.course_number}</span>}
              </div>

              <div className="flex flex-wrap items-center gap-4 text-sm text-white/60">
                {course.total_videos > 0 && (
                  <span className="flex items-center gap-1.5">
                    <ListVideo className="h-4 w-4" />
                    {course.total_videos} lectures
                  </span>
                )}
                {course.total_duration_seconds > 0 && (
                  <span className="flex items-center gap-1.5">
                    <Clock className="h-4 w-4" />
                    {formatDuration(course.total_duration_seconds)}
                  </span>
                )}
                {course.view_count > 0 && (
                  <span className="flex items-center gap-1.5">
                    <Eye className="h-4 w-4" />
                    {course.view_count.toLocaleString()} views
                  </span>
                )}
              </div>

              {/* Action buttons */}
              <div className="flex flex-wrap gap-2 pt-1">
                {!videoUrl && (
                  // No stored video data — link directly to YouTube search
                  <Button size="sm" className="gap-1.5 bg-primary hover:bg-primary/90" asChild>
                    <a href={youtubeSearchUrl} target="_blank" rel="noopener noreferrer">
                      <Youtube className="h-4 w-4" />
                      Find on YouTube
                    </a>
                  </Button>
                )}
                {youtubeDirectUrl && !activeVideo && (
                  <Button variant="outline" size="sm" asChild className="gap-1.5 border-white/20 hover:bg-white/10">
                    <a href={youtubeDirectUrl} target="_blank" rel="noopener noreferrer">
                      <Youtube className="h-4 w-4" />
                      YouTube Playlist
                    </a>
                  </Button>
                )}
                {course.has_lecture_notes && course.lecture_notes_url && (
                  <Button variant="outline" size="sm" asChild className="gap-1.5 border-white/20 hover:bg-white/10">
                    <a href={course.lecture_notes_url} target="_blank" rel="noopener noreferrer">
                      <FileText className="h-4 w-4" />
                      Notes
                    </a>
                  </Button>
                )}
                {course.has_exams && course.exams_url && (
                  <Button variant="outline" size="sm" asChild className="gap-1.5 border-white/20 hover:bg-white/10">
                    <a href={course.exams_url} target="_blank" rel="noopener noreferrer">
                      <CheckSquare className="h-4 w-4" />
                      Exams
                    </a>
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Body ────────────────────────────────────────────────── */}
      <div className="max-w-screen-xl mx-auto px-4 md:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main column */}
          <div className="lg:col-span-2 space-y-6" id="player-section">
            {/* Video player */}
            {videoUrl ? (
              <div className="space-y-2">
                <div className="rounded-xl overflow-hidden shadow-2xl bg-black border border-white/10">
                  <ReactPlayer
                    ref={playerRef}
                    url={videoUrl}
                    width="100%"
                    height="100%"
                    style={{ aspectRatio: "16/9" }}
                    controls
                    playing={playing}
                    light={!playing && !isPlaylist && (poster ?? true)}
                    onClickPreview={() => setPlaying(true)}
                    onProgress={(s) =>
                      handleProgress(s, (t) => {
                        const ip = playerRef.current?.getInternalPlayer();
                        if (ip?.seekTo) { ip.seekTo(t, true); } else { playerRef.current?.seekTo(t, "seconds"); }
                      })
                    }
                    onSeek={handleSeek}
                    progressInterval={50}
                    config={{
                      playerVars: {
                        modestbranding: 1,
                        rel: 0,
                        ...(isPlaylist && resolvedPlaylistId
                          ? { list: resolvedPlaylistId, listType: "playlist" }
                          : {}),
                      },
                    }}
                  />
                </div>

                {/* Skip-silence toggle — only shown when silence data is available */}
                {hasSilenceData && (
                  <div className="flex justify-end">
                    <button
                      onClick={() => setSkipSilence((v) => !v)}
                      className={cn(
                        "flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border transition-colors",
                        skipSilence
                          ? "bg-primary/15 border-primary/40 text-primary"
                          : "border-white/10 text-white/40 hover:text-white/70 hover:border-white/20"
                      )}
                    >
                      <Scissors className="h-3 w-3" />
                      {skipSilence ? "Silence skipping on" : "Skip silence"}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="aspect-video bg-card/60 rounded-xl flex flex-col items-center justify-center gap-4 border border-white/10">
                <Youtube className="h-12 w-12 text-muted-foreground/30" />
                <div className="text-center space-y-1 px-6">
                  <p className="text-sm font-semibold">
                    {course.has_video_lectures ? "No lectures indexed yet" : "No video lectures"}
                  </p>
                  <p className="text-xs text-muted-foreground max-w-xs">
                    {course.has_video_lectures
                      ? "Video lectures exist for this course but haven't been imported yet."
                      : "This course provides notes, readings, and exams but no video content."}
                  </p>
                </div>
                {course.has_video_lectures && (
                  <a
                    href={youtubeSearchUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors shadow-lg"
                  >
                    <Youtube className="h-4 w-4" />
                    Search on YouTube
                  </a>
                )}
              </div>
            )}

            {/* Active video title */}
            {activeVideo && (
              <div className="flex items-start gap-2">
                <Play className="h-4 w-4 text-primary mt-0.5 shrink-0 fill-current" />
                <p className="text-sm font-medium text-white/80">
                  Lecture {activeVideoIndex + 1}: {activeVideo.title}
                </p>
              </div>
            )}


          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            {course.videos.length > 0 ? (
              <div className="rounded-xl border border-white/10 overflow-hidden">
                <div className="bg-white/5 px-4 py-3 border-b border-white/10">
                  <h2 className="font-semibold text-sm flex items-center gap-2">
                    <ListVideo className="h-4 w-4 text-primary" />
                    Lectures
                    <span className="ml-auto text-xs text-muted-foreground font-normal">
                      {course.videos.length} total
                    </span>
                  </h2>
                </div>
                <div className="divide-y divide-white/5 max-h-[520px] overflow-y-auto">
                  {displayedVideos.map((video, i) => (
                    <button
                      key={video.id}
                      onClick={() => { setActiveVideoIndex(i); setPlaying(true); }}
                      className={cn(
                        "w-full flex items-start gap-3 p-3 text-left transition-colors",
                        activeVideoIndex === i
                          ? "bg-primary/15 border-l-2 border-primary"
                          : "hover:bg-white/5 border-l-2 border-transparent"
                      )}
                    >
                      {/* Thumbnail */}
                      <div className="relative shrink-0 w-16 rounded overflow-hidden bg-black/50">
                        <Image
                          src={videoThumb(video.youtube_id)}
                          alt=""
                          width={64}
                          height={36}
                          className="object-cover w-16 h-9"
                          unoptimized
                        />
                        {activeVideoIndex === i && (
                          <div className="absolute inset-0 flex items-center justify-center bg-black/40">
                            <Play className="h-3 w-3 fill-white text-white" />
                          </div>
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-medium line-clamp-2 leading-snug">
                          {i + 1}. {video.title}
                        </p>
                        {video.duration_seconds && (
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {formatDuration(video.duration_seconds)}
                          </p>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
                {course.videos.length > 15 && (
                  <div className="p-2 border-t border-white/10">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="w-full text-xs"
                      onClick={() => setShowAllVideos((v) => !v)}
                    >
                      {showAllVideos
                        ? "Show less"
                        : `Show all ${course.videos.length} lectures`}
                      <ChevronDown className={cn("h-3.5 w-3.5 ml-1 transition-transform", showAllVideos && "rotate-180")} />
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="rounded-xl border border-white/10 overflow-hidden">
                <div className="bg-white/5 px-4 py-3 border-b border-white/10">
                  <h2 className="font-semibold text-sm flex items-center gap-2 text-white/50">
                    <ListVideo className="h-4 w-4" />
                    Episodes not indexed
                  </h2>
                </div>
                <div className="p-4 space-y-3">
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {course.has_video_lectures
                      ? "Lecture videos for this course haven't been imported yet."
                      : "No video lectures for this course."}
                  </p>
                  {youtubeDirectUrl && (
                    <a
                      href={youtubeDirectUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex w-full items-center justify-center gap-2 bg-red-600/15 hover:bg-red-600/25 border border-red-600/30 text-red-400 text-xs font-semibold px-3 py-2 rounded-lg transition-colors"
                    >
                      <Youtube className="h-3.5 w-3.5" />
                      Open Playlist on YouTube
                    </a>
                  )}
                  {course.has_video_lectures && (
                    <a
                      href={youtubeSearchUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex w-full items-center justify-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white/50 text-xs font-semibold px-3 py-2 rounded-lg transition-colors"
                    >
                      <Youtube className="h-3.5 w-3.5" />
                      Search on YouTube
                    </a>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
