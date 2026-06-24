import { BrowserRouter, Route, Routes } from "react-router-dom";

import { DesignSystemPage } from "../pages/design-system/DesignSystemPage";
import { EditorPage } from "../pages/editor/EditorPage";
import { HomePage } from "../pages/home/HomePage";
import { NotFoundPage } from "../pages/not-found/NotFoundPage";
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
        {showcaseEnabled && (
          <Route path="/design-system" element={<DesignSystemPage />} />
        )}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
