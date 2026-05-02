import { HeroBanner } from "@/components/hero-banner";
import { CourseRow } from "@/components/course-row";
import { UniversityGrid } from "@/components/university-grid";

export default function HomePage() {
  return (
    <div className="space-y-0">
      {/* Netflix-style hero */}
      <HeroBanner />

      {/* Course rows by category */}
      <div className="px-4 md:px-8 lg:px-12 space-y-10 pb-16 -mt-32 relative z-10">
        <CourseRow
          title="Featured Courses"
          queryKey="featured"
          fetchType="featured"
          priority
        />
        <CourseRow
          title="Computer Science"
          queryKey="cs"
          fetchType="subject"
          subjectSlug="computer-science"
        />
        <CourseRow
          title="Mathematics"
          queryKey="math"
          fetchType="subject"
          subjectSlug="mathematics"
        />
        <CourseRow
          title="Physics"
          queryKey="physics"
          fetchType="subject"
          subjectSlug="physics"
        />
        <CourseRow
          title="MIT OpenCourseWare"
          queryKey="mit"
          fetchType="university"
          universitySlug="mit"
        />
        <CourseRow
          title="Stanford University"
          queryKey="stanford"
          fetchType="university"
          universitySlug="stanford"
        />
        <CourseRow
          title="Harvard University"
          queryKey="harvard"
          fetchType="university"
          universitySlug="harvard"
        />
        <CourseRow
          title="NPTEL — IIT/IISc"
          queryKey="nptel"
          fetchType="university"
          universitySlug="nptel"
        />
        <CourseRow
          title="UC Berkeley"
          queryKey="berkeley"
          fetchType="university"
          universitySlug="berkeley"
        />
        <CourseRow
          title="Machine Learning & AI"
          queryKey="ml"
          fetchType="subject"
          subjectSlug="machine-learning"
        />
        <CourseRow
          title="Graduate Courses"
          queryKey="grad"
          fetchType="level"
          level="graduate"
        />

        {/* University grid */}
        <section>
          <h2 className="text-xl font-semibold text-foreground mb-4">
            Browse by University
          </h2>
          <UniversityGrid />
        </section>
      </div>
    </div>
  );
}
