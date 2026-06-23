import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AssistantMark, BalighWordmark } from "./BrandMarks";

describe("brand marks", () => {
  it("exposes meaningful accessible names", () => {
    render(
      <>
        <BalighWordmark />
        <AssistantMark />
      </>,
    );

    expect(screen.getByRole("img", { name: "بليغ" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "مساعد بليغ" })).toBeInTheDocument();
  });
});
