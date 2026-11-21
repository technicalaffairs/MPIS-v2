# -*- coding: utf-8 -*-
"""Runner: translate distribution slice 1 and write .translation.json files."""
import json, re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import norm, norm_ar, translate_ar, translate_en, EN_TITLES, AR_EN_NORM

BASE = '/home/hatch/workspace/mpis-v2'
OUT = os.path.join(BASE, 'tools/translation41')
IDS = open(os.path.join(BASE, 'translation_slices/distribution_slice1.txt')).read().split()

UNCERTAIN = {
"distr-trans-all-docs-t-101-r1a-htm": [
 {"term": "item numbering 1,2,3,4,6,7,8", "note": "Source inspection table skips item 5; numbering reproduced verbatim."},
 {"term": "000الخ / إلخ", "note": "Source OCR artifact '000' before 'الخ' rendered as 'etc.' by intent."},
],
"distr-trans-all-docs-tk-001-r1a-htm": [
 {"term": "000الخ", "note": "Source OCR artifact for 'إلخ' (etc.); rendered as 'etc.' by intent."},
 {"term": "سكاكه ، روزة ، ترباس بقفل ، كالون", "note": "Locking means rendered by intent as hasp, rose, bolt with padlock, lock."},
 {"term": "بلاور", "note": "Loanword for blower; kept as 'blower'."},
],
"distr-trans-all-docs-tk-001-r2a-htm": [
 {"term": "000الخ", "note": "Source OCR artifact for 'إلخ' (etc.); rendered as 'etc.' by intent."},
 {"term": "بالراجع عليها", "note": "Back-fed voltage on the components; rendered as 'back-fed voltage' by intent."},
],
"distr-trans-all-docs-tk-002-r0a-htm": [
 {"term": "احالة", "note": "Column header rendered as 'Referral' by intent (disposition/referral column)."},
],
"distr-trans-all-docs-tk-002-r1a-htm": [
 {"term": "doc_number TK-002-R0A", "note": "Source doc_number is TK-002-R0A although the file/revision is TK-002-r1a; reproduced verbatim, not corrected."},
 {"term": "احالة", "note": "Column header rendered as 'Referral' by intent."},
],
"distr-trans-all-docs-tk-002-r2a-htm": [
 {"term": "احالة", "note": "Column header rendered as 'Referral' by intent."},
],
"distr-trans-all-docs-tk-003-r0a-htm": [
 {"term": "000الخ", "note": "Source OCR artifact for 'إلخ' (etc.); rendered as 'etc.' by intent."},
 {"term": "مجموعة أراضى محلية", "note": "Rendered as 'set of local earths' by intent."},
],
"distr-trans-all-docs-tk-003-r1a-htm": [
 {"term": "doc_number / header TK-003-r0a", "note": "Header table inside the document says TK-003-r0a although the file/revision is TK-003-r1a; reproduced verbatim, not corrected."},
 {"term": "000الخ", "note": "Source OCR artifact for 'إلخ' (etc.); rendered as 'etc.' by intent."},
],
"distr-trans-all-docs-tk-004-r0a-htm": [
 {"term": "احالة", "note": "Column header rendered as 'Referral' by intent."},
],
"distr-trans-all-docs-tl-043-r0a-htm": [
 {"term": "Conductivity not less than 400 s", "note": "Source value is garbled (resistivity >=1300 ohm/cm contradicts conductivity 'not less than 400 s'); reproduced verbatim, not corrected."},
 {"term": "الطائرة الأولى / الطائرة الثانية", "note": "Source uses 'الطائرة' for a tower cross-arm level; rendered as 'level' by intent."},
 {"term": "الدئرتين", "note": "Source typo for 'الدائرتين' (the two circuits); rendered as 'both circuits' by intent."},
 {"term": "بشبورى", "note": "Washing nozzle; rendered as 'nozzle'."},
 {"term": "لواكير التجميع", "note": "Hose assembly couplings; rendered as 'assembly couplings' by intent."},
 {"term": "الكربراتير ، الاسبراتير", "note": "Carburettor and distributor of the pump engine; rendered in English by intent."},
 {"term": "trailing '0' in pump-engine step", "note": "Source ends the pump-engine check with a stray '0' (OCR artifact); reproduced verbatim."},
 {"term": "شداد", "note": "Tension member of the tower; rendered as 'tension member' by intent."},
 {"term": "سلنجة", "note": "Sling used to fix the hose; rendered as 'sling'."},
],
"distr-trans-all-docs-tl-048-r0a-htm": [
 {"term": "الترخيم", "note": "Conductor sag; rendered as 'sag'."},
 {"term": "الارضي المتكرر", "note": "Repeated earthing of the poles; rendered as 'repeated earthing'."},
],
"distr-trans-all-docs-td-pc-003-r0-htm": [
 {"term": "V DC", "note": "Rendered as 'فولت تيار مستمر' (volts DC)."},
],
"distr-trans-cairo-zone-page-html": [],
"distr-trans-delta-zone-page-html": [
 {"term": "Helioples", "note": "Source place-name spelling reproduced as transliterated (مصر الجديدة) by intent; source spelling is a typo for Heliopolis."},
 {"term": "Qaluob / Qalubia", "note": "Source variant spellings of Qalyubia; transliterated consistently."},
],
"distr-trans-ds-es-cai-zone-htm": [
 {"term": "Helioples", "note": "Source typo for Heliopolis; transliterated as مصر الجديدة by intent."},
 {"term": "MITSUBISH", "note": "Source typo for Mitsubishi; kept as manufacturer name, not corrected."},
 {"term": "Bani Swief Wast", "note": "Source typo for West; rendered as بني سويف غرب by intent."},
 {"term": "PFAST Acting Earthing Switch", "note": "Source typo 'PFAST' for 'Fast'; rendered as سكينة تأريض سريعة الفعل by intent."},
 {"term": "Esmant / Masria Esmant / Esmnt Suez", "note": "Place names left in Latin script; Arabic form not established from the source."},
 {"term": "Mansogat / El-Mansougate", "note": "Place names left in Latin script; Arabic form not established from the source."},
 {"term": "Eroq Solb / Solb Makhsous", "note": "Place names left in Latin script; Arabic form not established from the source."},
],
"distr-trans-index-htm": [],
"distr-trans-middle-egypt-zone-page-html": [
 {"term": "title 'Cairo Zone_Page'", "note": "Source title says Cairo Zone but the page body is the Middle Egypt Zone; title translated verbatim, not corrected."},
 {"term": "Asuit / Assuit", "note": "Source variant spellings of Assiut; transliterated consistently as أسيوط."},
 {"term": "Air Blust", "note": "Source typo for 'Air Blast'; rendered as هوائي by intent."},
],
"distr-trans-prot-cai-zone-htm": [
 {"term": "Also all u can open XP excel file (PC work sheet)", "note": "Source heading is garbled English; rendered by intent as 'كما يمكنكم فتح ملف إكسيل XP (ورقة عمل الوقاية)'."},
 {"term": "Earth Faultfor Busbar Relay", "note": "Source missing space ('Faultfor'); rendered as ريلاي عطل أرضي للقضبان by intent."},
 {"term": "Buchloz Relay", "note": "Source spelling 'Buchloz' for Buchholz relay; transliterated as بوخولز by intent."},
 {"term": "Police Acadym", "note": "Source typo for Academy; rendered as أكاديمية الشرطة by intent."},
 {"term": "Severker", "note": "Source spelling of the test-set name; kept in Latin, not corrected."},
],
"distr-trans-prot-canal-zone-htm": [
 {"term": "Masria Esmant / Esmant Suez", "note": "Place names left in Latin script; Arabic form not established from the source."},
],
"distr-trans-prot-delta-zone-htm": [],
"distr-trans-ss-canal-zone-htm": [
 {"term": "Eroq Solb / Solb Makhsous", "note": "Place names left in Latin script; Arabic form not established from the source."},
 {"term": "Esmnt Suez", "note": "Place name left in Latin script; Arabic form not established from the source."},
 {"term": "Al Manaief SS", "note": "Transliterated phonetically as محطة المنايف; spelling not verified against an official list."},
],
"distr-trans-ss-delta-zone-htm": [
 {"term": "Qaliub / Qaluob", "note": "Source variant spellings of Qalyub; transliterated consistently as قليوب."},
 {"term": "Sandoub / Sandob", "note": "Source variant spellings; transliterated consistently as صندوب."},
],
"distr-trans-ss-megypt-htm": [
 {"term": "Asuit / Assuit", "note": "Source variant spellings of Assiut; transliterated consistently as أسيوط."},
 {"term": "Air Blust", "note": "Source typo for 'Air Blast'; rendered as هوائي by intent."},
 {"term": "SPERCHER & SCHUH", "note": "Source typo for Sprecher & Schuh; kept in Latin, not corrected."},
 {"term": "Demo", "note": "Location given as 'Demo' in the source; rendered as تجريبي by intent."},
],
"distr-trans-ss-uegypt-htm": [
 {"term": "Enrginovest / Energonvest", "note": "Source typos for Energoinvest; kept in Latin, not corrected."},
],
"distr-trans-subs-ecet-page-htm": [
 {"term": "truncated_rows: 17 in one source table", "note": "Source JSON flags 17 truncated rows in a switchgear table; the source text field renders identically from the sections present, so nothing additional was available to translate."},
 {"term": "Basbar", "note": "Source typo for Busbar; rendered as قضبان by intent."},
 {"term": "Blust", "note": "Source typo for Blast; rendered as هوائي by intent."},
 {"term": "Enrginovest / Energonvest", "note": "Source typos for Energoinvest; kept in Latin, not corrected."},
 {"term": "Sabtiaa", "note": "Source typo for Sabtia; transliterated as السبتية by intent."},
 {"term": "Demo", "note": "Location given as 'Demo' in the source; rendered as تجريبي by intent."},
 {"term": "EroqSolb", "note": "Place name left in Latin script; Arabic form not established from the source."},
 {"term": "Mansogat", "note": "Place name left in Latin script; Arabic form not established from the source."},
 {"term": "El Atamia", "note": "Transliterated phonetically as العتامية; spelling not verified against an official list."},
],
"distr-trans-transm-co-page-html": [],
"distr-trans-upper-egypt-zone-page-html": [
 {"term": "title 'Cairo Zone_Page'", "note": "Source title says Cairo Zone but the page body is the Upper Egypt Zone; title translated verbatim, not corrected."},
],
"distr-trans-west-delta-zone-page-html": [],
"gen-docs-app-gen-edepc-distribution-boards-des-008-r0-htm": [
 {"term": "Ayoun Moussa PS", "note": "Rendered as محطة عيون موسى by intent."},
 {"term": "EDEPC", "note": "East Delta Electricity Production Company; rendered by its Arabic name in the certification line."},
],
"gen-docs-app-gen-hyd-ep-all-docs-distribution-boards-des-009-r0-htm": [
 {"term": "will trained", "note": "Source typo for 'well trained'; rendered as مدربين جيدًا by intent."},
 {"term": "manufactures manual", "note": "Source typo for 'manufacturer's manual'; rendered as دليل الشركة الصانعة by intent."},
 {"term": "input and and output voltage", "note": "Source double 'and'; rendered once by intent."},
 {"term": "Make a clean and used spray with oil", "note": "Source wording is garbled; rendered by intent as clean the fan and use an oil spray to lubricate it."},
 {"term": "HPGC", "note": "Hydro Power Generation Company; rendered by its Arabic name in the certification line."},
],
"gen-docs-app-gen-hyd-ep-all-docs-distribution-boards-des-010-r0-htm": [
 {"term": "Vaccum cleaner", "note": "Source typo for 'Vacuum cleaner'; rendered as مكنسة كهربائية by intent."},
 {"term": "led\"s", "note": "Source typo for LED's; rendered as لمبات LED by intent."},
 {"term": "Make a clean and used spray with oil", "note": "Source wording is garbled; rendered by intent as clean the fan and use an oil spray to lubricate it."},
 {"term": "HPGC", "note": "Hydro Power Generation Company; rendered by its Arabic name in the certification line."},
],
}

