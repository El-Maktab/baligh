import { BrowserRouter, Route, Routes } from "react-router-dom";

import { DesignSystemPage } from "../pages/design-system/DesignSystemPage";
import { EditorPage } from "../pages/editor/EditorPage";
import { HomePage } from "../pages/home/HomePage";
import { Mo3gmPage } from "../pages/mo3gm/Mo3gmPage";
import { NotFoundPage } from "../pages/not-found/NotFoundPage";
import { RulesPage } from "../pages/rules/RulesPage";
import { isShowcaseEnabled } from "./environment";

const showcaseEnabled = isShowcaseEnabled(
  import.meta.env.DEV,
  import.meta.env.VITE_SHOWCASE_ENABLED,
);

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/editor" element={<EditorPage />} />
        <Route path="/mo3gm" element={<Mo3gmPage />} />
        <Route path="/rules" element={<RulesPage />} />
        {showcaseEnabled && (
          <Route path="/design-system" element={<DesignSystemPage />} />
        )}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
