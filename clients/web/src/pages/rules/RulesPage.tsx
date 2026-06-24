import {
  BookMarked,
  Check,
  CircleX,
  Search,
  SlidersHorizontal,
} from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { useState } from "react";
import { Button, Input, SearchField } from "react-aria-components";

import { motionPresets } from "../../design-system";
import { ReferenceHeader } from "../../shared/reference/ReferenceHeader";
import {
  filterGrammarRules,
  grammarRules,
  ruleCategories,
  type GrammarRule,
  type RuleCategory,
} from "./rulesData";
import "../reference.css";

const categoryLabels: Record<RuleCategory, string> = {
  syntax: "نحو",
  orthography: "إملاء",
  semantics: "استعمال لغوي",
};

function RuleCard({ rule, index }: { rule: GrammarRule; index: number }) {
  const reduceMotion = useReducedMotion();
  const blobSource =
    rule.category === "orthography"
      ? "/blobs/features-blob-1.svg"
      : "/blobs/features-blob-2.svg";

  return (
    <motion.article
      className="rule-card"
      data-category={rule.category}
      initial={reduceMotion ? false : { opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...motionPresets.enter.transition, delay: index * 0.04 }}
    >
      <img
        alt=""
        aria-hidden="true"
        className="rule-card__blob"
        data-position={index % 4}
        src={blobSource}
      />
      <div className="rule-card__topline">
        <span>{categoryLabels[rule.category]}</span>
        <BookMarked aria-hidden="true" size={19} />
      </div>
      <h2>{rule.title}</h2>
      <p className="rule-card__explanation">{rule.explanation}</p>

      <div className="rule-card__examples">
        <div data-tone="incorrect">
          <span>
            <CircleX aria-hidden="true" size={17} /> تجنّب
          </span>
          <p>{rule.incorrect}</p>
        </div>
        <div data-tone="correct">
          <span>
            <Check aria-hidden="true" size={17} /> الصواب
          </span>
          <p>{rule.correct}</p>
        </div>
      </div>
      <p className="rule-card__note">{rule.note}</p>
    </motion.article>
  );
}

export function RulesPage() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<"all" | RuleCategory>("all");
  const reduceMotion = useReducedMotion();
  const visibleRules = filterGrammarRules(grammarRules, query, category);

  return (
    <main className="reference-page rules-page">
      <ReferenceHeader />
      <section className="reference-hero rules-hero">
        <motion.div
          initial={reduceMotion ? false : motionPresets.enter.initial}
          animate={motionPresets.enter.animate}
          transition={motionPresets.enter.transition}
        >
          <p className="reference-eyebrow">
            <SlidersHorizontal aria-hidden="true" size={18} /> افهم القاعدة، ثم
            طبّقها
          </p>
          <h1>دليل القواعد</h1>
          <p className="reference-hero__intro">
            شروح عربية قريبة، وأمثلة عملية، وتفاصيل تكشف كيف يتعرّف بليغ إلى
            الأخطاء.
          </p>
        </motion.div>
      </section>

      <section className="rules-browser" aria-labelledby="rules-browser-title">
        <div className="rules-browser__toolbar">
          <div>
            <p className="reference-eyebrow">تصفّح المكتبة</p>
            <h2 id="rules-browser-title">قاعدة وراء كل ملاحظة</h2>
          </div>
          <SearchField
            aria-label="ابحث في القواعد"
            className="rules-search"
            value={query}
            onChange={setQuery}
          >
            <Search aria-hidden="true" size={19} />
            <Input placeholder="ابحث بالشرح أو المثال أو المعرّف" />
          </SearchField>
        </div>

        <div className="rules-browser__filter-row">
          <div className="rules-browser__filters" aria-label="فئات القواعد">
            {ruleCategories.map((item) => (
              <Button
                aria-pressed={category === item.value}
                className="rules-browser__filter"
                data-active={category === item.value || undefined}
                key={item.value}
                onPress={() => setCategory(item.value)}
              >
                {item.label}
              </Button>
            ))}
          </div>
          <p aria-live="polite" className="rules-browser__count">
            {visibleRules.length}{" "}
            {visibleRules.length === 1 ? "قاعدة" : "قواعد"}
          </p>
        </div>

        {visibleRules.length ? (
          <div className="rules-grid">
            {visibleRules.map((rule, index) => (
              <RuleCard index={index} key={rule.id} rule={rule} />
            ))}
          </div>
        ) : (
          <div className="reference-empty">
            <Search aria-hidden="true" size={28} />
            <h2>لا توجد قاعدة مطابقة</h2>
            <p>جرّب عبارة أقصر أو اختر فئة أخرى.</p>
          </div>
        )}
      </section>
    </main>
  );
}