def body_lang(text):
    ar = len(re.findall(r'[\u0600-\u06FF]', text))
    lat = len(re.findall(r'[A-Za-z]', text))
    return ('ar' if ar > lat else 'en'), ar, lat

def translate_value(v, fn):
    """Translate a string cell; returns (translated, issues list)."""
    if v is None:
        return v, []
    out, extra = fn(v)
    issues = []
    if isinstance(extra, bool) and extra:
        issues.append(('leftover-ar', v))
    elif isinstance(extra, list) and extra:
        issues.append(('leftover-latin', v, extra))
    return out, issues

def translate_section(sec, fn):
    s = dict(sec)
    issues = []
    if sec['type'] == 'table':
        rows = []
        for r in sec['rows']:
            nr = []
            for c in r:
                t, iss = translate_value(c, fn)
                nr.append(t)
                issues += iss
            rows.append(nr)
        s['rows'] = rows
    elif sec['type'] == 'list':
        items = []
        for it in sec['items']:
            t, iss = translate_value(it, fn)
            items.append(t)
            issues += iss
        s['items'] = items
    else:
        t, iss = translate_value(sec.get('text', ''), fn)
        s['text'] = t
        issues += iss
    return s, issues

def render(sections):
    out = []
    for s in sections:
        if s['type'] == 'table':
            for r in s['rows']:
                out.append(' | '.join(r))
        elif s['type'] == 'list':
            out.extend(s['items'])
        else:
            out.append(s.get('text', ''))
    return '\n'.join(out)

