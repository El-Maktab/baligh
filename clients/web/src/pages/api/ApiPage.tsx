import { useState } from "react";
import {
  Braces,
  Check,
  Code2,
  Copy,
  Database,
  FileJson,
  Languages,
  Search,
  Terminal,
} from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { Button, Input, SearchField } from "react-aria-components";

import { motionPresets } from "../../design-system";
import { ReferenceHeader } from "../../shared/reference/ReferenceHeader";
import "./apiPage.css";

// Interface Definitions
interface QueryParam {
  name: string;
  type: string;
  required: boolean;
  description: string;
}

interface Endpoint {
  id: string;
  method: "GET" | "POST" | "PATCH";
  path: string;
  title: string;
  description: string;
  params?: QueryParam[];
  requestJson?: string;
  responseJson: string;
}

interface ApiGroup {
  id: string;
  title: string;
  icon: typeof Terminal;
  endpoints: Endpoint[];
}

// Full API Contracts Definition
const apiGroups: ApiGroup[] = [
  {
    id: "editor",
    title: "مساعد الكتابة (Editor API)",
    icon: Code2,
    endpoints: [
      {
        id: "list-drafts",
        method: "GET",
        path: "/api/v1/drafts",
        title: "قائمة المسودات (List Drafts)",
        description:
          "استرجاع قائمة بجميع مسودات المستخدم مع ملخص لكل مسودة (المعرف، العنوان، حالة التقدم، وتاريخ التعديل). إذا لم تكن هناك بيانات بعد فستعود المصفوفة فارغة، ويقوم الخادم افتراضياً بإنشاء مسودة أولية لتسهيل فتح المحرر.",
        responseJson: JSON.stringify(
          [
            {
              id: "draft-1",
              title: "مقدمة عن الخط العربي",
              stageLabel: "مراجعة إملائية",
              updatedAt: "منذ دقيقتين",
            },
            {
              id: "draft-2",
              title: "قواعد الكتابة السليمة",
              stageLabel: "جاهز للربط",
              updatedAt: "منذ يومين",
            },
          ],
          null,
          2,
        ),
      },
      {
        id: "create-draft",
        method: "POST",
        path: "/api/v1/drafts",
        title: "إنشاء مسودة جديدة (Create Draft)",
        description: "إنشاء مسودة جديدة فارغة أو مع توفير عنوان ومحتوى أولي.",
        params: [
          {
            name: "title",
            type: "string (اختياري)",
            required: false,
            description: "عنوان المسودة المراد إنشاؤها.",
          },
          {
            name: "body",
            type: "string (اختياري)",
            required: false,
            description: "المحتوى الأولي للمسودة.",
          },
        ],
        requestJson: JSON.stringify(
          {
            title: "مسودة جديدة",
            body: "اكتب النص هنا...",
          },
          null,
          2,
        ),
        responseJson: JSON.stringify(
          {
            id: "draft-3",
            title: "مسودة جديدة",
            body: "اكتب النص هنا...",
            stageLabel: "جاهز للربط",
            updatedAt: "الآن",
            savedAt: "2026-06-25T12:00:00.000Z",
            revision: 1,
            formatting: {
              strong: [],
              emphasis: [],
              lines: {},
            },
            corrections: [],
          },
          null,
          2,
        ),
      },
      {
        id: "get-draft",
        method: "GET",
        path: "/api/v1/drafts/{draftId}",
        title: "جلب مسودة محددة (Get Draft)",
        description:
          "استرجاع تفاصيل مسودة معينة كاملة بما فيها نص المسودة والتصحيحات والتنسيقات.",
        params: [
          {
            name: "draftId",
            type: "string (مسار)",
            required: true,
            description: "معرّف المسودة المطلوب جلبها.",
          },
        ],
        responseJson: JSON.stringify(
          {
            id: "draft-1",
            title: "نص التجربة",
            body: "هذا النص يحتوى على خطأ.",
            stageLabel: "مسودة نشطة",
            updatedAt: "منذ ساعة",
            savedAt: "2026-06-25T11:00:00.000Z",
            revision: 3,
            formatting: {
              strong: [],
              emphasis: [],
              lines: {},
            },
            corrections: [
              {
                id: "err-1",
                category: "spelling",
                status: "active",
                span: { start: 14, end: 19 },
                title: "ياء زائفة",
                lineLabel: "السطر ١",
                original: "يحتوى",
                replacement: "يحتوي",
                explanation:
                  "الأفعال المعتلة الآخر بالياء تُكتب بالياء المنقوطة (ي) وليس بالألف المقصورة (ى).",
                ruleLabel: "كتابة الياء المتطرفة",
              },
            ],
          },
          null,
          2,
        ),
      },
      {
        id: "update-draft",
        method: "PATCH",
        path: "/api/v1/drafts/{draftId}",
        title: "تحديث مسودة (Update Draft)",
        description:
          "حفظ العنوان الجديد أو النص للمسودة مع التحقق من رقم المراجعة (revision) لتفادي التعارض.",
        params: [
          {
            name: "draftId",
            type: "string (مسار)",
            required: true,
            description: "معرّف المسودة المراد تحديثها.",
          },
          {
            name: "title",
            type: "string (اختياري)",
            required: false,
            description: "العنوان الجديد للمسودة.",
          },
          {
            name: "body",
            type: "string (اختياري)",
            required: false,
            description: "النص الجديد للمسودة.",
          },
          {
            name: "clientRevision",
            type: "number",
            required: true,
            description:
              "رقم مراجعة المسودة الحالي لدى العميل للتحقق من الاتساق.",
          },
        ],
        requestJson: JSON.stringify(
          {
            title: "عنوان معدل",
            body: "النص بعد التعديل اليدوي.",
            clientRevision: 3,
          },
          null,
          2,
        ),
        responseJson: JSON.stringify(
          {
            draft: {
              id: "draft-1",
              title: "عنوان معدل",
              body: "النص بعد التعديل اليدوي.",
              stageLabel: "مسودة نشطة",
              updatedAt: "الآن",
              savedAt: "2026-06-25T12:00:00.000Z",
              revision: 4,
              formatting: {
                strong: [],
                emphasis: [],
                lines: {},
              },
              corrections: [],
            },
            persistedRevision: 4,
            savedAt: "2026-06-25T12:00:00.000Z",
          },
          null,
          2,
        ),
      },
      {
        id: "analyze-draft",
        method: "POST",
        path: "/api/v1/drafts/{draftId}/analyze",
        title: "تحليل المسودة (Analyze Draft)",
        description:
          "تشغيل محرك التدقيق النحوي والإملائي والأسلوبي واستخراج الملاحظات والتصحيحات المقترحة.",
        params: [
          {
            name: "draftId",
            type: "string (مسار)",
            required: true,
            description: "معرّف المسودة.",
          },
          {
            name: "body",
            type: "string",
            required: true,
            description: "محتوى النص الكامل للتحليل.",
          },
          {
            name: "selection",
            type: "{ start: number, end: number }",
            required: true,
            description: "موضع اختيار النص الحالي.",
          },
          {
            name: "caret",
            type: "number",
            required: true,
            description: "موضع مؤشر الكتابة داخل النص.",
          },
          {
            name: "clientRevision",
            type: "number",
            required: true,
            description: "رقم المراجعة الحالي لدى العميل.",
          },
          {
            name: "categories",
            type: "string[]",
            required: true,
            description: "فئات التدقيق المطلوبة: spelling, grammar, style.",
          },
        ],
        requestJson: JSON.stringify(
          {
            body: "هذا النص يحتوى على خطأ.",
            selection: { start: 23, end: 23 },
            caret: 23,
            clientRevision: 4,
            categories: ["spelling", "grammar", "style"],
          },
          null,
          2,
        ),
        responseJson: JSON.stringify(
          {
            analysisRevision: 4,
            corrections: [
              {
                id: "err-1",
                category: "spelling",
                status: "active",
                span: { start: 14, end: 19 },
                title: "ياء زائفة",
                lineLabel: "السطر ١",
                original: "يحتوى",
                replacement: "يحتوي",
                explanation:
                  "الأفعال المعتلة الآخر بالياء تُكتب بالياء المنقوطة (ي) وليس بالألف المقصورة (ى).",
                ruleLabel: "كتابة الياء المتطرفة",
              },
            ],
            counts: {
              all: 1,
              spelling: 1,
              grammar: 0,
              style: 0,
            },
          },
          null,
          2,
        ),
      },
      {
        id: "accept-correction",
        method: "POST",
        path: "/api/v1/drafts/{draftId}/corrections/{correctionId}/accept",
        title: "قبول تصحيح (Accept Correction)",
        description:
          "تطبيق تصحيح مقترح معين على النص وتحديث محتوى المسودة وزيادة رقم المراجعة.",
        params: [
          {
            name: "draftId",
            type: "string (مسار)",
            required: true,
            description: "معرّف المسودة.",
          },
          {
            name: "correctionId",
            type: "string (مسار)",
            required: true,
            description: "معرّف الملاحظة المطلوب قبولها وتطبيق اقتراحها.",
          },
          {
            name: "body",
            type: "string (اختياري)",
            required: false,
            description: "محتوى النص الحالي للتأكد من المزامنة قبل التعديل.",
          },
          {
            name: "clientRevision",
            type: "number",
            required: true,
            description: "رقم المراجعة الحالي لدى العميل.",
          },
        ],
        requestJson: JSON.stringify(
          {
            body: "هذا النص يحتوى على خطأ.",
            clientRevision: 4,
          },
          null,
          2,
        ),
        responseJson: JSON.stringify(
          {
            draftBody: "هذا النص يحتوي على خطأ.",
            persistedRevision: 5,
            corrections: [
              {
                id: "err-1",
                category: "spelling",
                status: "accepted",
                span: { start: 14, end: 19 },
                title: "ياء زائفة",
                lineLabel: "السطر ١",
                original: "يحتوى",
                replacement: "يحتوي",
                explanation:
                  "الأفعال المعتلة الآخر بالياء تُكتب بالياء المنقوطة (ي) وليس بالألف المقصورة (ى).",
                ruleLabel: "كتابة الياء المتطرفة",
              },
            ],
            counts: {
              all: 0,
              spelling: 0,
              grammar: 0,
              style: 0,
            },
          },
          null,
          2,
        ),
      },
      {
        id: "ignore-correction",
        method: "POST",
        path: "/api/v1/drafts/{draftId}/corrections/{correctionId}/ignore",
        title: "تجاهل تصحيح (Ignore Correction)",
        description:
          "تغيير حالة الملاحظة المقترحة إلى متجاهلة (ignored) لعدم إزعاج الكاتب بها مجدداً.",
        params: [
          {
            name: "draftId",
            type: "string (مسار)",
            required: true,
            description: "معرّف المسودة.",
          },
          {
            name: "correctionId",
            type: "string (مسار)",
            required: true,
            description: "معرّف الملاحظة المطلوب تجاهلها.",
          },
          {
            name: "body",
            type: "string (اختياري)",
            required: false,
            description: "محتوى النص الحالي للتأكد من المزامنة.",
          },
          {
            name: "clientRevision",
            type: "number",
            required: true,
            description: "رقم المراجعة الحالي لدى العميل.",
          },
        ],
        requestJson: JSON.stringify(
          {
            clientRevision: 5,
          },
          null,
          2,
        ),
        responseJson: JSON.stringify(
          {
            correctionId: "err-1",
            status: "ignored",
            corrections: [
              {
                id: "err-1",
                category: "spelling",
                status: "ignored",
                span: { start: 14, end: 19 },
                title: "ياء زائفة",
                lineLabel: "السطر ١",
                original: "يحتوى",
                replacement: "يحتوي",
                explanation:
                  "الأفعال المعتلة الآخر بالياء تُكتب بالياء المنقوطة (ي) وليس بالألف المقصورة (ى).",
                ruleLabel: "كتابة الياء المتطرفة",
              },
            ],
            counts: {
              all: 0,
              spelling: 0,
              grammar: 0,
              style: 0,
            },
          },
          null,
          2,
        ),
      },
      {
        id: "get-suggestions",
        method: "POST",
        path: "/api/v1/drafts/{draftId}/suggestions",
        title: "الاقتراحات التلقائية (Get Suggestions)",
        description:
          "توقع وإكمال الكلمات أثناء الكتابة أو اقتراح نهايات مناسبة للجمل اعتماداً على موقع المؤشر.",
        params: [
          {
            name: "draftId",
            type: "string (مسار)",
            required: true,
            description: "معرّف المسودة.",
          },
          {
            name: "body",
            type: "string",
            required: true,
            description: "نص المسودة الكامل.",
          },
          {
            name: "selection",
            type: "{ start: number, end: number }",
            required: true,
            description: "موقع الاختيار الحالي للمؤشر.",
          },
          {
            name: "caret",
            type: "number",
            required: true,
            description: "موقع الكود/المؤشر العددي.",
          },
          {
            name: "clientRevision",
            type: "number",
            required: true,
            description: "رقم المراجعة الحالي للمسودة.",
          },
          {
            name: "mode",
            type: "string",
            required: true,
            description:
              "نمط الاقتراح: word (إكمال كلمة) أو sentence (متابعة جملة).",
          },
          {
            name: "limit",
            type: "number",
            required: true,
            description: "الحد الأقصى لعدد الاقتراحات المطلوبة.",
          },
        ],
        requestJson: JSON.stringify(
          {
            body: "الكتابة هي الم",
            selection: { start: 14, end: 14 },
            caret: 14,
            clientRevision: 5,
            mode: "word",
            limit: 3,
          },
          null,
          2,
        ),
        responseJson: JSON.stringify(
          {
            suggestionSessionId: "suggest-1719320000",
            mode: "word",
            replaceRange: { start: 11, end: 14 },
            suggestions: [
              {
                id: "word-0",
                label: "المحبة",
                displayText: "المحبة",
                insertText: "المحبة",
                kind: "word",
              },
              {
                id: "word-1",
                label: "المحرر",
                displayText: "المحرر",
                insertText: "المحرر",
                kind: "word",
              },
            ],
          },
          null,
          2,
        ),
      },
      {
        id: "apply-tashkeel",
        method: "POST",
        path: "/api/v1/drafts/{draftId}/tashkeel",
        title: "تطبيق التشكيل (Apply Tashkeel)",
        description:
          "تزويد النص المحدد بالتشكيل وتعديل الحركات الإملائية آلياً.",
        params: [
          {
            name: "draftId",
            type: "string (مسار)",
            required: true,
            description: "معرّف المسودة.",
          },
          {
            name: "body",
            type: "string",
            required: true,
            description: "نص المسودة الكامل.",
          },
          {
            name: "selection",
            type: "{ start: number, end: number }",
            required: true,
            description: "النطاق المحدد لتطبيق التشكيل عليه.",
          },
          {
            name: "clientRevision",
            type: "number",
            required: true,
            description: "رقم المراجعة الحالي للمسودة.",
          },
        ],
        requestJson: JSON.stringify(
          {
            body: "كتب بليغ نصا",
            selection: { start: 0, end: 12 },
            clientRevision: 5,
          },
          null,
          2,
        ),
        responseJson: JSON.stringify(
          {
            draftBody: "كَتَبَ بَلِيغٌ نَصَّاُ",
            replaceRange: { start: 0, end: 12 },
            persistedRevision: 6,
          },
          null,
          2,
        ),
      },
    ],
  },
  {
    id: "mo3gm",
    title: "المعجم (Mo3gm API)",
    icon: Database,
    endpoints: [
      {
        id: "mo3gm-bootstrap",
        method: "GET",
        path: "/api/v1/mo3gm",
        title: "تهيئة المعجم (Bootstrap)",
        description:
          "استرجاع البيانات الأولية لتهيئة واجهة المعجم مثل الكلمة المميزة وعمليات البحث الأخيرة.",
        responseJson: JSON.stringify(
          {
            initialQuery: "بليغ",
            featuredEntry: {
              word: "بليغ",
              vocalized: "بَلِيغ",
              root: "بلغ",
              partOfSpeech: "صفة مشبهة",
              meanings: [
                "الفصيح، ذو المنطق الحسن واللسان المؤثّر.",
                "البالغ أقصى الغاية أو الأثر العالي.",
              ],
              synonyms: ["فصيح", "مفوّه", "بين", "مؤثر"],
              antonyms: ["عاجز", "عيي", "ألكن"],
              examples: [
                {
                  source: "لسان العرب",
                  text: "تكلّم بلسان بليغ فأثّر في القلوب.",
                },
              ],
            },
            recentSearches: ["استنبط", "جذر", "متوارث"],
          },
          null,
          2,
        ),
      },
      {
        id: "mo3gm-search",
        method: "POST",
        path: "/api/v1/mo3gm/search",
        title: "البحث في المعجم (Search)",
        description:
          "البحث عن معاني كلمة محددة وجذرها ومرادفاتها وتفاصيل تصريفها.",
        params: [
          {
            name: "query",
            type: "string",
            required: true,
            description: "الكلمة العربية المراد البحث عنها.",
          },
        ],
        requestJson: JSON.stringify(
          {
            query: "بليغ",
          },
          null,
          2,
        ),
        responseJson: JSON.stringify(
          {
            query: "بليغ",
            entry: {
              word: "بليغ",
              vocalized: "بَلِيغ",
              root: "بلغ",
              partOfSpeech: "صفة مشبهة",
              meanings: ["الفصيح، ذو المنطق الحسن واللسان المؤثّر."],
              synonyms: ["فصيح", "مفوّه"],
              antonyms: ["عاجز", "عيي"],
              examples: [
                {
                  source: "المعجم المحيط",
                  text: "خطيبٌ بليغٌ يهزّ المنابر بكلماته.",
                },
              ],
            },
          },
          null,
          2,
        ),
      },
    ],
  },
  {
    id: "rules",
    title: "دليل القواعد (Rules API)",
    icon: Languages,
    endpoints: [
      {
        id: "rules-list",
        method: "GET",
        path: "/api/v1/rules",
        title: "قائمة القواعد (List Rules)",
        description:
          "جلب القواعد اللغوية والنحوية والأسلوبية التي يعتمد عليها مدقق بليغ في كشف الأخطاء.",
        responseJson: JSON.stringify(
          [
            {
              id: "rule-sp-1",
              category: "orthography",
              subtype: "yaleh",
              tier: "tier_1_rule_derived",
              title: "الياء المتطرفة والألف المقصورة",
              explanation:
                "يجب التفريق بين الياء (ي) التي تحتها نقطتان، والألف المقصورة (ى) التي ترسم كياء مهملة.",
              incorrect: "صليت على النبي",
              correct: "صليت علي النبي",
              note: "الأفعال المعتلة الآخر مثل (صلى) تُكتب بالألف المقصورة، أما الضمائر أو حروف الجر مثل (علي) فتكتب بالياء.",
            },
          ],
          null,
          2,
        ),
      },
      {
        id: "rules-categories",
        method: "GET",
        path: "/api/v1/rules/categories",
        title: "فئات القواعد (List Categories)",
        description:
          "جلب تصنيفات القواعد المتاحة لفرز القواعد حسب الفئة (نحو، إملاء، أسلوب).",
        responseJson: JSON.stringify(
          [
            {
              value: "all",
              label: "الكل",
            },
            {
              value: "syntax",
              label: "نحو",
            },
            {
              value: "orthography",
              label: "إملاء",
            },
            {
              value: "semantics",
              label: "استعمال لغوي",
            },
          ],
          null,
          2,
        ),
      },
    ],
  },
];

