"""Fills the K! Hacks 4.0 online-submission template with Team Proxy's E-Healthcare content."""
import copy
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree

SRC = r"C:\Users\yoges\Downloads\Khacks_4.0_ppt.pptx"
OUTS = [
    r"c:\Users\yoges\Downloads\e-healthcare\Khacks_4.0_Proxy_Submission.pptx",
    r"C:\Users\yoges\Downloads\Khacks_4.0_Proxy_Submission.pptx",
]

FONT = "Calibri"
LIME = RGBColor(214, 250, 62)
TEAL = RGBColor(56, 210, 235)
WHITE = RGBColor(255, 255, 255)
LIGHT = RGBColor(214, 222, 235)
DIM = RGBColor(160, 174, 196)
CARD = RGBColor(12, 20, 42)
HEAD = RGBColor(24, 58, 92)

prs = pptx.Presentation(SRC)


# ---------------------------------------------------------------- helpers
def drop_placeholder(slide):
    for sh in list(slide.shapes):
        if sh.has_text_frame and sh.text.strip().lower() == "type here":
            sh._element.getparent().remove(sh._element)


def set_alpha(shape, pct):
    sf = shape.fill._xPr.find(qn("a:solidFill"))
    clr = sf[0]
    a = etree.SubElement(clr, qn("a:alpha"))
    a.set("val", str(int(pct * 1000)))


def R(text, size=12, bold=False, color=LIGHT, italic=False):
    return (text, size, bold, color, italic)


def card(slide, x, y, w, h, paras, fill=CARD, alpha=82, line=TEAL, line_w=0.75,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, anchor=MSO_ANCHOR.TOP, margin=0.16, radius=0.04):
    sh = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        sh.adjustments[0] = radius
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
        if alpha < 100:
            set_alpha(sh, alpha)
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(line_w)
    tf = sh.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = Inches(margin * 0.75)
    write(tf, paras)
    return sh


def write(tf, paras):
    """paras: list of (runs, align, space_before_pt)"""
    first = True
    for item in paras:
        item = tuple(item)
        defaults = (None, PP_ALIGN.LEFT, 0)
        runs, align, sb = item + defaults[len(item):]
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.space_before = Pt(sb)
        for text, size, bold, color, italic in runs:
            r = p.add_run()
            r.text = text
            r.font.name = FONT
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.italic = italic
            r.font.color.rgb = color


