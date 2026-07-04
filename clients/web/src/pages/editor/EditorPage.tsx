import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  Bold,
  BookOpenText,
  Check,
  CircleAlert,
  FilePlus2,
  FolderOpen,
  Home,
  Languages,
  List,
  ListOrdered,
  LoaderCircle,
  Sparkles,
  SpellCheck2,
  X,
} from "lucide-react";
import type { KeyboardEvent, ReactNode } from "react";
import {
  Button,
  Dialog,
  Heading,
  Modal,
  ModalOverlay,
} from "react-aria-components";
import { Link } from "react-router-dom";

import { BalighWordmark } from "../../design-system";
import { EditableDocument } from "../../features/editor/EditableDocument";
import {
  getLineFormat,
  getSelectedLineIndices,
  isRangeCovered,
  resolveFormattingRange,
  useEditorController,
  type FilterValue,
} from "../../features/editor/useEditorController";
import type {
  CorrectionCategory,
  DraftSummary,
} from "../../features/editor/types";
import { ArabicConfettiButton } from "../../shared/ui/ArabicConfettiButton";
import { ThemeControl } from "../../shared/ui/ThemeControl";
import "./editor.css";

const filterLabels: Record<FilterValue, string> = {
  spelling: "إملاء",
  grammar: "نحو",
  style: "أسلوب",
};

const correctionMeta: Record<
  CorrectionCategory,
  { label: string; icon: typeof SpellCheck2 }
> = {
  spelling: { label: "إملاء", icon: SpellCheck2 },
  grammar: { label: "نحو", icon: CircleAlert },
  style: { label: "أسلوب", icon: Sparkles },
};

function DraftList({
  drafts,
  activeDraftId,
  selectDraft,
}: {
  drafts: DraftSummary[];
  activeDraftId: string;
  selectDraft: (draftId: string) => void;
}) {
  if (drafts.length === 0) {
    return (
      <div className="editor-page__empty-state">
        <span>
          <FolderOpen aria-hidden="true" size={20} />
        </span>
        <strong>لا توجد مسودات بعد</strong>
        <p>أضف نصاً جديداً لتظهره هذه القائمة.</p>
      </div>
    );
  }

  return (
    <div className="editor-page__draft-list" aria-label="المسودات">
      {drafts.map((draft) => (
        <Button
          aria-pressed={draft.id === activeDraftId}
          className="editor-page__draft-item"
          data-active={draft.id === activeDraftId || undefined}
          key={draft.id}
          onPress={() => selectDraft(draft.id)}
        >
          <span className="editor-page__draft-item-title">{draft.title}</span>
          <span className="editor-page__draft-item-meta">
            {draft.stageLabel} · {draft.updatedAt}
          </span>
        </Button>
      ))}
    </div>
  );
}

function ToolbarButton({
  label,
  active = false,
  className,
  onPress,
  children,
}: {
  label: string;
  active?: boolean;
  className?: string;
  onPress: () => void;
  children: ReactNode;
}) {
  return (
    <Button
      aria-label={label}
      aria-pressed={active}
      className={["editor-page__toolbar-button", className]
        .filter(Boolean)
        .join(" ")}
      data-active={active || undefined}
      onPress={onPress}
    >
      {children}
    </Button>
  );
}