def main():
    total_words = 0
    written = []
    problems = []
    mislabeled = []
    for doc_id in IDS:
        src = json.load(open(os.path.join(BASE, 'content', doc_id + '.json')))
        text = src.get('text', '') or ''
        blang, ar_n, lat_n = body_lang(text)
        manifest = src.get('language')
        if blang != manifest:
            mislabeled.append((doc_id, manifest, blang))
        if blang == 'ar':
            src_lang, tgt_lang, fn = 'ar', 'en', translate_ar
            title_src = src.get('title_ar') or ''
            title_tgt = norm_ar(title_src).replace('معتمد', 'APPROVED').strip()
        else:
            src_lang, tgt_lang, fn = 'en', 'ar', translate_en
            title_src = src.get('title_en') or ''
            t = norm(title_src)
            title_tgt = EN_TITLES.get(t, t.replace('APPROVED', 'معتمد').strip())
        secs_t, issues = [], []
        for s in src.get('sections', []):
            st, iss = translate_section(s, fn)
            secs_t.append(st)
            issues += iss
        # text_target: rebuilt from translated sections (verified: source text
        # is exactly the rendering of source sections for all 31 docs)
        text_t = render(secs_t)
        wc = len(text.split())
        total_words += wc
        out = {
            'id': doc_id,
            'doc_number': src.get('doc_number'),
            'category': 'distribution',
            'source_language': src_lang,
            'target_language': tgt_lang,
            'title_target': title_tgt,
            'sections_target': secs_t,
            'text_target': text_t,
            'word_count_source': wc,
            'uncertain_terms': UNCERTAIN.get(doc_id, []),
        }
        with open(os.path.join(OUT, doc_id + '.translation.json'), 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        written.append(doc_id)
        if issues:
            problems.append((doc_id, issues))
    print('written:', len(written), 'total source words:', total_words)
    print('mislabeled:', mislabeled)
    for doc_id, issues in problems:
        print('---', doc_id, len(issues), 'issues')
        for iss in issues[:25]:
            print('   ', iss)
    json.dump({'written': written, 'total_words': total_words, 'mislabeled': mislabeled},
              open('/tmp/slice1_report.json', 'w'), ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
