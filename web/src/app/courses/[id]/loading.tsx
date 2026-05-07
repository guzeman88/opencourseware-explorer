import { CourseDetailSkeleton } from "@/components/ui/skeleton";

export default function CourseLoading() {
  return (
    <div className="max-w-screen-xl mx-auto px-4 md:px-8 py-8">
      <CourseDetailSkeleton />
    </div>
  );
}
