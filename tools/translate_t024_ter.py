#!/usr/bin/env python3
"""Create the Arabic version of T-024-r0-ter (Two Winding + TER, Megger 5000V).

Source of truth: the English text of appr_docs/ad_subst/ad_sub_tp/T-024-r0-ter.pdf
(5 pages, extracted with pdftotext -layout). The translation follows the
terminology of the existing Arabic version of its sister document T-024-r0a
(new_translated/T-024-r0a.htm): تشريط = short circuit, بوشنج = bushing,
ميجر = megger. Nothing is added: fields left blank in the English original
(Issued to / Status) stay blank here. Test numbers and connections follow
the English original exactly.
"""
import json, os

DOC_ID = "arabic-web-ar-appr-docs-ar-ad-subst-ad-ss-docs-new-translated-t-024-r0a-ter-htm"
OUT = os.path.join(os.path.dirname(__file__), "..", "content", DOC_ID + ".json")

INTRO_AR = (
    "يحتوي هذا المستند على قائمة إجراءات اختبار المعدات، والتي يجب تنفيذها "
    "لمحولات القدرة طبقاً لتعليمات الشركة المصنعة."
)
SAFETY_AR = [
    "يتم عزل المحول من الخدمة وتأريضه.",
    "يجب كتابة أمر الشغل بعناية وتنفيذ ما جاء به من تعليمات.",
    "يجب أن يكون القائمون على الاختبار حاملين لفئات أمن صناعي مناسبة.",
    "يجب تسوير منطقة العمل ووضع اللافتات والتحذيرات المناسبة.",
    "يجب فك جميع أطراف الملفات من ناحية ملفات الجهد العالي والجهد المنخفض.",
    "يجب نظافة جميع البوشنجات بعناية لتجنب القراءة الخاطئة للميجر.",
    "لا يجب لمس أطراف كابلات الاختبار أثناء الاختبار لأنها تحمل جهد 5 ك.ف DC.",
]
METHOD_AR = (
    "يجب عمل تشريط على جميع الملفات كلٍّ على حدى، والتأكد من نظافة جميع "
    "البوشنجات لتجنب القراءة الخاطئة للميجر."
)
STEP_TAIL = [
    "نقوم بتشغيل جهاز الميجر والضغط على زر الاختبار بعد ضبط الميجر على 5 كيلو فولت DC.",
    "نقوم بتسجيل القراءة بعد 15 ثانية وبعد 60 ثانية.",
    "نقوم بفصل جهاز الميجر من زر الإغلاق وحساب قيمة R60 / R15.",
]

TESTS_AR = [
    {"n": 1, "label": "HV -------- LV + TER + E",
     "steps": [
         "نقوم بتوصيل التشريط على ملف الجهد المنخفض والملف الثالثي (TER) مع الأرضي.",
         "نقوم بتوصيل الكابل الموجب لجهاز الميجر على تشريط ملف الجهد العالي، وتوصيل الكابل السالب لجهاز الميجر على تشريط ملف الجهد المنخفض.",
     ] + STEP_TAIL},
    {"n": 2, "label": "LV -------- HV + TER + E",
     "steps": [
         "نقوم بتوصيل التشريط على ملف الجهد العالي مع التشريط على ملف التيرشري مع الأرضي.",
         "نقوم بتوصيل الكابل الموجب لجهاز الميجر على تشريط ملف الجهد المنخفض، وتوصيل الكابل السالب لجهاز الميجر على ملف الجهد العالي والتيرشري.",
     ] + STEP_TAIL},
    {"n": 3, "label": "TER -------- HV + LV + E",
     "steps": [
         "نقوم بتوصيل التشريط على ملف الجهد العالي مع التشريط على ملف الجهد المنخفض مع الأرضي.",
         "نقوم بتوصيل الكابل الموجب لجهاز الميجر على تشريط الملف التيرشري، وتوصيل الكابل السالب لجهاز الميجر على نقطة أرضي المحول.",
     ] + STEP_TAIL},
    {"n": 4, "label": "HV -------- LV",
     "steps": [
         "نقوم برفع أي تأريض.",
         "نقوم بتوصيل الكابل الموجب لجهاز الميجر على تشريط ملف الجهد العالي، وتوصيل الكابل السالب لجهاز الميجر على تشريط ملف الجهد المنخفض.",
     ] + STEP_TAIL},
    {"n": 5, "label": "HV + LV + TER ------------ E",
     "steps": [
         "نقوم بتوصيل التشريط على ملف الجهد العالي مع التشريط على ملف الجهد المنخفض وملف التيرشري.",
         "نقوم بتوصيل الكابل الموجب لجهاز الميجر على تشريط الثلاثة ملفات، وتوصيل الكابل السالب لجهاز الميجر على أرضي المحول.",
     ] + STEP_TAIL},
]

