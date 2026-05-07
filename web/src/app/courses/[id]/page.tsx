"use client";

import { useCourse } from "@/hooks/use-courses";
import { CourseDetailSkeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { levelLabel, levelColor, formatDuration, thumbnailUrl, cn } from "@/lib/utils";
import { useState } from "react";
import Image from "next/image";
import {
  Play,
  ExternalLink,
  BookOpen,
  FileText,
  CheckSquare,
  Clock,
  Eye,
  ChevronDown,
  GraduationCap,
  ListVideo,
} from "lucide-react";
import dynamic from "next/dynamic";

const ReactPlayer = dynamic(() => import("react-player/youtube"), {
  ssr: false,
  loading: () => (
    <div className="aspect-video bg-black/80 rounded-xl flex items-center justify-center">
      <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  ),
});

interface CoursePageProps {
  params: { id: string };
}

export default function CoursePage({ params }: CoursePageProps) {
  const { data: course, isLoading, error } = useCourse(params.id);
  const [activeVideoIndex, setActiveVideoIndex] = useState(0);
  const [showAllVideos, setShowAllVideos] = useState(false);
  const [playing, setPlaying] = useState(false);

  if (isLoading) {
    return (
      <div className="max-w-screen-xl mx-auto px-4 md:px-8 py-8">
        <CourseDetailSkeleton />
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        Course not found.
      </div>
    );
  }

  const activeVideo = course.videos[activeVideoIndex];
  const videoUrl = activeVideo
    ? `https://www.youtube.com/watch?v=${activeVideo.youtube_id}`
    : course.youtube_playlist_id
    ? `https://www.youtube.com/playlist?list=${course.youtube_playlist_id}`
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
          <div className="flex flex-col md:flex-row gap-6 md:gap-10 items-start">
            {/* Thumbnail */}
            {poster && (
              <div className="shrink-0 w-full md:w-56 rounded-xl overflow-hidden shadow-2xl border border-white/10">
                <Image
                  src={poster}
                  alt={course.title}
                  width={224}
                  height={126}
                  className="w-full object-cover"
                  unoptimized
                />
              </div>
            )}

            {/* Info */}
            <div className="flex-1 space-y-3">
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

              <h1 className="text-2xl md:text-4xl font-bold leading-tight tracking-tight">
                {course.title}
              </h1>

              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                <span className="font-semibold text-white/90 flex items-center gap-1.5">
                  <GraduationCap className="h-4 w-4 text-primary" />
                  {course.university_name}
                </span>
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
                {videoUrl && (
                  <Button
                    size="sm"
                    className="gap-1.5 bg-primary hover:bg-primary/90"
                    onClick={() => { setPlaying(true); document.getElementById("player-section")?.scrollIntoView({ behavior: "smooth" }); }}
                  >
                    <Play className="h-4 w-4 fill-current" />
                    Watch Now
                  </Button>
                )}
                {course.source_url && (
                  <Button variant="outline" size="sm" asChild className="gap-1.5 border-white/20 hover:bg-white/10">
                    <a href={course.source_url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-4 w-4" />
                      Course Page
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
              <div className="rounded-xl overflow-hidden shadow-2xl bg-black border border-white/10">
                <ReactPlayer
                  url={videoUrl}
                  width="100%"
                  height="100%"
                  style={{ aspectRatio: "16/9" }}
                  controls
                  playing={playing}
                  light={!playing && (poster ?? true)}
                  onClickPreview={() => setPlaying(true)}
                  config={{
                    playerVars: { modestbranding: 1, rel: 0 },
                  }}
                />
              </div>
            ) : (
              <div className="aspect-video bg-card rounded-xl flex items-center justify-center border border-border">
                <div className="text-center text-muted-foreground space-y-3">
                  <BookOpen className="h-14 w-14 mx-auto opacity-30" />
                  <p className="text-sm">No video available</p>
                </div>
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

            {/* Description */}
            {course.description && (
              <div className="rounded-xl bg-white/5 border border-white/10 p-5 space-y-2">
                <h2 className="text-base font-semibold">About this course</h2>
                <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
                  {course.description}
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
              <div className="rounded-xl border border-white/10 bg-white/5 p-6 text-center text-sm text-muted-foreground space-y-2">
                <BookOpen className="h-8 w-8 mx-auto opacity-30" />
                <p>No lecture videos available</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
