import { ArrowRight, Check, Info, Sparkles, TriangleAlert } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { Link } from "react-router-dom";

import {
  AssistantMark,
  BalighWordmark,
  motionPresets,
} from "../../design-system";
import { ThemeControl } from "../../shared/ui/ThemeControl";

const colorTokens = [
  ["الخلفية", "canvas"],
  ["السطح", "surface"],
  ["السطح الهادئ", "surface-muted"],
  ["النص", "text"],
  ["النص الهادئ", "text-muted"],
  ["الأساسي", "primary"],
  ["الأساسي القوي", "primary-strong"],
  ["المائي", "accent-aqua"],
  ["الرملي", "accent-sand"],
  ["الوردي", "accent-pink"],
  ["الحدود", "border"],
  ["التنبيه", "warning"],
  ["الخطأ", "danger"],
] as const;

const typeSamples = [
  ["عرض", "من الكلمة تبدأ الفكرة", "display"],
  ["عنوان ١", "العربية تستحق أدوات تفهمها", "heading-one"],
  ["عنوان ٢", "تفاصيل أوضح، وكتابة أدق", "heading-two"],
  ["نص", "يشرح بليغ الاقتراح قبل أن يطلب منك اعتماده.", "body"],
  ["صغير", "معلومة مساندة لا تنافس النص الأساسي.", "small"],
] as const;

export function DesignSystemPage() {
  const reduceMotion = useReducedMotion();

  return (
    <main className="showcase-page">
      <header className="showcase-header">
        <div>
          <p className="eyebrow">بليغ / الأسس</p>
          <h1>نَهْجُ التَّصْمِيم.</h1>
          <p>
            مرجع حي للألوان، والكتابة، والعلامة، والحركة قبل بناء واجهات المنتج.
          </p>
        </div>
        <div className="showcase-header__actions">
          <ThemeControl />
          <Link to="/" aria-label="العودة إلى الرئيسية">
            <ArrowRight aria-hidden="true" />
          </Link>
        </div>
      </header>

      <section className="showcase-section">
        <div className="section-heading">
          <span>٠١</span>
          <div>
            <h2>الألوان الدلالية</h2>
            <p>تتغير القيم بين المظهرين، بينما يبقى المعنى ثابتاً.</p>
          </div>
        </div>
        <div className="swatch-grid">
          {colorTokens.map(([label, token]) => (
            <article className="swatch" key={token}>
              <div className={`swatch__color swatch__color--${token}`} />
              <div>
                <strong>{label}</strong>
                <code>--ds-color-{token}</code>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="showcase-section">
        <div className="section-heading">
          <span>٠٢</span>
          <div>
            <h2>الكتابة</h2>
            <p>Alexandria بهرم واضح ومساحة كافية لتشكيل الحروف العربية.</p>
          </div>
        </div>
        <div className="type-specimen">
          {typeSamples.map(([label, sample, style]) => (
            <div className="type-row" key={style}>
              <span>{label}</span>
              <p className={`type-${style}`}>{sample}</p>
            </div>
          ))}
          <div className="mixed-copy" dir="auto">
            يدعم المحرر نصاً مختلطاً مثل Baligh 1.0 داخل السياق العربي.
          </div>
        </div>
      </section>

      <section className="showcase-section showcase-section--split">
        <div>
          <div className="section-heading">
            <span>٠٣</span>
            <div>
              <h2>العلامة</h2>
              <p>علامات مرنة ترث لون السياق وتعمل في المظهرين.</p>
            </div>
          </div>
          <div className="brand-stage">
            <BalighWordmark />
            <AssistantMark />
          </div>
        </div>

        <div>
          <div className="section-heading">
            <span>٠٤</span>
            <div>
              <h2>الحالة</h2>
              <p>اللون يدعم المعنى ولا يحمله منفرداً.</p>
            </div>
          </div>
          <div className="status-stack">
            <div className="status-card status-card--success">
              <Check aria-hidden="true" />
              <span>تم حفظ التعديل</span>
            </div>
            <div className="status-card status-card--info">
              <Info aria-hidden="true" />
              <span>يوجد تفسير إضافي</span>
            </div>
            <div className="status-card status-card--warning">
              <TriangleAlert aria-hidden="true" />
              <span>راجع الاقتراح قبل اعتماده</span>
            </div>
          </div>
        </div>
      </section>

      <section className="showcase-section motion-section">
        <div className="section-heading">
          <span>٠٥</span>
          <div>
            <h2>الحركة</h2>
            <p>تعبيرية في العلامة، وأهدأ داخل تجربة الكتابة.</p>
          </div>
        </div>
        <motion.div
          className="motion-demo"
          initial={reduceMotion ? false : motionPresets.softScale.initial}
          whileInView={motionPresets.softScale.animate}
          transition={motionPresets.softScale.transition}
          viewport={{ once: false, amount: 0.5 }}
        >
          <Sparkles aria-hidden="true" />
          <span>المعنى أولاً، ثم اللمسة.</span>
        </motion.div>
      </section>
    </main>
  );
}
