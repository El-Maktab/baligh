import {
  ArrowDown,
  BookOpenText,
  CaseUpper,
  CirclePlay,
  Github,
  Linkedin,
  PencilLine,
  SearchCheck,
  Sparkles,
  SpellCheck2,
  WandSparkles,
} from "lucide-react";
import {
  motion,
  useMotionValue,
  useReducedMotion,
  useSpring,
  useTransform,
} from "motion/react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { BalighWordmark, motionPresets } from "../../design-system";
import { ArabicConfettiButton } from "../../shared/ui/ArabicConfettiButton";
import { ThemeControl } from "../../shared/ui/ThemeControl";
import { VideoPlayerModal } from "../../shared/ui/VideoPlayerModal";
import "./home.css";
import { LandingCursor } from "./LandingCursor";

const features = [
  {
    id: "language",
    title: "مدقق لغوي",
    description:
      "اكتشف الأخطاء الإملائية والنحوية والصرفية في النصوص، وحسّن أسلوبك بالتعلّم من أخطائك.",
    icon: CaseUpper,
    tone: "aqua",
    demo: true,
  },
  {
    id: "diacritics",
    title: "إضافة التشكيل",
    description: "استمتع بتشكيل دقيق لكتابتك، لإضفاء طابع احترافي لنصوصك.",
    icon: SpellCheck2,
    tone: "sand",
    demo: false,
  },
  {
    id: "analysis",
    title: "تحليل أسباب الأخطاء",
    description:
      "بليغ مبني على نظام الأنطولوجيا الذكي وقواعد اللغة ليمنحك تفسيراً مبرراً للأخطاء والتعديلات المقترحة.",
    icon: SearchCheck,
    tone: "green",
    demo: false,
  },
  {
    id: "completion",
    title: "اقتراحات لتكملة الكلام",
    description:
      "يستخدم بليغ الذكاء الاصطناعي وأشهر العبارات ليساعدك على إكمال كتابتك كرفيق كتابة ذكي.",
    icon: Sparkles,
    tone: "sand",
    demo: false,
  },
  {
    id: "style",
    title: "تحسين الأسلوب",
    description:
      "يساعدك بليغ على اختيار الكلمات الأنسب للسياق وتشكيل جملة أفضل واستخدام علامات الترقيم بدقة.",
    icon: WandSparkles,
    tone: "aqua",
    demo: false,
  },
  {
    id: "dictionary",
    title: "الكشف في المعجم",
    description:
      "ابحث عن أصول الكلمات والمعاني والمرادفات والاستخدامات في معجم عربي متكامل.",
    icon: BookOpenText,
    tone: "sand",
    demo: false,
  },
] as const;

