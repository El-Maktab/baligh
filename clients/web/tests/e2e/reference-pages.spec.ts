import { expect, test, type Page } from "@playwright/test";

async function openEditorReference(
  page: Page,
  projectName: string,
  name: RegExp,
) {
  await page.goto("/editor");
  if (projectName === "mobile-chromium") {
    await page.getByRole("button", { name: "المسودات" }).click();
    await page.getByRole("dialog").getByRole("link", { name }).click();
  } else {
    await page.getByRole("link", { name }).click();
  }
}

test("dictionary navigation, keyboard search, and recent searches work", async ({
  page,
}, testInfo) => {
  await openEditorReference(page, testInfo.project.name, /المعجم/);
  await expect(page).toHaveURL(/\/mo3gm$/);
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");

  const search = page.getByRole("searchbox", { name: "ابحث في المعجم" });
  await search.fill("جِـذْر");
  await search.press("Enter");
  await expect(page.getByRole("heading", { name: "جِذْر" })).toBeVisible();

  await page.getByRole("button", { name: /متوارث/ }).click();
  await expect(page.getByRole("heading", { name: "مُتَوَارَث" })).toBeVisible();
  await expect(
    page.getByRole("link", { name: "العودة إلى المحرر" }),
  ).toBeVisible();
});

test("rules filtering and search work without technical metadata", async ({
  page,
}, testInfo) => {
  await openEditorReference(page, testInfo.project.name, /القواعد النحوية/);
  await expect(page).toHaveURL(/\/rules$/);
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");

  await page.getByRole("button", { name: "الإملاء" }).click();
  await expect(page.getByText("3 قواعد")).toBeVisible();
  await page.getByRole("searchbox", { name: "ابحث في القواعد" }).fill("التاء");
  await expect(page.getByText("التاء المربوطة في الاسم المؤنث")).toBeVisible();
  await expect(page.getByText("1 قاعدة")).toBeVisible();

  await expect(
    page.getByRole("button", { name: "التفاصيل التقنية" }),
  ).toHaveCount(0);
  await expect(page.getByText("OT_TA_MARBUTA_NOUN")).toHaveCount(0);
});

for (const route of ["/mo3gm", "/rules"] as const) {
  test(`${route} renders in light and dark themes`, async ({
    page,
  }, testInfo) => {
    const pageName = route.slice(1);
    await page.goto(route);
    await page.evaluate(() => localStorage.setItem("baligh-theme", "light"));
    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
    await expect(page.locator("main.reference-page")).toBeVisible();
    await expect(page).toHaveScreenshot(
      `${pageName}-light-${testInfo.project.name}.png`,
      { fullPage: true },
    );

    await page.evaluate(() => localStorage.setItem("baligh-theme", "dark"));
    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await expect(page.locator("main.reference-page")).toBeVisible();
    await expect(page).toHaveScreenshot(
      `${pageName}-dark-${testInfo.project.name}.png`,
      { fullPage: true },
    );
  });
}

test("reference pages honor reduced motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/mo3gm");
  await expect(page.locator(".dictionary-result")).toHaveCSS(
    "transition-duration",
    "0.001s",
  );
});
