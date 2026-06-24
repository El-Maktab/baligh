import {
  BookOpen,
  Clock3,
  Headphones,
  Search,
  Sparkles,
  Volume2,
  VolumeX,
} from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useState } from "react";
import { Button, Form, Input, SearchField } from "react-aria-components";

import { motionPresets } from "../../design-system";
import { ReferenceHeader } from "../../shared/reference/ReferenceHeader";
import {
  dictionaryEntries,
  findDictionaryEntry,
  updateRecentSearches,
  type DictionaryEntry,
} from "./dictionaryData";
import "../reference.css";

function EntryResult({ entry }: { entry: DictionaryEntry }) {
  const reduceMotion = useReducedMotion();
  const speechAvailable =
    typeof window !== "undefined" &&
    "speechSynthesis" in window &&
    "SpeechSynthesisUtterance" in window;

  const speak = () => {
    if (!speechAvailable) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(entry.vocalized);
    utterance.lang = "ar";
    window.speechSynthesis.speak(utterance);
  };

  const sectionMotion = (index: number) => ({
    initial: reduceMotion ? false : { opacity: 0, y: 12 },
    animate: { opacity: 1, y: 0 },
    transition: { ...motionPresets.enter.transition, delay: index * 0.06 },
  });

  return (
    <motion.article
      key={entry.word}
      aria-live="polite"
      className="dictionary-result"
      initial={reduceMotion ? false : motionPresets.softScale.initial}
      animate={motionPresets.softScale.animate}
      exit={reduceMotion ? undefined : { opacity: 0, y: -8 }}
      transition={motionPresets.softScale.transition}
    >
      <header className="dictionary-result__heading">
        <div>
          <div className="dictionary-result__title-line">
            <h2>{entry.vocalized}</h2>
            <span>{entry.partOfSpeech}</span>
          </div>
          <p>الجذر: {entry.root}</p>
        </div>
        <Button
          aria-label={
            speechAvailable
              ? `الاستماع إلى نطق ${entry.word}`
              : "النطق الصوتي غير متاح في هذا المتصفح"
          }
          className="dictionary-result__speaker"
          isDisabled={!speechAvailable}
          onPress={speak}
        >
          {speechAvailable ? (
            <Volume2 aria-hidden="true" />
          ) : (
            <VolumeX aria-hidden="true" />
          )}
        </Button>
      </header>

      <motion.section
        className="dictionary-result__meanings"
        {...sectionMotion(0)}
      >
        <h3>
          <BookOpen aria-hidden="true" size={19} /> المعاني
        </h3>
        <ol>
          {entry.meanings.map((meaning) => (
            <li key={meaning}>{meaning}</li>
          ))}
        </ol>
      </motion.section>

      <div className="dictionary-result__relations">
        <motion.section {...sectionMotion(1)}>
          <h3>المرادفات</h3>
          <div className="dictionary-result__chips">
            {entry.synonyms.map((word) => (
              <span key={word}>{word}</span>
            ))}
          </div>
        </motion.section>
        <motion.section data-tone="antonym" {...sectionMotion(2)}>
          <h3>الأضداد</h3>
          <div className="dictionary-result__chips">
            {entry.antonyms.map((word) => (
              <span key={word}>{word}</span>
            ))}
          </div>
        </motion.section>
      </div>

      <motion.section
        className="dictionary-result__examples"
        {...sectionMotion(3)}
      >
        <h3>
          <Sparkles aria-hidden="true" size={19} /> أمثلة الاستخدام
        </h3>
        {entry.examples.map((example) => (
          <blockquote key={example.text}>
            <span>{example.source}</span>
            <p>«{example.text}»</p>
          </blockquote>
        ))}
      </motion.section>
    </motion.article>
  );
}

export function Mo3gmPage() {
  const [query, setQuery] = useState("بليغ");
  const [entry, setEntry] = useState<DictionaryEntry | undefined>(
    dictionaryEntries[0],
  );
  const [submittedQuery, setSubmittedQuery] = useState("بليغ");
  const [recent, setRecent] = useState(["بليغ", "استنبط", "جذر", "متوارث"]);
  const reduceMotion = useReducedMotion();

  const submitSearch = (value = query) => {
    const result = findDictionaryEntry(value);
    setSubmittedQuery(value.trim());
    setEntry(result);
    if (result) setRecent((items) => updateRecentSearches(items, result.word));
  };

  return (
    <main className="reference-page dictionary-page">
      <ReferenceHeader />
      <section className="reference-hero dictionary-hero">
        <motion.div
          initial={reduceMotion ? false : motionPresets.enter.initial}
          animate={motionPresets.enter.animate}
          transition={motionPresets.enter.transition}
        >
          <p className="reference-eyebrow">
            <Headphones aria-hidden="true" size={18} /> كلماتٌ أقرب، كتابةٌ أدق
          </p>
          <h1>المعجم العربي</h1>
          <p className="reference-hero__intro">
            ابحث عن معنى الكلمة وجذرها، وتعرّف إلى مرادفاتها وأضدادها في تجربة
            سريعة وواضحة.
          </p>
        </motion.div>

        <Form
          className="reference-search"
          onSubmit={(event) => {
            event.preventDefault();
            submitSearch();
          }}
        >
          <SearchField
            aria-label="ابحث في المعجم"
            className="reference-search__field"
            value={query}
            onChange={setQuery}
          >
            <Search aria-hidden="true" size={20} />
            <Input placeholder="اكتب كلمة عربية، مثل: بليغ" />
          </SearchField>
          <Button className="reference-search__button" type="submit">
            بحث
          </Button>
        </Form>
      </section>

      <section className="dictionary-layout">
        <aside className="dictionary-recent">
          <div className="dictionary-recent__heading">
            <Clock3 aria-hidden="true" size={19} />
            <div>
              <h2>عمليات البحث الأخيرة</h2>
              <p>ارجع إلى كلمة سابقة بضغطة واحدة.</p>
            </div>
          </div>
          <div className="dictionary-recent__list">
            {recent.map((word) => (
              <Button
                className="dictionary-recent__item"
                key={word}
                onPress={() => {
                  setQuery(word);
                  submitSearch(word);
                }}
              >
                <strong>{word}</strong>
                <span>اعرض المعنى</span>
              </Button>
            ))}
          </div>
        </aside>

        <div className="dictionary-result-slot">
          <AnimatePresence mode="wait">
            {entry ? (
              <EntryResult entry={entry} key={entry.word} />
            ) : (
              <motion.div
                aria-live="polite"
                className="reference-empty"
                key="empty"
                initial={reduceMotion ? false : { opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Search aria-hidden="true" size={28} />
                <h2>لم نجد «{submittedQuery || "هذه الكلمة"}»</h2>
                <p>
                  هذه نسخة تجريبية مصغّرة. جرّب إحدى الكلمات: بليغ، استنبط، جذر،
                  أو متوارث.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>
    </main>
  );
}
