import {
  ArrowDown,
  BookOpenText,
  CaseUpper,
  CirclePlay,
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

import { BalighWordmark, motionPresets } from "../../design-system";
import { ArabicConfettiButton } from "../../shared/ui/ArabicConfettiButton";
import { ThemeControl } from "../../shared/ui/ThemeControl";
import "./home.css";

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
  ["أمير أنور", "/blobs/person-blob-4.svg", -2],
  ["أكرم هاني", "/blobs/person-blob-3.svg", 2],
  ["أحمد حامد", "/blobs/person-blob-2.svg", -3],
  ["سمية سعد", "/blobs/person-blob-1.svg", 3],
] as const;

function HeroFocus() {
  const reduceMotion = useReducedMotion();
  const pointerX = useMotionValue(0);
  const pointerY = useMotionValue(0);
  const springX = useSpring(pointerX, { stiffness: 90, damping: 18 });
  const springY = useSpring(pointerY, { stiffness: 90, damping: 18 });
  const blobX = useTransform(springX, (value) => value * 0.35);
  const blobY = useTransform(springY, (value) => value * 0.35);

  const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (reduceMotion) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    pointerX.set((event.clientX - bounds.left - bounds.width / 2) / 7);
    pointerY.set((event.clientY - bounds.top - bounds.height / 2) / 7);
  };

  return (
    <div
      className="hero-focus"
      onPointerLeave={() => {
        pointerX.set(0);
        pointerY.set(0);
      }}
      onPointerMove={handlePointerMove}
    >
      <motion.img
        alt=""
        className="hero-focus__blob"
        src="/blobs/hero_blob.svg"
        style={{ x: blobX, y: blobY }}
        animate={
          reduceMotion
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
          className={`hero-letter ${className}`}
          style={{ x: springX, y: springY }}
          animate={
            reduceMotion ? undefined : { y: [0, -9, 0], rotate: [-1, 2, -1] }
          }
          whileHover={{ scale: 1.08, rotate: 5 }}
          whileTap={{ scale: 0.94 }}
          transition={{ duration: 4.5, delay: Number(delay), repeat: Infinity }}
        >
          {letter}
        </motion.span>
      ))}
    </div>
  );
}

export function HomePage() {
  const reduceMotion = useReducedMotion();

  const scrollToFeatures = () => {
    document.getElementById("features")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <main className="landing-page">
      <section className="landing-section landing-hero" id="home">
        <header className="landing-header">
          <BalighWordmark className="landing-logo" />
          <nav className="landing-nav" aria-label="التنقل الرئيسي">
            <a href="#features">تسجيل الدخول</a>
            <a className="guest-link" href="#features">
              دخول كضيف
            </a>
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
              <span>للكتابة العربية</span>
              بأسلوب <strong>بليغ</strong>
            </h1>
            <p>
              ارتقِ بمستوى كتاباتك العربية مع أدوات تحليل نحوي وإملائي دقيقة،
              مدعومة بالذكاء الاصطناعي لتحسين الأسلوب والمفردات لحظياً.
            </p>
            <div className="hero-actions">
              <ArabicConfettiButton onPress={scrollToFeatures}>
                <PencilLine aria-hidden="true" />
                ابدأ الكتابة الآن
              </ArabicConfettiButton>
              <a className="secondary-cta" href="#features">
                <CirclePlay aria-hidden="true" />
                شاهد كيف يعمل
              </a>
            </div>
          </motion.div>

          <HeroFocus />
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
          {team.map(([name, image, rotate], index) => (
            <motion.article
              className="team-member"
              key={name}
              initial={reduceMotion ? false : { opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.5 }}
              transition={{ delay: index * 0.09 }}
            >
              <motion.img
                alt=""
                src={image}
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
              />
              <h3>{name}</h3>
            </motion.article>
          ))}
        </div>

        <p className="supervisor">تحت إشراف دكتور أيمن أبوالحسن</p>
      </section>
    </main>
  );
}
