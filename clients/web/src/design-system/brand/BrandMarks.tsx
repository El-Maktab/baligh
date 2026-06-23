type BrandMarkProps = {
  className?: string;
  title?: string;
};

export function BalighWordmark({ className, title = "بليغ" }: BrandMarkProps) {
  return (
    <span
      aria-label={title}
      className={["brand-asset", "brand-asset--logo", className]
        .filter(Boolean)
        .join(" ")}
      role="img"
    >
      <img
        aria-hidden="true"
        alt=""
        className="brand-asset__light"
        src="/logos/Logo_light.svg"
      />
      <img
        aria-hidden="true"
        alt=""
        className="brand-asset__dark"
        src="/logos/Logo_dark.svg"
      />
    </span>
  );
}

export function AssistantMark({
  className,
  title = "مساعد بليغ",
}: BrandMarkProps) {
  return (
    <span
      aria-label={title}
      className={["brand-asset", "brand-asset--assistant", className]
        .filter(Boolean)
        .join(" ")}
      role="img"
    >
      <img
        aria-hidden="true"
        alt=""
        className="brand-asset__light"
        src="/logos/Assistant_light.svg"
      />
      <img
        aria-hidden="true"
        alt=""
        className="brand-asset__dark"
        src="/logos/Assistant_dark.svg"
      />
    </span>
  );
}
