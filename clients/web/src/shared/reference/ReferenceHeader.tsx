import { ArrowRight, PencilLine } from "lucide-react";
import { Link } from "react-router-dom";

import { BalighWordmark } from "../../design-system";
import { ThemeControl } from "../ui/ThemeControl";

export function ReferenceHeader() {
  return (
    <header className="reference-header">
      <Link
        aria-label="العودة إلى الصفحة الرئيسية"
        className="reference-header__brand"
        to="/"
      >
        <BalighWordmark className="reference-header__wordmark" />
      </Link>
      <div className="reference-header__actions">
        <Link
          aria-label="العودة إلى المحرر"
          className="reference-header__editor-link"
          to="/editor"
        >
          <ArrowRight aria-hidden="true" size={18} />
          <span className="reference-header__editor-label">
            العودة إلى المحرر
          </span>
          <PencilLine
            aria-hidden="true"
            className="reference-header__editor-icon"
            size={18}
          />
        </Link>
        <ThemeControl />
      </div>
    </header>
  );
}