const team = [
  {
    name: "أمير أنور",
    image: "/blobs/person-blob-4.svg",
    portrait: "/pics/amir-2-nobg.png",
    portraitViewBox: "0 0 329 287",
    portraitClipPath:
      "M159.3 275.794C113.985 269.166 33.5202 223.823 16.3691 183.907C-0.782019 143.99 23.4191 64.266 56.3933 36.2968C89.3675 8.32765 171.56 6.17069 214.214 16.0915C256.869 26.0123 299.978 61.2245 312.318 95.8218C324.659 130.419 313.762 193.68 288.259 223.675",
    portraitFrame: { x: -335, y: -318, width: 1000, height: 1333 },
    rotate: -2,
    github: "https://github.com/amir-kedis",
    linkedin: "https://www.linkedin.com/in/amir-kedis/",
  },
  {
    name: "أكرم هاني",
    image: "/blobs/person-blob-3.svg",
    portrait: "/pics/akram-nobg-2.png",
    portraitViewBox: "0 0 320 341",
    portraitClipPath:
      "M266.456 316.303C228.057 339.369 121.252 330.673 78.6515 305.27C36.0513 279.867 8.36607 210.708 10.8553 163.886C13.3445 117.063 57.1398 46.2974 93.5868 24.3366C130.034 2.37572 193.627 8.36462 229.537 32.1205C265.447 55.8764 302.894 119.508 309.047 166.872",
    portraitFrame: { x: -70, y: -80, width: 460, height: 493 },
    rotate: 2,
    github: "https://github.com/akramhany",
    linkedin: "https://www.linkedin.com/in/akramhany/",
  },
  {
    name: "أحمد حامد",
    image: "/blobs/person-blob-2.svg",
    portrait: "/pics/hamed-nobg.png",
    portraitViewBox: "0 0 282 318",
    portraitClipPath:
      "M270.339 233.621C255.823 272.525 203.106 299.971 161.283 305.373C119.46 310.775 39.4705 304.258 19.4013 266.032C-0.667829 227.807 17.1328 118.572 40.8684 76.0192C64.6041 33.4661 127.23 11.3927 161.815 10.7136C196.401 10.0345 230.293 34.7934 248.38 71.9446",
    portraitFrame: { x: -140, y: -190, width: 560, height: 746 },
    rotate: -3,
    github: "https://github.com/AhmedHamed3699",
    linkedin: "https://www.linkedin.com/in/ahmedhamed3699/",
  },
  {
    name: "سمية سعد",
    image: "/blobs/person-blob-1.svg",
    portrait: "/pics/somia-nobg.png",
    portraitViewBox: "0 0 322 304",
    portraitClipPath:
      "M228.059 268.879C193.921 291.432 142.079 301.814 105.852 282.762C69.6262 263.711 10.3489 194.833 10.7018 154.57C11.0546 114.308 72.7785 63.982 107.969 41.1865C143.16 18.3911 188.061 0.088439 221.847 17.7977C255.633 35.5069 309.649 105.595 310.684 147.442",
    portraitFrame: { x: 15, y: -50, width: 280, height: 373 },
    rotate: 3,
    github: "https://github.com/somiaelshemy",
    linkedin: "https://www.linkedin.com/in/somia-elshemy-a252a834b/",
  },
] as const;

const FINE_POINTER_QUERY = "(hover: hover) and (pointer: fine)";

function useFinePointer() {
  const [hasFinePointer, setHasFinePointer] = useState(
    () => window.matchMedia(FINE_POINTER_QUERY).matches,
  );

  useEffect(() => {
    const mediaQuery = window.matchMedia(FINE_POINTER_QUERY);
    const update = () => setHasFinePointer(mediaQuery.matches);

    update();
    mediaQuery.addEventListener("change", update);
    return () => mediaQuery.removeEventListener("change", update);
  }, []);

  return hasFinePointer;
}

type HeroFocusProps = {
  interactive: boolean;
};

