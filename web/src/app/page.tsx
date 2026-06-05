import { HomeCourseRows } from "@/components/home-course-rows";
import { filterCatalogReadyPage } from "@/lib/catalog-quality";
import type { CourseSummary, PaginatedList } from "@/types";

const API =
  process.env.API_UPSTREAM ||
  process.env.NEXT_PUBLIC_API_URL ||
  "https://opencourseware-api.onrender.com";

async function serverFetch(path: string): Promise<PaginatedList<CourseSummary> | undefined> {
  try {
    const res = await fetch(`${API}/api/v1${path}`, { next: { revalidate: 300 } });
    if (!res.ok) return undefined;
    return filterCatalogReadyPage(await res.json());
  } catch {
    return undefined;
  }
}

export default async function HomePage() {
  const [featured, computerScience] = await Promise.all([
    serverFetch("/courses/featured?page_size=18&has_video_lectures=true&catalog_ready=true"),
    serverFetch("/courses?subject_slug=computer-science&page_size=18&sort_by=view_count&sort_dir=desc&has_video_lectures=true&catalog_ready=true"),
  ]);

  return (
    <div className="space-y-0">
      <div className="px-4 md:px-8 lg:px-12 space-y-10 pb-16 pt-8 relative z-10">
        <HomeCourseRows featured={featured} computerScience={computerScience} />
      </div>
    </div>
  );
}
