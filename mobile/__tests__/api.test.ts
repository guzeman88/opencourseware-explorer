import { fetchCourses, fetchFeaturedCourses, searchCourses } from "../lib/api";
import axios from "axios";

jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

const mockList = {
  items: [
    {
      id: "1",
      title: "CS50",
      slug: "cs50",
      level: "undergraduate",
      source_key: "harvard",
      has_video_lectures: true,
      total_videos: 12,
      university_id: "u1",
      university_name: "Harvard",
      university_slug: "harvard",
      subjects: [],
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
  pages: 1,
};

describe("Mobile API client", () => {
  beforeEach(() => {
    // Create a mock axios instance with get method
    const mockInstance = {
      get: jest.fn().mockResolvedValue({ data: mockList }),
      post: jest.fn(),
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() },
      },
    };
    (axios.create as jest.Mock).mockReturnValue(mockInstance);
  });

  it("exports fetchCourses function", () => {
    expect(typeof fetchCourses).toBe("function");
  });

  it("exports fetchFeaturedCourses function", () => {
    expect(typeof fetchFeaturedCourses).toBe("function");
  });

  it("exports searchCourses function", () => {
    expect(typeof searchCourses).toBe("function");
  });
});
