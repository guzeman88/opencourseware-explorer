"use client";

import { useCourse } from "@/hooks/use-courses";
import { CourseDetailSkeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { levelLabel, levelColor, formatDuration, cn } from "@/lib/utils";
import { useState } from "react";
import {
  Play,
  ExternalLink,
  BookOpen,
  FileText,
  CheckSquare,
  Clock,
  Eye,
  ChevronDown,
} from "lucide-react";
import dynamic from "next/dynamic";

const ReactPlayer = dynamic(() => import("react-player/youtube"), {
  ssr: false,
  loading: () => (
    <div className="aspect-video bg-black/50 rounded-lg flex items-center justify-center">
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

  const displayedVideos = showAllVideos
    ? course.videos
    : course.videos.slice(0, 12);

  return (
    <div className="max-w-screen-xl mx-auto px-4 md:px-8 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Video player */}
          {videoUrl ? (
            <div className="rounded-lg overflow-hidden shadow-2xl">
              <ReactPlayer
                url={videoUrl}
                width="100%"
                height="100%"
                style={{ aspectRatio: "16/9" }}
                controls
                playing={false}
                config={{
                  playerVars: {
                    modestbranding: 1,
                    rel: 0,
                  },
                }}
              />
            </div>
          ) : (
            <div className="aspect-video bg-card rounded-lg flex items-center justify-center border border-border">
              <div className="text-center text-muted-foreground space-y-2">
                <BookOpen className="h-12 w-12 mx-auto opacity-50" />
                <p>No video available</p>
              </div>
            </div>
          )}

          {/* Active video title */}
          {activeVideo && (
            <p className="text-sm text-muted-foreground">
              Lecture {activeVideoIndex + 1}: {activeVideo.title}
            </p>
          )}

          {/* Course title & meta */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className={cn(
                  "px-2 py-0.5 rounded-full text-xs font-medium",
                  levelColor(course.level)
                )}
              >
                {levelLabel(course.level)}
              </span>
              {course.subjects.map((s) => (
                <Badge key={s.id} variant="secondary">
                  {s.name}
                </Badge>
              ))}
            </div>

            <h1 className="text-2xl md:text-3xl font-bold">{course.title}</h1>

            <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
              <span className="font-medium text-foreground">
                {course.university_name}
              </span>
              {course.instructor && <span>by {course.instructor}</span>}
              {course.year && (
                <span>
                  {course.semester ? `${course.semester} ` : ""}
                  {course.year}
                </span>
              )}
              {course.course_number && (
                <span>Course {course.course_number}</span>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
              {course.total_videos > 0 && (
                <span className="flex items-center gap-1">
                  <Play className="h-3.5 w-3.5" />
                  {course.total_videos} lectures
                </span>
              )}
              {course.total_duration_seconds > 0 && (
                <span className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" />
                  {formatDuration(course.total_duration_seconds)}
                </span>
              )}
              {course.view_count > 0 && (
                <span className="flex items-center gap-1">
                  <Eye className="h-3.5 w-3.5" />
                  {course.view_count.toLocaleString()} views
                </span>
              )}
            </div>
          </div>

          {/* Description */}
          {course.description && (
            <div className="prose prose-sm prose-invert max-w-none">
              <h2 className="text-lg font-semibold">About this course</h2>
              <p className="text-muted-foreground leading-relaxed whitespace-pre-line">
                {course.description}
              </p>
            </div>
          )}

          {/* Materials */}
          <div className="flex flex-wrap gap-3">
            {course.source_url && (
              <Button variant="outline" size="sm" asChild>
                <a
                  href={course.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="h-4 w-4" />
                  Course Page
                </a>
              </Button>
            )}
            {course.has_lecture_notes && course.lecture_notes_url && (
              <Button variant="outline" size="sm" asChild>
                <a
                  href={course.lecture_notes_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <FileText className="h-4 w-4" />
                  Lecture Notes
                </a>
              </Button>
            )}
            {course.has_exams && course.exams_url && (
              <Button variant="outline" size="sm" asChild>
                <a
                  href={course.exams_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <CheckSquare className="h-4 w-4" />
                  Exams
                </a>
              </Button>
            )}
          </div>
        </div>

        {/* Video list sidebar */}
        {course.videos.length > 0 && (
          <div className="space-y-3">
            <h2 className="font-semibold text-lg">
              Lectures ({course.videos.length})
            </h2>
            <div className="space-y-1 max-h-[600px] overflow-y-auto pr-1">
              {displayedVideos.map((video, i) => (
                <button
                  key={video.id}
                  onClick={() => setActiveVideoIndex(i)}
                  className={cn(
                    "w-full flex items-start gap-3 p-2.5 rounded-lg text-left transition-colors",
                    activeVideoIndex === i
                      ? "bg-primary/20 border border-primary/30"
                      : "hover:bg-accent/50"
                  )}
                >
                  <span className="text-xs text-muted-foreground w-6 shrink-0 pt-0.5 text-right">
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium line-clamp-2 leading-snug">
                      {video.title}
                    </p>
                    {video.duration_seconds && (
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {formatDuration(video.duration_seconds)}
                      </p>
                    )}
                  </div>
                  {activeVideoIndex === i && (
                    <Play className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5 fill-current" />
                  )}
                </button>
              ))}
            </div>

            {course.videos.length > 12 && (
              <Button
                variant="ghost"
                size="sm"
                className="w-full"
                onClick={() => setShowAllVideos((v) => !v)}
              >
                {showAllVideos
                  ? "Show less"
                  : `Show all ${course.videos.length} lectures`}
                <ChevronDown
                  className={cn(
                    "h-4 w-4 transition-transform",
                    showAllVideos && "rotate-180"
                  )}
                />
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
