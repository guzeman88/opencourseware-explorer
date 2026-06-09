import type { Metadata } from "next";

// Cache course metadata at the page segment level for 1 hour
export const revalidate = 3600;

const BASE_URL =
  process.env.API_UPSTREAM ||
  process.env.NEXT_PUBLIC_API_URL ||
  "https://opencourseware-api.onrender.com";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  try {
    const { id } = await params;
    const res = await fetch(`${BASE_URL}/api/v1/courses/${id}`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) throw new Error("not found");
    const course = await res.json();

    const title = `${course.title} — The Commons`;
    const description =
      course.description?.slice(0, 160) ??
      `Free course from ${course.university_name}`;
    const image =
      course.thumbnail_url ??
      (course.youtube_playlist_id
        ? `https://i.ytimg.com/vi/${course.youtube_playlist_id}/hqdefault.jpg`
        : undefined);

    return {
      title,
      description,
      openGraph: {
        title,
        description,
        type: "website",
        ...(image ? { images: [{ url: image, width: 480, height: 360 }] } : {}),
      },
      twitter: {
        card: "summary_large_image",
        title,
        description,
        ...(image ? { images: [image] } : {}),
      },
    };
  } catch {
    return {
      title: "Course — The Commons",
      description: "Browse free university courses on The Commons.",
    };
  }
}

export default function CourseLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