def textbox(slide, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    write(tf, paras)
    return tb


def subtitle(slide, text, y=1.12, w=8.45):
    textbox(slide, 0.25, y, w, 0.62, [([R(text, 14.5, False, WHITE, True)],)])


def bullet(text_bold, text, size=12, sb=5, mark_color=TEAL):
    runs = [R("▪  ", size, True, mark_color)]
    if text_bold:
        runs.append(R(text_bold, size, True, WHITE))
    runs.append(R(text, size, False, LIGHT))
    return (runs, PP_ALIGN.LEFT, sb)


def arrow(slide, x, y, w=0.32, h=0.34):
    a = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    a.shadow.inherit = False
    a.fill.solid()
    a.fill.fore_color.rgb = TEAL
    a.line.fill.background()


# ================================================================ SLIDE 1
s = prs.slides[0]
for sh in s.shapes:
    if sh.has_text_frame and "Team Name" in sh.text:
        values = ["Proxy", "New Horizon College of Engineering", "Health Tech"]
        paras = sh.text_frame.paragraphs
        for p, val in zip(paras, values):
            for r in p.runs:
                if "Type Here" in r.text:
                    r.text = r.text.replace("Type Here", val)
        # extra line: project title, cloned from the last line so it keeps template formatting
        new_p = copy.deepcopy(paras[-1]._p)
        sh.text_frame._txBody.append(new_p)
        last = sh.text_frame.paragraphs[-1]
        runs = last.runs
        full = "".join(r.text for r in runs)
        # rebuild text in the cloned runs
        for r in runs[1:]:
            r._r.getparent().remove(r._r)
        runs[0].text = "Project Title   :    E-Healthcare"
        sh.height = Inches(1.95)

textbox(s, 1.58, 5.25, 10.3, 0.5, [([R("Instant, privacy-safe access to a patient's critical medical information in an emergency",
                                       16, False, LIME, True)],)])

# ================================================================ SLIDE 2 - PROBLEM
s = prs.slides[1]
drop_placeholder(s)
subtitle(s, "When a person is brought in after an accident or a sudden collapse, the information that decides "
            "their treatment is missing at the exact moment it is needed.")

card(s, 0.45, 1.85, 12.43, 0.6, [([
    R("Scale:  ", 13, True, LIME),
    R("4,61,312 road accidents and 1,68,491 deaths in India in 2022 (MoRTH). Many victims reach hospital "
      "unconscious, alone and with no medical history.", 13, False, WHITE)],)],
     line=None, fill=HEAD, alpha=85, anchor=MSO_ANCHOR.MIDDLE)

cols = [
    ("01", "The patient cannot speak",
     ["Unconscious or in shock, the patient cannot tell anyone their blood group, drug allergies, "
      "current medicines or conditions such as diabetes, epilepsy or heart disease.",
      "Bystanders do not know whom to call."]),
    ("02", "The information is locked away",
     ["Details sit in a locked phone, in paper files at another hospital, or in apps that need the "
      "patient's own OTP, password or access code.",
      "Consent-first systems assume a conscious, cooperating patient."]),
    ("03", "The hospital cannot wait",
     ["Doctors begin treatment without history: a wrong drug can trigger a severe allergic reaction, "
      "and unknown blood thinners raise bleeding risk in surgery.",
      "Later, details are lost again during shift handovers."]),
]
cw, gap, cy, ch = 3.977, 0.25, 2.6, 2.7
for i, (num, title, body) in enumerate(cols):
    paras = [([R(num + "  ", 22, True, LIME), R(title, 15, True, WHITE)],)]
    for b in body:
        paras.append(bullet(None, b, 13, 8))
    card(s, 0.45 + i * (cw + gap), cy, cw, ch, paras)

card(s, 0.45, 5.45, 12.43, 0.68, [([
    R("Problem:  ", 13.5, True, LIME),
    R("There is no fast and privacy-safe way for responders and doctors to see a patient's critical medical "
      "information in an emergency, or to keep it intact through the hospital stay.", 13.5, False, WHITE)],)],
     line=LIME, anchor=MSO_ANCHOR.MIDDLE)

# ================================================================ SLIDE 3 - SOLUTION
s = prs.slides[2]
drop_placeholder(s)
subtitle(s, "E-Healthcare is a web platform that puts a patient's critical medical information in front of the "
            "right person within seconds, showing each person only what they need.")

users = [
    ("BYSTANDER", "Scans the QR sticker on the patient's phone or ID card. No app, no login.",
     [("Sees only ", "name, blood group and emergency contacts."),
      ("One tap ", "sends the live GPS location to family by SMS."),
      ("No medical history ", "is ever shown at this level.")]),
    ("PARAMEDIC / ER DOCTOR", "Verified clinician login. Searches by patient name, phone or ID. No codes or OTPs.",
     [("Sees ", "allergies, active medicines, conditions, latest vitals, past consultations, prescriptions and reports."),
      ("Every emergency access ", "is logged with clinician, time and reason.")]),
    ("PATIENT & FAMILY", "Personal login for the patient and linked family members.",
     [("Symptom check ", "by voice or text in English, Tamil, Telugu, Kannada, Malayalam and Hindi."),
      ("Lab report upload ", "with out-of-range values flagged."),
      ("Medicine reminders ", "and control over which records are shared.")]),
]
cw, cy, ch = 3.977, 1.88, 3.22
for i, (who, access, pts) in enumerate(users):
    paras = [([R(who, 14, True, LIME)],),
             ([R(access, 11.5, False, TEAL, True)], PP_ALIGN.LEFT, 4)]
    for b, t in pts:
        paras.append(bullet(b, t, 13, 8))
    card(s, 0.45 + i * (cw + 0.25), cy, cw, ch, paras)

card(s, 0.45, 5.23, 12.43, 0.9, [
    ([R("After admission:  ", 13, True, LIME),
      R("Consultations are recorded as structured SBAR handover notes (Situation, Background, Assessment, "
        "Recommendation), and wearable vitals are graded automatically, raising warning and critical alerts "
        "on the doctor's dashboard.", 12.5, False, WHITE)],)],
     line=LIME, anchor=MSO_ANCHOR.MIDDLE)

# ================================================================ SLIDE 4 - ARCHITECTURE
s = prs.slides[3]
drop_placeholder(s)
subtitle(s, "Three-tier web architecture with role-based access: every request is checked against who is asking before any data is returned.", y=1.66, w=12.4)

top = 2.08          # column labels
bt, bh = 2.38, 2.6  # boxes top / height
mid = bt + bh / 2 - 0.17
textbox(s, 0.45, top, 2.0, 0.3, [([R("USERS", 11, True, DIM)],)])
for j, u in enumerate(["Bystander (QR scan)", "Patient / Family", "Paramedic / Doctor"]):
    card(s, 0.45, bt + j * 0.91, 2.0, 0.78, [([R(u, 12.5, True, WHITE)], PP_ALIGN.CENTER)],
         anchor=MSO_ANCHOR.MIDDLE)
arrow(s, 2.53, mid)

textbox(s, 2.93, top, 2.3, 0.3, [([R("CLIENT", 11, True, DIM)],)])
card(s, 2.93, bt, 2.3, bh, [
    ([R("Web Client", 14, True, LIME)],),
    bullet(None, "HTML5, Bootstrap 5, JavaScript", 11.5, 5),
    bullet(None, "Patient, doctor and emergency portals", 11.5, 4),
    bullet(None, "Web Speech API: voice input in 6 languages", 11.5, 4),
    bullet(None, "Chart.js vitals graphs", 11.5, 4),
])
arrow(s, 5.31, mid)

textbox(s, 5.71, top, 4.75, 0.3, [([R("APPLICATION SERVER", 11, True, DIM)],)])
card(s, 5.71, bt, 4.75, bh, [
    ([R("FastAPI (Python)  ", 14, True, LIME), R("REST APIs, JWT role-based access", 11.5, False, TEAL)],)])
mods = ["Emergency passport & QR", "Patient record search", "Break-glass audit log", "Symptom triage model",
        "Lab report parser", "SBAR handover engine", "Vitals grading & alerts", "Reminder scheduler"]
mw, mh = 2.19, 0.44
for k, m in enumerate(mods):
    cx = 5.85 + (k % 2) * (mw + 0.1)
    cyy = bt + 0.5 + (k // 2) * (mh + 0.08)
    card(s, cx, cyy, mw, mh, [([R(m, 11.5, False, WHITE)], PP_ALIGN.CENTER)], fill=HEAD, alpha=90,
         line=None, anchor=MSO_ANCHOR.MIDDLE, margin=0.06)
arrow(s, 10.54, mid)

textbox(s, 10.94, top, 1.95, 0.3, [([R("DATA & SERVICES", 11, True, DIM)],)])
card(s, 10.94, bt, 1.94, 1.24, [
    ([R("Database", 13, True, LIME)],),
    ([R("PostgreSQL / SQLite via SQLAlchemy ORM", 11, False, LIGHT)], PP_ALIGN.LEFT, 3)])
card(s, 10.94, bt + 1.36, 1.94, 1.24, [
    ([R("External", 13, True, LIME)],),
    ([R("SMS gateway, map location links, wearable vitals feed", 11, False, LIGHT)], PP_ALIGN.LEFT, 3)])

textbox(s, 0.45, 5.08, 3.0, 0.3, [([R("EMERGENCY ACCESS FLOW", 11, True, DIM)],)])
steps = ["Scan QR / search name", "Verify role", "Return tiered view", "Write audit entry", "Alert family by SMS"]
sw = 12.43 / 5
for k, st in enumerate(steps):
    shp = MSO_SHAPE.PENTAGON if k == 0 else MSO_SHAPE.CHEVRON
    card(s, 0.45 + k * sw, 5.4, sw + 0.05, 0.6, [([R(st, 12, True, WHITE if k % 2 == 0 else CARD)], PP_ALIGN.CENTER)],
         shape=shp, fill=HEAD if k % 2 == 0 else TEAL, alpha=100, line=None, anchor=MSO_ANCHOR.MIDDLE, margin=0.25)

# ================================================================ SLIDE 5 - FEASIBILITY & USP
s = prs.slides[4]
drop_placeholder(s)
subtitle(s, "A working prototype on an open-source stack, built around the cases existing health apps do "
            "not handle.", y=1.66, w=12.4)

card(s, 0.45, 2.1, 4.85, 4.03, [
    ([R("FEASIBILITY", 14, True, LIME)],),
    bullet("Prototype built: ", "patient, doctor and emergency portals with live APIs and a test suite.", 12, 8),
    bullet("Low cost: ", "open-source tools; runs on one laptop or a small cloud server. No special hardware.", 12, 7),
    bullet("Any device: ", "works in a phone browser; the QR view needs no installation.", 12, 7),
    bullet("Interoperable: ", "records map to FHIR resources (Patient, AllergyIntolerance, MedicationStatement, "
                              "Observation) for ABDM integration.", 12, 7),
    bullet("Legally grounded: ", "the DPDP Act 2023 (Sec. 7) allows processing personal data in a medical "
                                 "emergency; the audit log keeps every access accountable.", 12, 7),
])

rows = [
    ("", "Typical health apps / EHRs", "E-Healthcare"),
    ("Patient unconscious", "Needs the patient's OTP or password", "QR scan, or clinician searches by name"),
    ("Privacy", "All records or nothing", "Three views: bystander, clinician, patient"),
    ("Accountability", "Access rarely tracked", "Every emergency access logged with reason"),
    ("Language", "Mostly English", "Voice and text in 6 Indian languages"),
    ("After admission", "Free-text notes", "SBAR handovers and live vitals alerts"),
]
tx, ty, tw = 5.5, 2.1, 7.38
tbl_shape = s.shapes.add_table(len(rows), 3, Inches(tx), Inches(ty), Inches(tw), Inches(4.03))
tbl = tbl_shape.table
tbl.first_row = True
for ci, wdt in enumerate([1.85, 2.6, 2.93]):
    tbl.columns[ci].width = Inches(wdt)
for ri, row in enumerate(rows):
    tbl.rows[ri].height = Inches(0.53 if ri == 0 else 0.7)
    for ci, val in enumerate(row):
        cell = tbl.cell(ri, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = HEAD if ri == 0 else (CARD if ri % 2 else RGBColor(20, 32, 60))
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = cell.margin_right = Inches(0.1)
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = ""
        r = p.add_run()
        r.text = val
        r.font.name = FONT
        if ri == 0:
            r.font.size, r.font.bold = Pt(13), True
            r.font.color.rgb = LIME if ci == 2 else WHITE
        else:
            r.font.size = Pt(12)
            r.font.bold = ci != 1
            r.font.color.rgb = TEAL if ci == 0 else (DIM if ci == 1 else WHITE)

# ================================================================ SLIDE 6 - MARKET & BUSINESS
s = prs.slides[5]
drop_placeholder(s)
subtitle(s, "Free for citizens, paid for by the institutions that save time and lives with it.", y=1.66, w=12.4)

cw, cy, ch = 3.977, 2.1, 2.42
market = [
    ("WHO NEEDS IT", [
        ("Accident and emergency patients: ", "4.6 lakh road accidents a year."),
        ("Hospital emergency departments ", "treating unknown patients."),
        ("Ambulance services ", "(108 and private fleets)."),
        ("Elderly and chronic patients ", "living alone, and their families."),
    ]),
    ("REVENUE MODEL", [
        ("Citizens: ", "free emergency profile and QR."),
        ("Hospitals: ", "yearly subscription for the clinician console, SBAR and vitals dashboard."),
        ("Ambulance operators: ", "licence for the paramedic view."),
        ("Colleges, employers, insurers: ", "bulk QR health IDs; premium family plan."),
    ]),
    ("GO-TO-MARKET", [
        ("Step 1: ", "QR health IDs for students at our own campus."),
        ("Step 2: ", "pilot with one partner hospital's emergency department."),
        ("Step 3: ", "tie-up with a private ambulance operator."),
        ("Step 4: ", "ABDM sandbox integration, then scale city by city."),
    ]),
]
for i, (head, pts) in enumerate(market):
    paras = [([R(head, 14, True, LIME)],)]
    for b, t in pts:
        paras.append(bullet(b, t, 12, 6))
    card(s, 0.45 + i * (cw + 0.25), cy, cw, ch, paras)

alts = [
    ("PHR / ABHA apps", "Consent-first; need the patient to log in or approve. No emergency mode."),
    ("Hospital information systems", "Data stays inside one hospital; nothing available on arrival elsewhere."),
    ("Medical ID cards and bracelets", "Static, rarely updated, no clinician detail and no family alert."),
]
card(s, 0.45, 4.63, 12.43, 1.5, [([R("EXISTING ALTERNATIVES AND THE GAP WE FILL", 13, True, LIME)],)], line=LIME)
aw = 12.1 / 3
for i, (a, gapt) in enumerate(alts):
    textbox(s, 0.62 + i * aw, 5.05, aw - 0.15, 1.0, [
        ([R(a, 12.5, True, WHITE)],),
        ([R(gapt, 11.5, False, LIGHT)], PP_ALIGN.LEFT, 3)])

# ================================================================ SLIDE 7 - RESEARCH & REFERENCES
s = prs.slides[6]
drop_placeholder(s)
subtitle(s, "Our design choices are based on published data, Indian law and open healthcare standards.")

left = [
    ("Ministry of Road Transport & Highways, ", "Road Accidents in India 2022, Transport Research Wing, Govt. of India.",
     "Scale of the problem"),
    ("Supreme Court of India, ", "Parmanand Katara v. Union of India (1989).",
     "Duty to give immediate medical aid to accident victims"),
    ("Digital Personal Data Protection Act, 2023, ", "Section 7 (legitimate uses).",
     "Legal basis for emergency access without prior consent"),
    ("WHO Collaborating Centre for Patient Safety, ", "Communication During Patient Hand-Overs, Patient Safety Solutions, Vol. 1, Sol. 3 (2007).",
     "Structured handover (SBAR)"),
]
right = [
    ("Starmer A.J. et al., ", "Changes in Medical Errors after Implementation of a Handoff Program, N Engl J Med 2014; 371:1803-1812.",
     "Structured handoffs cut medical errors by 23%"),
    ("National Health Authority, ", "Ayushman Bharat Digital Mission: ABHA, Health Information Exchange & Consent Manager (abdm.gov.in).",
     "National integration path"),
    ("HL7 International, ", "FHIR Release 4 (v4.0.1), hl7.org/fhir/R4.",
     "Data model for interoperability"),
    ("US HHS, HIPAA Security Rule, ", "45 CFR 164.312(a)(2)(ii), Emergency Access Procedure.",
     "Break-glass access with audit"),
]


def refs_card(x, items, start):
    paras = []
    for n, (who, what, used) in enumerate(items, start):
        paras.append(([R(f"[{n}]  ", 12.5, True, LIME), R(who, 12.5, True, WHITE), R(what, 12.5, False, LIGHT)],
                      PP_ALIGN.LEFT, 0 if n == start else 11))
        paras.append(([R("Used for: " + used, 11.5, False, TEAL, True)], PP_ALIGN.LEFT, 2))
    card(s, x, 1.88, 6.09, 4.25, paras)


refs_card(0.45, left, 1)
refs_card(6.79, right, 5)

# ================================================================ SLIDE 8 - TEAM
s = prs.slides[7]
team = [
    ("Team Lead", "Yogeshwaran S", "AIML", "3rd Year", "New Horizon College of Engineering"),
    ("Backend Developer", "Sampreetha", "AIML", "3rd Year", "New Horizon College of Engineering"),
    ("ML Developer", "Sunku Joshika", "AIML", "3rd Year", "New Horizon College of Engineering"),
    ("UI/UX & Testing", "V Vikas", "AIML", "3rd Year", "New Horizon College of Engineering"),
]
for sh in s.shapes:
    if sh.has_table:
        t = sh.table
        for ri, row in enumerate(team, start=1):
            for ci, val in enumerate(row):
                cell = t.cell(ri, ci)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                p = cell.text_frame.paragraphs[0]
                p.text = ""
                p.alignment = PP_ALIGN.CENTER
                p.line_spacing = 1.0
                p.space_before = Pt(0)
                p.space_after = Pt(0)
                r = p.add_run()
                r.text = val
                r.font.name = FONT
                r.font.size = Pt(14)
                r.font.bold = ci in (0, 1)
                r.font.color.rgb = LIME if ci == 0 else WHITE

for out in OUTS:
    prs.save(out)
    print("saved", out)