REPORT_ROWS = [
    ["HV to (LV+T+E)", "", "", ""],
    ["LV to (HV+T+E)", "", "", ""],
    ["T to (H+L+E)", "", "", ""],
    ["LV to HV", "", "", ""],
    ["(HV+LV+T) to E", "", "", ""],
]

sections = [
    {"type": "heading", "level": 1, "text": "اختبار العزل بالميجر 5000 فولت لمحول ثنائي الملفات + ملف ثالثي (TER)"},
    {"type": "paragraph", "text": "المعدة: محولات قدرة ثنائية الملفات + ملف ثالثي — رقم المستند: T-024-r0 — إجراء فني: اختبار بالميجر 5000 فولت."},
    {"type": "heading", "level": 2, "text": "مقدمة"},
    {"type": "paragraph", "text": INTRO_AR},
    {"type": "heading", "level": 2, "text": "احتياطات الأمان"},
    {"type": "list", "items": SAFETY_AR},
    {"type": "heading", "level": 2, "text": "طريقة الاختبار"},
    {"type": "paragraph", "text": METHOD_AR},
]
for t in TESTS_AR:
    sections.append({"type": "heading", "level": 3, "text": f"الاختبار {t['n']}: {t['label']}"})
    sections.append({"type": "list", "items": t["steps"]})
sections.append({"type": "heading", "level": 2, "text": "نموذج تقرير الاختبار — اختبار مقاومة العزل بالميجر 5000 فولت"})
sections.append({"type": "table", "rows": [
    ["الاختبار", "المقاومة بعد 15 ثانية", "المقاومة بعد 60 ثانية", "R60/R15"],
] + REPORT_ROWS, "truncated_rows": 0})
sections.append({"type": "paragraph", "text": "الموقع: ______    كود المعدة: ______    تم الفحص بواسطة: ______    التاريخ: ______    التوقيع: ______"})

text = "\n".join(
    s.get("text", "") if s["type"] != "list" else "\n".join(s["items"])
    if s["type"] != "table" else "\n".join(" | ".join(r) for r in s["rows"])
    for s in sections)

doc = {
    "id": DOC_ID,
    "doc_number": "T-024-R0-TER",
    "title_en": "Two Winding + TER Transformers Test — Megger 5000 V",
    "title_ar": "اختبار العزل بالميجر 5000 فولت لمحول ثنائي الملفات + ملف ثالثي (TER)",
    "category": "transformers",
    "source_path": "arabic_web/Ar_appr_docs/Ar_ad_subst/ad_ss_docs/new_translated/T-024-r0a-ter.htm",
    "source_type": "html",
    "source_encoding": "utf-8",
    "language": "ar",
    "languages_available": ["en", "ar"],
    "translation_status": "available",
    "translation_note": (
        "Arabic translation created in MPIS v2 from the English original "
        "appr_docs/ad_subst/ad_sub_tp/T-024-r0-ter.pdf. No Arabic version of "
        "this document existed anywhere in the v1 repository (the other five "
        "test procedures already had Arabic HTML versions in new_translated/). "
        "Terminology follows the existing T-024-r0a Arabic version."
    ),
    "translated_from": "appr_docs/ad_subst/ad_sub_tp/T-024-r0-ter.pdf",
    "sections": sections,
    "text": text,
    "text_truncated": False,
    "links": [],
    "images": [],
}

if __name__ == "__main__":
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print("wrote", OUT)
