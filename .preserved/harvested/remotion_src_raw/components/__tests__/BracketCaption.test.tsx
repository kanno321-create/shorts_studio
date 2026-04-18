import { vi, describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import React from "react";
import { BracketCaption } from "../BracketCaption";

// Mock remotion hooks — vitest pattern (not jest).
// useCurrentFrame=30 @ fps=30 → 1000ms "now".
vi.mock("remotion", () => ({
  AbsoluteFill: ({ children, style }: any) => <div style={style}>{children}</div>,
  useCurrentFrame: () => 30,
  useVideoConfig: () => ({ fps: 30 }),
  interpolate: (_t: number, _from: number[], to: number[]) => to[1],
}));

describe("BracketCaption", () => {
  it("renders text wrapped in parentheses", () => {
    const { getByTestId } = render(<BracketCaption text="테이저를 꺼낸다" />);
    const el = getByTestId("bracket-caption");
    expect(el.textContent).toBe("(테이저를 꺼낸다)");
  });

  it("returns null before startMs window", () => {
    // at frame 30, fps 30 → 1000ms "now"; startMs=5000 → below window → null
    const { queryByTestId } = render(<BracketCaption text="X" startMs={5000} endMs={8000} />);
    expect(queryByTestId("bracket-caption")).toBeNull();
  });

  it("returns null after endMs window", () => {
    // at 1000ms "now"; endMs=500 → past window → null
    const { queryByTestId } = render(<BracketCaption text="Y" startMs={0} endMs={500} />);
    expect(queryByTestId("bracket-caption")).toBeNull();
  });

  it("renders within active window", () => {
    // 1000ms is inside [500, 2000]
    const { getByTestId } = render(<BracketCaption text="현장 진입" startMs={500} endMs={2000} />);
    expect(getByTestId("bracket-caption").textContent).toBe("(현장 진입)");
  });
});