// Single Endpoint Rendering Component (handles tabs + copy state)
function EndpointCard({ endpoint }: { endpoint: Endpoint }) {
  const [activeTab, setActiveTab] = useState<"request" | "response">(
    endpoint.requestJson ? "request" : "response",
  );
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const codeToCopy =
      activeTab === "request" ? endpoint.requestJson : endpoint.responseJson;
    if (!codeToCopy) return;

    void navigator.clipboard.writeText(codeToCopy).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const getMethodClass = (method: Endpoint["method"]) => {
    switch (method) {
      case "GET":
        return "api-card__method--get";
      case "POST":
        return "api-card__method--post";
      case "PATCH":
        return "api-card__method--patch";
      default:
        return "";
    }
  };

  return (
    <article className="api-card" id={endpoint.id}>
      <div className="api-card__info">
        <div className="api-card__endpoint-row">
          <span
            className={`api-card__method ${getMethodClass(endpoint.method)}`}
          >
            {endpoint.method}
          </span>
          <code className="api-card__path">{endpoint.path}</code>
        </div>
        <h3 className="api-card__title">{endpoint.title}</h3>
        <p className="api-card__description">{endpoint.description}</p>

        {endpoint.params && endpoint.params.length > 0 && (
          <>
            <h4 className="api-card__subtitle">
              <FileJson size={16} /> معلمات الطلب
            </h4>
            <div className="api-card__params">
              {endpoint.params.map((param) => (
                <div className="api-card__param-item" key={param.name}>
                  <div className="api-card__param-name-row">
                    <span className="api-card__param-name">{param.name}</span>
                    <span className="api-card__param-type">{param.type}</span>
                    {param.required ? (
                      <span className="api-card__param-required">مطلوب</span>
                    ) : (
                      <span className="api-card__param-optional">اختياري</span>
                    )}
                  </div>
                  <p className="api-card__param-desc">{param.description}</p>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      <div className="api-card__code-side">
        <div className="api-card__tabs">
          {endpoint.requestJson && (
            <button
              className="api-card__tab"
              data-active={activeTab === "request"}
              onClick={() => setActiveTab("request")}
              type="button"
            >
              بيانات الطلب (Request)
            </button>
          )}
          <button
            className="api-card__tab"
            data-active={activeTab === "response"}
            onClick={() => setActiveTab("response")}
            type="button"
          >
            بيانات الاستجابة (Response)
          </button>
        </div>

        <div className="api-card__code-wrapper">
          <button
            className="api-card__copy-btn"
            onClick={handleCopy}
            title="نسخ الشفرة"
            type="button"
          >
            {copied ? (
              <>
                <Check size={14} />
                <span>تم النسخ!</span>
              </>
            ) : (
              <>
                <Copy size={14} />
                <span>نسخ</span>
              </>
            )}
          </button>
          <pre className="api-card__code">
            {activeTab === "request"
              ? endpoint.requestJson
              : endpoint.responseJson}
          </pre>
        </div>
      </div>
    </article>
  );
}

// Main Page Component
export function ApiPage() {
  const reduceMotion = useReducedMotion();
  const [searchQuery, setSearchQuery] = useState("");
  const [activeGroup, setActiveGroup] = useState<string>("all");

  // Filtering Logic
  const filteredGroups = apiGroups
    .map((group) => {
      const matchedEndpoints = group.endpoints.filter((endpoint) => {
        const query = searchQuery.toLowerCase();
        return (
          endpoint.title.toLowerCase().includes(query) ||
          endpoint.path.toLowerCase().includes(query) ||
          endpoint.description.toLowerCase().includes(query)
        );
      });
      return {
        ...group,
        endpoints: matchedEndpoints,
      };
    })
    .filter(
      (group) =>
        (activeGroup === "all" || group.id === activeGroup) &&
        group.endpoints.length > 0,
    );

  const getSidebarMethodClass = (method: Endpoint["method"]) => {
    switch (method) {
      case "GET":
        return "api-sidebar__method-badge--get";
      case "POST":
        return "api-sidebar__method-badge--post";
      case "PATCH":
        return "api-sidebar__method-badge--patch";
      default:
        return "";
    }
  };

  return (
    <main className="api-page">
      <ReferenceHeader />

      <section className="api-hero">
        <motion.div
          initial={reduceMotion ? false : motionPresets.enter.initial}
          animate={motionPresets.enter.animate}
          transition={motionPresets.enter.transition}
        >
          <p className="api-eyebrow">
            <Braces aria-hidden="true" size={18} /> دليل المطورين وواجهة الربط
            البرمجي
          </p>
          <h1>واجهة برمجة التطبيقات (API)</h1>
          <p className="api-hero__intro">
            توثيق كامل لجميع العقود، معالم الطلب، واستجابات خدمات بليغ المتمثلة
            في المحرر الذكي والمعجم ودليل القواعد.
          </p>
        </motion.div>
      </section>

      <section className="api-layout">
        {/* Endpoints Documentation Content Area */}
        <div className="api-content">
          {filteredGroups.length > 0 ? (
            filteredGroups.map((group) => (
              <div
                className="api-group"
                id={`group-${group.id}`}
                key={group.id}
              >
                <h2 className="api-group__title">
                  <group.icon aria-hidden="true" size={24} />
                  <span>{group.title}</span>
                </h2>
                {group.endpoints.map((endpoint) => (
                  <EndpointCard endpoint={endpoint} key={endpoint.id} />
                ))}
              </div>
            ))
          ) : (
            <div className="api-empty">
              <Search aria-hidden="true" size={28} />
              <h2>لم نعثر على أي تطابق</h2>
              <p>جرّب البحث بكلمة مفتاحية مختلفة أو تغيير تصفية المجموعات.</p>
            </div>
          )}
        </div>

        {/* Sidebar Navigation */}
        <aside className="api-sidebar">
          <div className="api-sidebar__heading">
            <Terminal aria-hidden="true" size={18} />
            <h2>روابط سريعة</h2>
          </div>
          <div style={{ padding: "0.8rem 1.2rem 0" }}>
            <SearchField
              aria-label="ابحث في العقود"
              className="rules-search"
              onChange={setSearchQuery}
              value={searchQuery}
            >
              <Search aria-hidden="true" size={16} />
              <Input
                placeholder="ابحث باسم العقد أو الرابط..."
                style={{ fontSize: "0.78rem" }}
              />
            </SearchField>
          </div>
          <div className="api-sidebar__menu">
            {/* Filter buttons */}
            <div
              className="rules-browser__filters"
              style={{ marginBottom: "0.75rem", gap: "0.35rem" }}
            >
              <Button
                aria-pressed={activeGroup === "all"}
                className="rules-browser__filter"
                data-active={activeGroup === "all" || undefined}
                onPress={() => setActiveGroup("all")}
                style={{ padding: "0.35rem 0.75rem", fontSize: "0.72rem" }}
              >
                الكل
              </Button>
              {apiGroups.map((g) => (
                <Button
                  aria-pressed={activeGroup === g.id}
                  className="rules-browser__filter"
                  data-active={activeGroup === g.id || undefined}
                  key={g.id}
                  onPress={() => setActiveGroup(g.id)}
                  style={{ padding: "0.35rem 0.75rem", fontSize: "0.72rem" }}
                >
                  {g.id === "editor"
                    ? "المحرر"
                    : g.id === "mo3gm"
                      ? "المعجم"
                      : "القواعد"}
                </Button>
              ))}
            </div>

            {filteredGroups.map((group) => (
              <div key={group.id}>
                <h3 className="api-sidebar__group-title">{group.title}</h3>
                <nav
                  className="api-sidebar__links"
                  aria-label={`روابط ${group.title}`}
                >
                  {group.endpoints.map((endpoint) => (
                    <a
                      className="api-sidebar__link"
                      href={`#${endpoint.id}`}
                      key={endpoint.id}
                      onClick={(e) => {
                        e.preventDefault();
                        const element = document.getElementById(endpoint.id);
                        if (element) {
                          element.scrollIntoView({ behavior: "smooth" });
                        }
                      }}
                    >
                      <span
                        className={`api-sidebar__method-badge ${getSidebarMethodClass(endpoint.method)}`}
                      >
                        {endpoint.method}
                      </span>
                      <span>{endpoint.title.split(" (")[0]}</span>
                    </a>
                  ))}
                </nav>
              </div>
            ))}
          </div>
        </aside>
      </section>
    </main>
  );
}
