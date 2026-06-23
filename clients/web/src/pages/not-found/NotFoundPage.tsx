import { Link } from "react-router-dom";

import { BalighWordmark } from "../../design-system";

export function NotFoundPage() {
  return (
    <main className="not-found-page">
      <BalighWordmark className="not-found-page__logo" />
      <p className="eyebrow">٤٠٤</p>
      <h1>هذه الصفحة لم تُكتب بعد.</h1>
      <Link className="showcase-link" to="/">
        العودة إلى البداية
      </Link>
    </main>
  );
}