function HeroFocus({ interactive }: HeroFocusProps) {
  const reduceMotion = useReducedMotion();
  const pointerX = useMotionValue(0);
  const pointerY = useMotionValue(0);
  const springX = useSpring(pointerX, { stiffness: 90, damping: 18 });
  const springY = useSpring(pointerY, { stiffness: 90, damping: 18 });
  const blobX = useTransform(springX, (value) => value * 0.35);
  const blobY = useTransform(springY, (value) => value * 0.35);
  const boundsRef = useRef<DOMRect | null>(null);
  const allowMotion = interactive && !reduceMotion;

  const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!allowMotion) return;
    const bounds =
      boundsRef.current ?? event.currentTarget.getBoundingClientRect();
    pointerX.set((event.clientX - bounds.left - bounds.width / 2) / 12);
    pointerY.set((event.clientY - bounds.top - bounds.height / 2) / 12);
  };

  return (
    <div
      className="hero-focus"
      data-interactive={allowMotion || undefined}
      onPointerEnter={(event) => {
        if (allowMotion) {
          boundsRef.current = event.currentTarget.getBoundingClientRect();
        }
      }}
      onPointerLeave={() => {
        boundsRef.current = null;
        pointerX.set(0);
        pointerY.set(0);
      }}
      onPointerMove={handlePointerMove}
    >
      <motion.img
        alt=""
        className="hero-focus__blob"
        src="/blobs/hero_blob.webp"
        style={{ x: blobX, y: blobY }}
        animate={
          !allowMotion
            ? undefined
            : { rotate: [-1, 2, -1], scale: [1, 1.025, 1] }
        }
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
      />
      {[
        ["ب", "hero-letter--ba", -0.7],
        ["ع", "hero-letter--ain", -2.2],
        ["ض", "hero-letter--dad", -3.8],
      ].map(([letter, className, delay]) => (
        <motion.span
          key={letter}
          className={`hero-letter-shell ${className}`}
          style={{ x: springX, y: springY }}
        >
          <motion.span
            className="hero-letter"
            animate={
              !allowMotion ? undefined : { y: [0, -6, 0], rotate: [-1, 1, -1] }
            }
            transition={{
              duration: 5.5,
              delay: Number(delay),
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            {letter}
          </motion.span>
        </motion.span>
      ))}
    </div>
  );
}

export function HomePage() {
  const reduceMotion = useReducedMotion();
  const hasFinePointer = useFinePointer();
  const navigate = useNavigate();
  const [videoOpen, setVideoOpen] = useState(false);

  return (
    <main className="landing-page">
      {hasFinePointer && !reduceMotion && <LandingCursor />}
      <section className="landing-section landing-hero" id="home">
        <header className="landing-header">
          <BalighWordmark className="landing-logo" />
          <nav className="landing-nav" aria-label="التنقل الرئيسي">
            <button type="button">تسجيل الدخول</button>
            <button className="guest-link" type="button">
              دخول كضيف
            </button>
            <ThemeControl />
          </nav>
        </header>

        <div className="landing-hero__content">
          <motion.div
            className="landing-hero__copy"
            initial={reduceMotion ? false : motionPresets.enter.initial}
            animate={motionPresets.enter.animate}
            transition={motionPresets.enter.transition}
          >
            <h1>
              مساعدك الذكي
              <span className="hero-line">للكتابة العربية</span>
            </h1>
            <div className="hero-logo-line" aria-label="بأسلوب بليغ">
              <span>بأسلوب</span>
              <BalighWordmark className="hero-inline-logo" />
            </div>
            <p>
              ارتقِ بمستوى كتاباتك العربية مع أدوات تحليل نحوي وإملائي دقيقة،
              مدعومة بالذكاء الاصطناعي لتحسين الأسلوب والمفردات لحظياً.
            </p>
            <div className="hero-actions">
              <ArabicConfettiButton
                onPress={() => {
                  void navigate("/editor");
                }}
              >
                <PencilLine aria-hidden="true" />
                ابدأ الكتابة الآن
              </ArabicConfettiButton>
              <button
                className="secondary-cta"
                type="button"
                onClick={() => setVideoOpen(true)}
              >
                <CirclePlay aria-hidden="true" />
                شاهد كيف يعمل
              </button>
            </div>
          </motion.div>

          <HeroFocus interactive={hasFinePointer} />
        </div>

        <a
          className="scroll-cue"
          href="#features"
          aria-label="انتقل إلى المزايا"
        >
          <ArrowDown aria-hidden="true" />
        </a>
      </section>

      <section className="landing-section features-section" id="features">
        <motion.div
          className="section-intro"
          initial={reduceMotion ? false : { opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.6 }}
        >
          <p className="section-kicker">أدوات بليغ</p>
          <h2>كل ما تحتاجه لكتابة متقنة</h2>
          <p>أدوات مصممة خصيصاً لفهم تعقيدات وجماليات اللغة العربية.</p>
        </motion.div>

        <div className="features-grid">
          {features.map(
            ({ id, title, description, icon: Icon, tone, demo }, index) => (
              <motion.article
                key={id}
                className={`feature-card feature-card--${id} feature-card--${tone}`}
                initial={reduceMotion ? false : { opacity: 0, y: 28 }}
                whileInView={{ opacity: 1, y: 0 }}
                whileHover={
                  reduceMotion
                    ? undefined
                    : { y: -5, rotate: index % 2 ? 0.25 : -0.25 }
                }
                transition={{ delay: index * 0.06, duration: 0.45 }}
                viewport={{ once: true, amount: 0.35 }}
              >
                <div className="feature-card__title">
                  <span>
                    <Icon aria-hidden="true" />
                  </span>
                  <h3>{title}</h3>
                </div>
                <p>{description}</p>
                {demo && (
                  <div
                    className="correction-demo"
                    aria-label="مثال على تصحيح لغوي"
                  >
                    <span>يجب على الكاتب أن</span>
                    <del>يعتن</del>
                    <ins>يعتني</ins>
                    <span>بالتفاصيل الدقيقة.</span>
                  </div>
                )}
                {id === "analysis" && (
                  <img
                    className="feature-card__blob"
                    src="/blobs/features-blob-2.svg"
                    alt=""
                  />
                )}
                {tone === "sand" && (
                  <img
                    className="feature-card__blob"
                    src="/blobs/features-blob-1.svg"
                    alt=""
                  />
                )}
              </motion.article>
            ),
          )}
        </div>
      </section>

      <section className="landing-section team-section" id="team">
        <div className="section-intro">
          <p className="section-kicker">فريق بليغ</p>
          <h2>تعرّفوا على فريق بليغ</h2>
          <p>
            طلاب هندسة القاهرة، قسم حاسبات، شغوفون بالعربية ومعالجة اللغات
            الطبيعية.
          </p>
        </div>

        <div className="team-grid">
          {team.map(
            (
              {
                name,
                image,
                portrait,
                portraitViewBox,
                portraitClipPath,
                portraitFrame,
                rotate,
                github,
                linkedin,
              },
              index,
            ) => (
              <motion.article
                className="team-member"
                key={name}
                initial={reduceMotion ? false : { opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.5 }}
                transition={{ delay: index * 0.09 }}
              >
                <motion.div
                  className="team-member__portrait"
                  animate={
                    reduceMotion
                      ? undefined
                      : { y: [0, -7, 0], rotate: [0, rotate, 0] }
                  }
                  whileHover={
                    reduceMotion
                      ? undefined
                      : { scale: 1.06, rotate: rotate * -1 }
                  }
                  transition={{
                    duration: 5 + index * 0.4,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                >
                  <img
                    alt=""
                    aria-hidden="true"
                    className="team-member__blob"
                    src={image}
                  />
                  {portrait && (
                    <svg
                      aria-label={`صورة ${name}`}
                      className="team-member__photo"
                      role="img"
                      viewBox={portraitViewBox}
                    >
                      <defs>
                        <clipPath id={`team-blob-clip-${index}`}>
                          <path d={portraitClipPath} />
                        </clipPath>
                      </defs>
                      <image
                        clipPath={`url(#team-blob-clip-${index})`}
                        height={portraitFrame.height}
                        href={portrait}
                        preserveAspectRatio="xMidYMid meet"
                        width={portraitFrame.width}
                        x={portraitFrame.x}
                        y={portraitFrame.y}
                      />
                    </svg>
                  )}
                </motion.div>
                <h3>{name}</h3>
                <div className="team-member__socials">
                  <a
                    aria-label={`حساب ${name} على لينكد إن`}
                    href={linkedin}
                    rel="noreferrer"
                    target="_blank"
                  >
                    <Linkedin aria-hidden="true" size={18} strokeWidth={1.8} />
                  </a>
                  <a
                    aria-label={`حساب ${name} على جيت هب`}
                    href={github}
                    rel="noreferrer"
                    target="_blank"
                  >
                    <Github aria-hidden="true" size={18} strokeWidth={1.8} />
                  </a>
                </div>
              </motion.article>
            ),
          )}
        </div>

        <p className="supervisor">تحت إشراف دكتور أيمن أبوالحسن</p>
      </section>

      <VideoPlayerModal open={videoOpen} onClose={() => setVideoOpen(false)} />
    </main>
  );
}
