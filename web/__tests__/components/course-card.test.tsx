import { screen } from "@testing-library/react";
import { CourseCard } from "@/components/course-card";
import type { CourseSummary } from "@/types";
import { renderWithProviders } from "../test-utils";

const mockCourse: CourseSummary = {
  id: "1",
  title: "Introduction to Computer Science",
  slug: "intro-to-cs",
  level: "undergraduate",
  source_key: "mit_ocw",
  has_video_lectures: true,
  total_videos: 24,
  university_id: "u1",
  university_name: "MIT",
  university_slug: "mit",
  subjects: [],
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

// Stub next/image
jest.mock("next/image", () => ({
  __esModule: true,
  default: (props: any) => {
    // eslint-disable-next-line @next/next/no-img-element
    return <img {...props} alt={props.alt} />;
  },
}));

// Stub next/link
jest.mock("next/link", () => ({
  __esModule: true,
  default: ({ href, children, ...props }: any) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

describe("CourseCard", () => {
  it("renders course title", () => {
    renderWithProviders(<CourseCard course={mockCourse} />);
    expect(screen.getByText("Introduction to Computer Science")).toBeTruthy();
  });

  it("renders university name", () => {
    renderWithProviders(<CourseCard course={mockCourse} />);
    expect(screen.getAllByText("MIT")).toHaveLength(2);
  });

  it("links to course page", () => {
    renderWithProviders(<CourseCard course={mockCourse} />);
    const link = screen.getByRole("link");
    expect(link.getAttribute("href")).toBe("/courses/intro-to-cs");
  });

  it("shows video count badge", () => {
    renderWithProviders(<CourseCard course={mockCourse} />);
    expect(screen.getByText("24")).toBeTruthy();
  });

  it("offers a save-to-library action", () => {
    renderWithProviders(<CourseCard course={mockCourse} />);
    expect(screen.getByLabelText("Save to library")).toBeTruthy();
  });
});
