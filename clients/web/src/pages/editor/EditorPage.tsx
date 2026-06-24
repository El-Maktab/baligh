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
  Italic,
  Languages,
  List,
  ListOrdered,
  Sparkles,
  SpellCheck2,
  X,
} from "lucide-react";
import { useState, type ReactNode } from "react";
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
  type FilterValue,
  useEditorDemo,
} from "../../features/editor/useEditorDemo";
import type {
  CorrectionCategory,
  EditorDraft,
  EditorTextRange,
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
  drafts: EditorDraft[];
  activeDraftId: string;
  selectDraft: (draftId: string) => void;
}) {
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

export function EditorPage() {
  const [selection, setSelection] = useState<EditorTextRange>([0, 0]);
  const {
    state,
    activeDraft,
    correctionCounts,
    visibleCorrections,
    selectDraft,
    addDraft,
    updateTitle,
    updateBody,
    setFilter,
    toggleExpanded,
    focusCorrection,
    acceptCorrection,
    ignoreCorrection,
    togglePanel,
    closePanel,
    toggleStrong,
    toggleEmphasis,
    cycleList,
    setAlign,
  } = useEditorDemo();

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
          <span>{state.drafts.length}</span>
        </div>
        <DraftList
          activeDraftId={state.activeDraftId}
          drafts={state.drafts}
          selectDraft={(draftId) => {
            setSelection([0, 0]);
            selectDraft(draftId);
          }}
        />
      </section>

      <section className="editor-page__rail-section editor-page__secondary-links">
        <h2>مراجع الكتابة</h2>
        <Button
          className="editor-page__side-link"
          isDisabled
          aria-label="القواعد النحوية، غير متاحة حالياً"
        >
          <Languages aria-hidden="true" size={19} />
          <span>القواعد النحوية</span>
          <small>قريباً</small>
        </Button>
        <Button
          className="editor-page__side-link"
          isDisabled
          aria-label="المعجم، غير متاح حالياً"
        >
          <BookOpenText aria-hidden="true" size={19} />
          <span>المعجم</span>
          <small>قريباً</small>
        </Button>
      </section>
    </div>
  );

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
              aria-pressed={state.activeFilter === filter}
              className="editor-page__filter"
              data-active={state.activeFilter === filter || undefined}
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
        <h3>{filterLabels[state.activeFilter]}</h3>
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
            const expanded = state.expandedCorrectionId === correction.id;
            const stale = correction.status === "stale";

            return (
              <article
                className="editor-page__correction-card"
                data-active={
                  state.focusedCorrectionId === correction.id || undefined
                }
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
                    <span className="editor-page__correction-line">
                      {correction.lineLabel}
                    </span>
                  </span>
                  <strong>{correction.title}</strong>
                  <span className="editor-page__correction-change">
                    <del>{correction.original}</del>
                    <span aria-hidden="true">←</span>
                    <ins>{correction.replacement}</ins>
                  </span>
                </button>

                {expanded && (
                  <div className="editor-page__correction-details">
                    <p>{correction.explanation}</p>
                    <p className="editor-page__rule-link">
                      {correction.ruleLabel}
                    </p>
                    {stale && (
                      <p className="editor-page__stale-note">
                        <CircleAlert aria-hidden="true" size={15} />
                        تغيّر هذا الموضع بعد تعديل النص يدوياً.
                      </p>
                    )}
                    <div className="editor-page__correction-actions">
                      <Button
                        className="editor-page__accept-button"
                        isDisabled={stale}
                        onPress={() => acceptCorrection(correction.id)}
                      >
                        <Check aria-hidden="true" size={16} />
                        قبول
                      </Button>
                      <Button
                        className="editor-page__ignore-button"
                        onPress={() => ignoreCorrection(correction.id)}
                      >
                        تجاهل
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

  const revealCorrection = (correctionId: string) => {
    const correction = activeDraft.corrections.find(
      (entry) => entry.id === correctionId,
    );
    if (!correction) return;

    if (state.activeFilter !== correction.category) {
      setFilter(correction.category);
    }
    if (state.expandedCorrectionId !== correctionId) {
      toggleExpanded(correctionId);
    } else {
      focusCorrection(correctionId);
    }
    if (window.matchMedia("(max-width: 1099px)").matches) {
      togglePanel("corrections");
    }
  };

  const formattingRange = resolveFormattingRange(activeDraft.body, selection);
  const selectedLines = getSelectedLineIndices(activeDraft.body, selection);
  const strongActive = isRangeCovered(
    activeDraft.formatting.strong,
    formattingRange,
  );
  const emphasisActive = isRangeCovered(
    activeDraft.formatting.emphasis,
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
              active={emphasisActive}
              className="editor-page__toolbar-button--italic"
              label="تمييز النص"
              onPress={() => toggleEmphasis(selection)}
            >
              <Italic aria-hidden="true" size={18} />
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
              focusedCorrectionId={state.focusedCorrectionId}
              formatting={activeDraft.formatting}
              onBodyChange={updateBody}
              onCorrectionFocus={revealCorrection}
              onSelectionChange={setSelection}
            />
          </div>
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
        isOpen={state.navigationOpen}
        onClose={() => closePanel("navigation")}
        title="المسودات"
      >
        {navigationContent}
      </Drawer>

      <Drawer
        isOpen={state.correctionsOpen}
        onClose={() => closePanel("corrections")}
        title="الملاحظات"
      >
        {correctionsContent}
      </Drawer>
    </main>
  );
}
