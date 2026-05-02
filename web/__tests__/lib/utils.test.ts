import { formatDuration, formatNumber, levelLabel, levelColor, sourceLabel, cn } from "@/lib/utils";

describe("formatDuration", () => {
  it("returns empty string for 0", () => {
    expect(formatDuration(0)).toBe("");
  });

  it("formats seconds only", () => {
    expect(formatDuration(45)).toBe("0m 45s");
  });

  it("formats minutes and seconds", () => {
    expect(formatDuration(90)).toBe("1m 30s");
  });

  it("formats hours and minutes", () => {
    expect(formatDuration(3661)).toBe("1h 1m");
  });
});

describe("formatNumber", () => {
  it("formats thousands", () => {
    expect(formatNumber(1500)).toBe("1.5K");
  });

  it("formats millions", () => {
    expect(formatNumber(2_000_000)).toBe("2.0M");
  });

  it("passes small numbers through", () => {
    expect(formatNumber(999)).toBe("999");
  });
});

describe("levelLabel", () => {
  it("maps all levels", () => {
    expect(levelLabel("undergraduate")).toBe("Undergraduate");
    expect(levelLabel("graduate")).toBe("Graduate");
    expect(levelLabel("professional")).toBe("Professional");
    expect(levelLabel("other")).toBe("General");
  });

  it("returns unknown levels unchanged", () => {
    expect(levelLabel("unknown")).toBe("unknown");
  });
});

describe("sourceLabel", () => {
  it("maps known sources", () => {
    expect(sourceLabel("mit_ocw")).toBe("MIT OCW");
    expect(sourceLabel("yale_ocw")).toBe("Yale");
    expect(sourceLabel("stanford")).toBe("Stanford");
    expect(sourceLabel("nptel")).toBe("NPTEL");
    expect(sourceLabel("berkeley")).toBe("UC Berkeley");
    expect(sourceLabel("harvard")).toBe("Harvard");
  });
});

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("a", "b")).toBe("a b");
    expect(cn("px-2", "px-4")).toBe("px-4");
  });
});