function Drawer({
  isOpen,
  title,
  onClose,
  children,
}: {
  isOpen: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  return (
    <ModalOverlay
      className="editor-page__mobile-overlay"
      isDismissable
      isOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <Modal className="editor-page__mobile-panel">
        <Dialog className="editor-page__mobile-dialog">
          <div className="editor-page__mobile-panel-header">
            <Heading slot="title">{title}</Heading>
            <Button
              aria-label="إغلاق اللوحة"
              className="editor-page__icon-button"
              onPress={onClose}
            >
              <X aria-hidden="true" size={18} />
            </Button>
          </div>
          {children}
        </Dialog>
      </Modal>
    </ModalOverlay>
  );
}

function SuggestionMenu({
  open,
  mode,
  anchorRect,
  suggestions,
  highlightedIndex,
  onHover,
  onSelect,
}: {
  open: boolean;
  mode: "word" | "sentence" | null;
  anchorRect: {
    top: number;
    left: number;
    width: number;
    height: number;
  } | null;
  suggestions: { id: string; label: string; displayText: string }[];
  highlightedIndex: number;
  onHover: (index: number) => void;
  onSelect: (index: number) => void;
}) {
  if (!open || !anchorRect || suggestions.length === 0) return null;

  return (
    <div
      className="editor-page__suggestions"
      data-mode={mode ?? undefined}
      style={{
        top: anchorRect.top + anchorRect.height + window.scrollY + 10,
        left: anchorRect.left + window.scrollX,
      }}
    >
      <div className="editor-page__suggestions-header">
        <Sparkles aria-hidden="true" size={15} />
        <span>{mode === "word" ? "إكمال الكلمة" : "متابعة الجملة"}</span>
      </div>
      <div className="editor-page__suggestions-list" role="listbox">
        {suggestions.map((suggestion, index) => (
          <button
            aria-selected={highlightedIndex === index}
            className="editor-page__suggestion-item"
            data-active={highlightedIndex === index || undefined}
            key={suggestion.id}
            onClick={() => onSelect(index)}
            onMouseEnter={() => onHover(index)}
            type="button"
          >
            <strong>{suggestion.label}</strong>
            <span>{suggestion.displayText}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export function EditorPage() {
  const {
    drafts,
    draftsLoading,
    activeDraft,
    activeDraftId,
    activeFilter,
    expandedCorrectionId,
    focusedCorrectionId,
    navigationOpen,
    correctionsOpen,
    selection,
    correctionCounts,
    visibleCorrections,
    suggestionsEnabled,
    suggestionState,
    suggestionAnchorRect,
    isHydratingDraft,
    selectDraft,
    addDraft,
    updateTitle,
    updateBody,
    updateSelection,
    setSuggestionAnchorRect,
    setFilter,
    toggleExpanded,
    focusCorrection,
    acceptCorrection,
    ignoreCorrection,
    togglePanel,
    closePanel,
    toggleStrong,
    applyTashkeel,
    cycleList,
    setAlign,
    toggleSuggestionsEnabled,
    cycleSuggestion,
    highlightSuggestion,
    applySuggestion,
    closeSuggestions,
  } = useEditorController();

  const navigationContent = (
    <div className="editor-page__navigation-content">
      <div className="editor-page__side-brand">
        <BalighWordmark className="editor-page__wordmark" />
        <strong>مساعد الكتابة الذكي</strong>
        <span>مساحة هادئة لكتابة عربية أدق</span>
      </div>

      <ArabicConfettiButton
        className="editor-page__primary-action"
        onPress={addDraft}
      >
        <FilePlus2 aria-hidden="true" size={18} />
        إضافة نص
      </ArabicConfettiButton>

      <section className="editor-page__rail-section">
        <div className="editor-page__rail-heading">
          <h2>مسوداتي</h2>
          <span>{drafts.length}</span>
        </div>
        <DraftList
          activeDraftId={activeDraftId}
          drafts={drafts}
          selectDraft={selectDraft}
        />
      </section>

      <section className="editor-page__rail-section editor-page__secondary-links">
        <h2>مراجع الكتابة</h2>
        <Link className="editor-page__side-link" to="/rules">
          <Languages aria-hidden="true" size={19} />
          <span>القواعد النحوية</span>
        </Link>
        <Link className="editor-page__side-link" to="/mo3gm">
          <BookOpenText aria-hidden="true" size={19} />
          <span>المعجم</span>
        </Link>
      </section>
    </div>
  );

  if (!activeDraft) {
    return (
      <main className="editor-page editor-page--loading">
        <div className="editor-page__loading-state">
          {draftsLoading || isHydratingDraft ? (
            <>
              <LoaderCircle
                aria-hidden="true"
                className="editor-page__spinner"
                size={26}
              />
              <p>جار تجهيز المحرر...</p>
            </>
          ) : (
            <>
              <FolderOpen aria-hidden="true" size={26} />
              <strong>لا توجد مسودة نشطة</strong>
              <p>أنشئ أول مسودة وسنفتحها لك مباشرة داخل المحرر.</p>
              <ArabicConfettiButton
                className="editor-page__primary-action"
                onPress={addDraft}
              >
                <FilePlus2 aria-hidden="true" size={18} />
                إضافة أول نص
              </ArabicConfettiButton>
            </>
          )}
        </div>
      </main>
    );
  }

  const revealCorrection = (correctionId: string) => {
    const correction = activeDraft.corrections.find(
      (entry) => entry.id === correctionId,
    );
    if (!correction) return;

    if (activeFilter !== correction.category) {
      setFilter(correction.category);
    }
    if (expandedCorrectionId !== correctionId) {
      toggleExpanded(correctionId);
    } else {
      focusCorrection(correctionId);
    }
    if (window.matchMedia("(max-width: 1099px)").matches) {
      togglePanel("corrections");
    }
  };

  const correctionsContent = (
    <div className="editor-page__corrections-content">
      <div className="editor-page__errors-header">
        <div>
          <p>مراجعة النص</p>
          <h2>الملاحظات</h2>
        </div>
        <span aria-label={`${correctionCounts.all} ملاحظات`}>
          {correctionCounts.all}
        </span>
      </div>

      <div className="editor-page__filter-stack" aria-label="فلاتر التصحيحات">
        {(["spelling", "grammar", "style"] as const).map((filter) => {
          const Icon = correctionMeta[filter].icon;
          return (
            <Button
              aria-pressed={activeFilter === filter}
              className="editor-page__filter"
              data-active={activeFilter === filter || undefined}
              key={filter}
              onPress={() => setFilter(filter)}
            >
              <span className="editor-page__filter-label">
                <Icon aria-hidden="true" size={17} />
                {filterLabels[filter]}
              </span>
              <span className="editor-page__filter-count">
                {correctionCounts[filter]}
              </span>
            </Button>
          );
        })}
      </div>

      <div className="editor-page__section-heading">
        <h3>{filterLabels[activeFilter]}</h3>
        <span>{visibleCorrections.length}</span>
      </div>

      <div className="editor-page__correction-list">
        {visibleCorrections.length === 0 ? (
          <div className="editor-page__empty-state">
            <span>
              <Check aria-hidden="true" size={20} />
            </span>
            <strong>لا توجد ملاحظات هنا</strong>
            <p>راجع قسماً آخر أو واصل الكتابة.</p>
          </div>
        ) : (
          visibleCorrections.map((correction) => {
            const meta = correctionMeta[correction.category];
            const expanded = expandedCorrectionId === correction.id;
            const stale = correction.status === "stale";

            return (
              <article
                className="editor-page__correction-card"
                data-active={focusedCorrectionId === correction.id || undefined}
                data-kind={correction.kind}
                data-stale={stale || undefined}
                data-tone={correction.category}
                key={correction.id}
              >
                <button
                  aria-expanded={expanded}
                  className="editor-page__correction-summary"
                  onClick={() => toggleExpanded(correction.id)}
                  type="button"
                >
                  <span className="editor-page__correction-meta">
                    <span className="editor-page__correction-tag">
                      {meta.label}
                    </span>
                    {correction.kind === "detection" && (
                      <span className="editor-page__correction-tag">
                        رصد فقط
                      </span>
                    )}
                    <span className="editor-page__correction-line">
                      {correction.lineLabel}
                    </span>
                  </span>
                  <strong>{correction.title}</strong>
                  <span className="editor-page__correction-line">
                    {correction.taxonomyLabel}
                  </span>
                  {correction.kind === "correction" ? (
                    <span className="editor-page__correction-change">
                      <del>{correction.original}</del>
                      <span aria-hidden="true">←</span>
                      <ins>{correction.replacement}</ins>
                    </span>
                  ) : (
                    <span className="editor-page__correction-change">
                      <span>النص المرصود:</span>
                      <strong>{correction.original}</strong>
                    </span>
                  )}
                </button>

                {expanded && (
                  <div className="editor-page__correction-details">
                    <p>{correction.explanation}</p>
                    <p className="editor-page__rule-link">
                      {correction.ruleLabel} · {correction.sourceModule}
                    </p>
                    {stale && (
                      <p className="editor-page__stale-note">
                        <CircleAlert aria-hidden="true" size={15} />
                        تغيّر هذا الموضع بعد تعديل النص يدوياً.
                      </p>
                    )}
                    <div className="editor-page__correction-actions">
                      {correction.kind === "correction" && (
                        <Button
                          className="editor-page__accept-button"
                          isDisabled={stale}
                          onPress={() => acceptCorrection(correction.id)}
                        >
                          <Check aria-hidden="true" size={16} />
                          قبول
                        </Button>
                      )}
                      <Button
                        className="editor-page__ignore-button"
                        onPress={() => ignoreCorrection(correction.id)}
                      >
                        {correction.kind === "correction" ? "تجاهل" : "إخفاء"}
                      </Button>
                    </div>
                  </div>
                )}
              </article>
            );
          })
        )}
      </div>
    </div>
  );

  const formattingRange = resolveFormattingRange(activeDraft.body, selection);
  const selectedLines = getSelectedLineIndices(activeDraft.body, selection);
  const strongActive = isRangeCovered(
    activeDraft.formatting.strong,
    formattingRange,
  );
  const currentAlignment = selectedLines.every(
    (line) => getLineFormat(activeDraft.formatting, line).align === "center",
  )
    ? "center"
    : selectedLines.every(
          (line) => getLineFormat(activeDraft.formatting, line).align === "end",
        )
      ? "end"
      : "start";
  const listActive = selectedLines.some(
    (line) => getLineFormat(activeDraft.formatting, line).list !== "none",
  );
  const currentList = getLineFormat(
    activeDraft.formatting,
    selectedLines[0] ?? 0,
  ).list;

  const handleEditorKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (!suggestionState.isOpen) return;
    if (event.key === "Tab") {
      event.preventDefault();
      cycleSuggestion(event.shiftKey ? -1 : 1);
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      applySuggestion();
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      closeSuggestions();
    }
  };

  return (
    <main className="editor-page">
      <header className="editor-page__topbar">
        <div className="editor-page__topbar-actions">
          <ThemeControl />
          <Link
            aria-label="العودة إلى الصفحة الرئيسية"
            className="editor-page__home-link"
            to="/"
          >
            <Home aria-hidden="true" size={18} />
          </Link>
        </div>
        <BalighWordmark
          aria-label="بليغ"
          className="editor-page__topbar-logo"
        />
      </header>

      <aside className="editor-page__rail editor-page__rail--navigation">
        {navigationContent}
      </aside>

      <section className="editor-page__workspace">
        <header className="editor-page__toolbar-row">
          <div
            aria-label="أدوات عرض النص"
            className="editor-page__toolbar"
            role="toolbar"
          >
            <ToolbarButton
              active={strongActive}
              label="عرض النص بخط عريض"
              onPress={() => toggleStrong(selection)}
            >
              <Bold aria-hidden="true" size={18} />
            </ToolbarButton>
            <ToolbarButton
              className="editor-page__toolbar-button--tashkeel"
              label="إضافة التشكيل"
              onPress={applyTashkeel}
            >
              <span aria-hidden="true" className="editor-page__toolbar-glyph">
                شّـ
              </span>
            </ToolbarButton>
            <ToolbarButton
              active={suggestionsEnabled}
              label={
                suggestionsEnabled ? "تعطيل الاقتراحات" : "تفعيل الاقتراحات"
              }
              onPress={toggleSuggestionsEnabled}
            >
              <Sparkles aria-hidden="true" size={18} />
            </ToolbarButton>
            <span className="editor-page__toolbar-divider" />
            <ToolbarButton
              active={listActive}
              label={`نوع القائمة: ${
                currentList === "none"
                  ? "بدون قائمة"
                  : currentList === "bullet"
                    ? "نقطية"
                    : "رقمية"
              }`}
              onPress={() => cycleList(selection)}
            >
              {currentList === "numbered" ? (
                <ListOrdered aria-hidden="true" size={18} />
              ) : (
                <List aria-hidden="true" size={18} />
              )}
            </ToolbarButton>
            <ToolbarButton
              active={currentAlignment === "start"}
              label="محاذاة لليمين"
              onPress={() => setAlign(selection, "start")}
            >
              <AlignRight aria-hidden="true" size={18} />
            </ToolbarButton>
            <ToolbarButton
              active={currentAlignment === "center"}
              label="محاذاة للمنتصف"
              onPress={() => setAlign(selection, "center")}
            >
              <AlignCenter aria-hidden="true" size={18} />
            </ToolbarButton>
            <ToolbarButton
              active={currentAlignment === "end"}
              label="محاذاة لليسار"
              onPress={() => setAlign(selection, "end")}
            >
              <AlignLeft aria-hidden="true" size={18} />
            </ToolbarButton>
          </div>
        </header>

        <section className="editor-page__editor-surface">
          <div className="editor-page__document">
            <input
              aria-label="عنوان النص"
              className="editor-page__title-input"
              onChange={(event) => updateTitle(event.target.value)}
              type="text"
              value={activeDraft.title}
            />
            <EditableDocument
              body={activeDraft.body}
              corrections={activeDraft.corrections}
              focusedCorrectionId={focusedCorrectionId}
              formatting={activeDraft.formatting}
              onBodyChange={updateBody}
              onCaretRectChange={setSuggestionAnchorRect}
              onCorrectionFocus={revealCorrection}
              onEditorKeyDown={handleEditorKeyDown}
              onSelectionChange={updateSelection}
            />
          </div>
          <SuggestionMenu
            anchorRect={suggestionAnchorRect}
            highlightedIndex={suggestionState.highlightedIndex}
            mode={suggestionState.mode}
            onHover={highlightSuggestion}
            onSelect={applySuggestion}
            open={suggestionState.isOpen}
            suggestions={suggestionState.suggestions}
          />
        </section>

        <nav className="editor-page__mobile-actions" aria-label="لوحات المحرر">
          <Button
            className="editor-page__mobile-action"
            onPress={() => togglePanel("navigation")}
          >
            <FolderOpen aria-hidden="true" size={18} />
            المسودات
          </Button>
          <Button
            className="editor-page__mobile-action"
            onPress={() => togglePanel("corrections")}
          >
            <CircleAlert aria-hidden="true" size={18} />
            الملاحظات
            <span>{correctionCounts.all}</span>
          </Button>
        </nav>
      </section>

      <aside className="editor-page__rail editor-page__rail--corrections">
        {correctionsContent}
      </aside>

      <Drawer
        isOpen={navigationOpen}
        onClose={() => closePanel("navigation")}
        title="المسودات"
      >
        {navigationContent}
      </Drawer>

      <Drawer
        isOpen={correctionsOpen}
        onClose={() => closePanel("corrections")}
        title="الملاحظات"
      >
        {correctionsContent}
      </Drawer>
    </main>
  );
}
