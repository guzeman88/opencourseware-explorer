import { render, screen, fireEvent } from "@testing-library/react";
import { Navbar } from "@/components/navbar";

// Stub next/navigation
const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ push: mockPush }),
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

describe("Navbar", () => {
  beforeEach(() => {
    mockPush.mockClear();
    render(<Navbar />);
  });

  it("renders logo text", () => {
    expect(screen.getByText("OCW Explorer")).toBeTruthy();
  });

  it("renders navigation links", () => {
    expect(screen.getByText("All Courses")).toBeTruthy();
    expect(screen.getByText("Universities")).toBeTruthy();
    expect(screen.getByText("Subjects")).toBeTruthy();
  });

  it("renders search input", () => {
    const input = screen.getByPlaceholderText("Search courses...");
    expect(input).toBeTruthy();
  });

  it("navigates on search submit", () => {
    const input = screen.getByPlaceholderText("Search courses...");
    fireEvent.change(input, { target: { value: "algorithms" } });
    fireEvent.submit(input.closest("form")!);
    expect(mockPush).toHaveBeenCalledWith("/search?q=algorithms");
  });
});
