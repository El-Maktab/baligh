import { expect, test, type Page } from "@playwright/test";

async function activateLandingSections(page: Page) {
  for (const selector of ["#features", "#team"]) {
    await page.locator(selector).scrollIntoViewIfNeeded();
    await page.waitForTimeout(650);
  }
  await page.evaluate(() => window.scrollTo({ top: 0 }));
  await page.waitForTimeout(200);
}

test("landing page renders in both themes", async ({ page }, testInfo) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "مساعدك الذكي",
  );
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");

  await page.evaluate(() => localStorage.setItem("baligh-theme", "light"));
  await page.reload();
  await activateLandingSections(page);
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page).toHaveScreenshot(
    `holding-light-${testInfo.project.name}.png`,
    {
      fullPage: true,
    },
  );

  await page.evaluate(() => localStorage.setItem("baligh-theme", "dark"));
  await page.reload();
  await activateLandingSections(page);
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page).toHaveScreenshot(
    `holding-dark-${testInfo.project.name}.png`,
    {
      fullPage: true,
    },
  );
});

test("landing interactions and viewport sections are active", async ({
  page,
}) => {
  await page.goto("/");

  const sectionHeights = await page
    .locator(".landing-section")
    .evaluateAll((sections) =>
      sections.map((section) => section.getBoundingClientRect().height),
    );
  const viewportHeight = await page.evaluate(() => window.innerHeight);
  expect(sectionHeights).toHaveLength(3);
  expect(sectionHeights.every((height) => height >= viewportHeight)).toBe(true);
  await expect(page.locator("html")).toHaveCSS("scroll-behavior", "smooth");

  await expect(page.locator(".hero-letter")).toHaveCount(3);
  const primaryButton = page.getByRole("button", { name: "ابدأ الكتابة الآن" });
  await primaryButton.hover();
  await expect(page.locator(".arabic-confetti__letter")).toHaveCount(13);
  await primaryButton.click();
  await page.getByRole("button", { name: "شاهد كيف يعمل" }).click();
  await page.getByRole("button", { name: "دخول كضيف" }).click();
  expect(await page.evaluate(() => window.scrollY)).toBeLessThan(2);
});

test("preview showcase documents foundations and mixed text", async ({
  page,
}) => {
  await page.goto("/design-system");

  await expect(
    page.getByRole("heading", { name: "نَهْجُ التَّصْمِيم." }),
  ).toBeVisible();
  await expect(page.getByText("Baligh 1.0", { exact: false })).toHaveAttribute(
    "dir",
    "auto",
  );
});
