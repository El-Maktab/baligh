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
}, testInfo) => {
  await page.goto("/");

  if (testInfo.project.name === "desktop-chromium") {
    await expect(page.locator(".landing-cursor")).toHaveCount(1);
    for (const selector of [
      ".hero-focus",
      ".hero-focus__blob",
      ".feature-card__blob",
      ".team-member img",
    ]) {
      await expect(page.locator(selector).first()).toHaveCSS("cursor", "none");
    }
  } else {
    await expect(page.locator(".landing-cursor")).toHaveCount(0);
  }

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
  await expect(page).toHaveURL(/\/editor$/);
});

test("editor mock workflow resolves corrections and renders in both themes", async ({
  page,
}, testInfo) => {
  await page.goto("/editor");
  await page.evaluate(() => localStorage.setItem("baligh-theme", "light"));
  await page.reload();
  await expect(page.locator('input[value="عن المحبة"]')).toBeVisible();
  if (testInfo.project.name === "mobile-chromium") {
    await expect(
      page.getByRole("button", { name: /^الملاحظات/ }),
    ).toBeVisible();
  } else {
    await expect(
      page.getByRole("heading", { name: "الملاحظات" }),
    ).toBeVisible();
  }
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  if (testInfo.project.name === "mobile-chromium") {
    await page.getByRole("button", { name: /^الملاحظات/ }).click();
    await expect(
      page.getByRole("dialog").getByRole("button", { name: /ضبط الفعل/ }),
    ).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog")).not.toBeVisible();
  } else {
    await expect(page.getByRole("button", { name: /ضبط الفعل/ })).toBeVisible();
  }
  await expect(page).toHaveScreenshot(
    `editor-light-${testInfo.project.name}.png`,
    {
      fullPage: true,
    },
  );

  if (testInfo.project.name === "mobile-chromium") {
    await page.getByRole("button", { name: /^الملاحظات/ }).click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: /^نحو/ })
      .click();
  } else {
    await page.getByRole("button", { name: /^نحو/ }).click();
  }

  await page.getByRole("button", { name: /فعل مضارع منصوب/ }).click();
  await page.getByRole("button", { name: "قبول" }).click();
  if (testInfo.project.name === "mobile-chromium") {
    await expect(
      page.getByRole("dialog").getByRole("button", { name: /فعل مضارع منصوب/ }),
    ).not.toBeVisible();
  } else {
    await expect(
      page.getByRole("button", { name: /فعل مضارع منصوب/ }),
    ).not.toBeVisible();
  }

  await page.evaluate(() => localStorage.setItem("baligh-theme", "dark"));
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page).toHaveScreenshot(
    `editor-dark-${testInfo.project.name}.png`,
    {
      fullPage: true,
    },
  );
});

test("editor body and presentation controls are interactive", async ({
  page,
}, testInfo) => {
  await page.goto("/editor");

  const editor = page.getByRole("textbox", { name: "محتوى النص" });
  const lineLocator = editor.locator(".editor-page__text-line");
  await expect.poll(async () => lineLocator.count()).toBeGreaterThan(1);
  const initialLineCount = await lineLocator.count();
  await editor.click();
  await page.keyboard.press("End");
  await page.keyboard.type(" نص تجريبي");
  await expect(editor).toContainText("نص تجريبي");
  await page.keyboard.press("Enter");
  await page.keyboard.type("سطر إضافي");
  await expect(editor.getByText("سطر إضافي", { exact: true })).toBeVisible();
  await expect(lineLocator).toHaveCount(initialLineCount + 1);

  const strongControl = page.getByRole("button", {
    name: "عرض النص بخط عريض",
  });
  await strongControl.click();
  await expect(strongControl).toHaveAttribute("aria-pressed", "true");
  await expect(
    editor.locator(".editor-page__text-line:has([data-strong])"),
  ).toHaveCount(1);
  expect(await lineLocator.count()).toBeGreaterThan(1);
  if (testInfo.project.name === "mobile-chromium") {
    await page.getByRole("button", { name: "المسودات" }).click();
    await expect(
      page.getByRole("dialog").getByRole("link", { name: /القواعد النحوية/ }),
    ).toHaveAttribute("href", "/rules");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "إضافة نص" })
      .click();
  } else {
    await expect(
      page.getByRole("link", { name: /القواعد النحوية/ }),
    ).toHaveAttribute("href", "/rules");
    await page.getByRole("button", { name: "إضافة نص" }).click();
  }
  await expect(page.locator(".arabic-confetti__letter")).toHaveCount(13);
  await expect(page.getByRole("textbox", { name: "عنوان النص" })).toHaveValue(
    "مسودة جديدة",
  );
});

test("landing secondary actions keep the page stable", async ({ page }) => {
  await page.goto("/");
  const initialScroll = await page.evaluate(() => window.scrollY);
  await page.getByRole("button", { name: "شاهد كيف يعمل" }).click();
  await expect(
    page.getByRole("dialog", { name: "مقطع تعريفي ببليغ" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "إغلاق" }).click();
  await expect(
    page.getByRole("dialog", { name: "مقطع تعريفي ببليغ" }),
  ).not.toBeVisible();
  await page.getByRole("button", { name: "دخول كضيف" }).click();
  const finalScroll = await page.evaluate(() => window.scrollY);
  expect(Math.abs(finalScroll - initialScroll)).toBeLessThan(20);
});

test("team social profiles are linked", async ({ page }) => {
  await page.goto("/");

  const expectedProfiles = [
    ["حساب أمير أنور على جيت هب", "https://github.com/amir-kedis"],
    ["حساب أمير أنور على لينكد إن", "https://www.linkedin.com/in/amir-kedis/"],
    ["حساب أكرم هاني على جيت هب", "https://github.com/akramhany"],
    ["حساب أحمد حامد على جيت هب", "https://github.com/AhmedHamed3699"],
    ["حساب سمية سعد على جيت هب", "https://github.com/somiaelshemy"],
  ] as const;

  for (const [name, href] of expectedProfiles) {
    await expect(page.getByRole("link", { name })).toHaveAttribute(
      "href",
      href,
    );
    await expect(page.getByRole("link", { name })).toHaveAttribute(
      "target",
      "_blank",
    );
  }
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
