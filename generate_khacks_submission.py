"""Fills the K! Hacks 4.0 online-submission template with Team Proxy's focused, high-impact E-Healthcare deck."""
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
AMBER = RGBColor(251, 191, 36)
WHITE = RGBColor(255, 255, 255)
LIGHT = RGBColor(220, 228, 240)
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


def card(slide, x, y, w, h, paras, fill=CARD, alpha=84, line=TEAL, line_w=0.9,
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


def subtitle(slide, text, y=1.18, w=12.4):
    textbox(slide, 0.45, y, w, 0.45, [([R(text, 14, False, WHITE, True)],)])


def bullet(text_bold, text, size=12, sb=6, mark_color=TEAL):
    runs = [R("▪  ", size, True, mark_color)]
    if text_bold:
        runs.append(R(text_bold, size, True, WHITE))
    runs.append(R(text, size, False, LIGHT))
    return (runs, PP_ALIGN.LEFT, sb)


def arrow(slide, x, y, w=0.30, h=0.32):
    a = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    a.shadow.inherit = False
    a.fill.solid()
    a.fill.fore_color.rgb = TEAL
    a.line.fill.background()


# ================================================================ SLIDE 1 - TITLE
s = prs.slides[0]
for sh in s.shapes:
    if sh.has_text_frame and "Team Name" in sh.text:
        values = ["Proxy", "New Horizon College of Engineering", "Health Tech"]
        paras = sh.text_frame.paragraphs
        for p, val in zip(paras, values):
            for r in p.runs:
                if "Type Here" in r.text:
                    r.text = r.text.replace("Type Here", val)
        new_p = copy.deepcopy(paras[-1]._p)
        sh.text_frame._txBody.append(new_p)
        last = sh.text_frame.paragraphs[-1]
        runs = last.runs
        for r in runs[1:]:
            r._r.getparent().remove(r._r)
        runs[0].text = "Project Title   :    E-Healthcare"
        sh.height = Inches(1.95)

textbox(s, 1.58, 5.25, 10.3, 0.5, [([R("Delivering Critical Medical Intelligence Within the First 15 Seconds of an Emergency",
                                       16, False, LIME, True)],)])

# ================================================================ SLIDE 2 - PROBLEM STATEMENT
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
      "Critical minutes are lost running basic baseline tests."]),
]
cw, gap, cy, ch = 3.977, 0.25, 2.6, 2.7
for i, (num, title, body) in enumerate(cols):
    paras = [([R(num + "  ", 22, True, LIME), R(title, 15, True, WHITE)],)]
    for b in body:
        paras.append(bullet(None, b, 13, 8))
    card(s, 0.45 + i * (cw + gap), cy, cw, ch, paras)

card(s, 0.45, 5.45, 12.43, 0.68, [([
    R("Core Problem:  ", 13.5, True, LIME),
    R("In an accident, life-saving medical data is trapped behind physical shock, locked screens, and "
      "authentication walls—costing patients the Golden Hour.", 13.5, False, WHITE)],)],
     line=LIME, anchor=MSO_ANCHOR.MIDDLE)

# ================================================================ SLIDE 3 - SOLUTION ABSTRACT (3 CORE FEATURES)
s = prs.slides[2]
drop_placeholder(s)
subtitle(s, "E-Healthcare unlocks life-saving medical intelligence in under 15 seconds through three focused "
            "core features—without compromising patient privacy.")

features = [
    ("FEATURE 01", "15-Second Dual-Role Handshake",
     "Separates public bystander help from verified doctor access.",
     [("Bystander QR View (No Login): ", "Scanning the lock-screen QR shows ONLY Blood Group (O+) and 1-tap buttons to call family or send live GPS via SMS. Zero private records exposed."),
      ("Doctor Name Lookup (<3s): ", "Verified ER doctors simply enter the patient's name—no hash codes or OTPs—to unlock drug allergies (Penicillin), blood thinners, implants, and vitals.")]),

    ("FEATURE 02", "Break-Glass Audit & Consent Shield",
     "Prevents misuse of name-based lookup with cryptographic accountability.",
     [("Immutable SHA-256 Log: ", "Every emergency lookup automatically records the Doctor ID, Hospital, Timestamp, and Clinical Reason in a tamper-proof audit block."),
      ("Instant Family Alert: ", "The patient's emergency contact receives an automated SMS whenever a hospital unlocks their trauma record."),
      ("Granular Vault: ", "Sensitive non-emergency records stay hidden behind patient consent.")]),

    ("FEATURE 03", "Vernacular Voice Triage & Lab AI",
     "Bridges the language and diagnostic gap before and during care.",
     [("6-Language Voice Triage: ", "Patients speak symptoms in Tamil, Telugu, Kannada, Malayalam, Hindi, or English; our Bayesian engine scores urgency and routes care."),
      ("Automated Lab Flagging: ", "Uploads of blood/scan reports (CBC, LFT, glucose, platelets) are parsed in seconds to highlight critical abnormal values for the doctor.")]),
]
cw, cy, ch = 3.977, 1.85, 3.38
for i, (tag, title, sub, pts) in enumerate(features):
    paras = [
        ([R(tag + "  —  ", 12, True, LIME), R(title, 13.5, True, WHITE)],),
        ([R(sub, 11.5, False, TEAL, True)], PP_ALIGN.LEFT, 3),
    ]
    for b, t in pts:
        paras.append(bullet(b, t, 11.8, 6))
    card(s, 0.45 + i * (cw + 0.25), cy, cw, ch, paras, line=LIME if i == 0 else TEAL)

card(s, 0.45, 5.36, 12.43, 0.76, [([
    R("Why It Wins the Golden Hour:  ", 13, True, LIME),
    R("A bystander at a crash site triggers GPS family alerts in 15 seconds with zero privacy leakage, while the "
      "receiving ER doctor pulls the complete allergy and medication baseline in 3 seconds just by entering the patient's name.",
      12.5, False, WHITE)],)],
     line=LIME, fill=HEAD, alpha=88, anchor=MSO_ANCHOR.MIDDLE)

# ================================================================ SLIDE 4 - ARCHITECTURE AND SYSTEM DESIGN
s = prs.slides[3]
drop_placeholder(s)
subtitle(s, "Role-aware architecture that separates public bystander actions from verified clinical data retrieval "
            "at the API gateway level.", y=1.64, w=12.4)

top = 2.04
bt, bh = 2.32, 2.66
mid = bt + bh / 2 - 0.16

# Col 1: Entry Channels
textbox(s, 0.45, top, 2.25, 0.28, [([R("1. ENTRY CHANNELS", 11, True, LIME)],)])
entries = [
    ("Lock-Screen QR Scan", "Bystander · No app or login"),
    ("Patient Name Search", "ER Doctor · No hash or OTP"),
    ("6-Language Voice Input", "Patient · Web Speech API"),
]
for j, (et, es) in enumerate(entries):
    card(s, 0.45, bt + j * 0.92, 2.25, 0.80, [
        ([R(et, 12, True, WHITE)], PP_ALIGN.CENTER),
        ([R(es, 10.5, False, TEAL)], PP_ALIGN.CENTER, 2),
    ], anchor=MSO_ANCHOR.MIDDLE, margin=0.08)
arrow(s, 2.76, mid)

# Col 2: Security & Role Gateway
textbox(s, 3.12, top, 2.65, 0.28, [([R("2. ROLE GATEWAY (FastAPI)", 11, True, LIME)],)])
card(s, 3.12, bt, 2.65, bh, [
    ([R("JWT + Role Router", 13.5, True, LIME)],),
    bullet("Public QR Route: ", "Strips all private history; returns only Blood Group, Name & 1-Tap SOS trigger.", 11.3, 6),
    bullet("Clinician Route: ", "Verifies doctor JWT; runs case-insensitive name search (ILIKE) in <50ms.", 11.3, 6),
    bullet("Rate & Scope Guard: ", "Blocks unverified queries and enforces break-glass logging.", 11.3, 6),
])
arrow(s, 5.83, mid)

# Col 3: 3 Core Engines
textbox(s, 6.19, top, 4.10, 0.28, [([R("3. CORE INTELLIGENCE ENGINES", 11, True, LIME)],)])
engines = [
    ("Dual-Role Emergency Engine", "Builds trauma baseline (Allergies, Blood Thinners, Implants, Vitals) & dispatches live GPS SMS."),
    ("SHA-256 Break-Glass Audit Ledger", "Hash-chains every emergency access (Doctor ID + Hospital + Timestamp + Reason) & alerts family."),
    ("Bayesian Voice Triage & Lab Parser", "Scores symptom urgency across 6 Indian languages & flags abnormal lab PDF biomarkers."),
]
for j, (en_t, en_d) in enumerate(engines):
    card(s, 6.19, bt + j * 0.92, 4.10, 0.82, [
        ([R(en_t, 12, True, LIME if j == 0 else TEAL)],),
        ([R(en_d, 10.5, False, LIGHT)], PP_ALIGN.LEFT, 2),
    ], fill=HEAD if j == 0 else CARD, alpha=88, anchor=MSO_ANCHOR.MIDDLE, margin=0.10)
arrow(s, 10.35, mid)

# Col 4: Storage & External
textbox(s, 10.71, top, 2.17, 0.28, [([R("4. DATA & DISPATCH", 11, True, LIME)],)])
card(s, 10.71, bt, 2.17, 1.26, [
    ([R("ACID Database", 12.5, True, LIME)],),
    ([R("PostgreSQL / SQLite via SQLAlchemy ORM; indexed on Patient Name, Phone & ID.", 10.8, False, LIGHT)], PP_ALIGN.LEFT, 4),
])
card(s, 10.71, bt + 1.40, 2.17, 1.26, [
    ([R("Live Dispatch", 12.5, True, LIME)],),
    ([R("Fast2SMS cellular gateway (GPS map links to family) & browser speech synthesis.", 10.8, False, LIGHT)], PP_ALIGN.LEFT, 4),
])

# Bottom Flow
textbox(s, 0.45, 5.08, 4.5, 0.28, [([R("END-TO-END 15-SECOND EMERGENCY HANDSHAKE", 11, True, LIME)],)])
steps = [
    "1. Bystander Scans QR",
    "2. GPS SMS Sent to Family",
    "3. ER Doctor Enters Name",
    "4. Allergies Unlocked (<3s)",
    "5. SHA-256 Audit Logged",
]
sw = 12.43 / 5
for k, st in enumerate(steps):
    shp = MSO_SHAPE.PENTAGON if k == 0 else MSO_SHAPE.CHEVRON
    card(s, 0.45 + k * sw, 5.38, sw + 0.05, 0.62,
         [([R(st, 11.5, True, WHITE if k % 2 == 0 else CARD)], PP_ALIGN.CENTER)],
         shape=shp, fill=HEAD if k % 2 == 0 else TEAL, alpha=100, line=None, anchor=MSO_ANCHOR.MIDDLE, margin=0.22)

# ================================================================ SLIDE 5 - FEASIBILITY & USP
s = prs.slides[4]
drop_placeholder(s)
subtitle(s, "A fully working, legally compliant system built around the exact emergency failure points that "
            "existing health apps fail to solve.", y=1.64, w=12.4)

card(s, 0.45, 2.08, 4.75, 4.05, [
    ([R("TECHNICAL & LEGAL FEASIBILITY", 13.5, True, LIME)],),
    bullet("100% Working Prototype: ", "Live FastAPI backend + Doctor, Patient & Emergency portals with <50ms name lookup.", 11.8, 8),
    bullet("Zero Hardware Cost: ", "Works on any phone browser with no app install; lock-screen QR or printed ID sticker costs < ₹5.", 11.8, 7),
    bullet("Legal Backing (DPDP Act 2023): ", "Section 7(d) explicitly permits processing personal data in a medical emergency; our audit log prevents misuse.", 11.8, 7),
    bullet("Offline Cellular Fallback: ", "Family SOS dispatch uses standard cellular SMS with GPS coordinates, working even in low-data zones.", 11.8, 7),
    bullet("ABDM & FHIR R4 Ready: ", "Clinical records map to standard FHIR AllergyIntolerance and Patient schemas.", 11.8, 7),
], line=LIME)

rows = [
    ("Core Capability", "Standard Health Apps / Isolated EMRs", "E-Healthcare (Our USP)"),
    ("Unconscious Patient Access", "Blocked by phone lock, OTP, or 64-char hash code", "15s QR scan + Doctor lookup by Name (<3s)"),
    ("Bystander Privacy Protection", "Static QR cards expose full medical history to all", "Dual-Role Split View (Bystander sees only Blood + SOS)"),
    ("Doctor Accountability", "No tracking of emergency record lookups", "SHA-256 Break-Glass Audit + instant family SMS alert"),
    ("Language Accessibility", "English-only forms and complex menus", "Voice symptom triage in 6 Indian languages"),
    ("Lab Report Triage", "Doctor manually reads multi-page PDFs", "Automated extraction & abnormal value flagging"),
]
tx, ty, tw = 5.38, 2.08, 7.50
tbl_shape = s.shapes.add_table(len(rows), 3, Inches(tx), Inches(ty), Inches(tw), Inches(4.05))
tbl = tbl_shape.table
tbl.first_row = True
for ci, wdt in enumerate([1.95, 2.65, 2.90]):
    tbl.columns[ci].width = Inches(wdt)
for ri, row in enumerate(rows):
    tbl.rows[ri].height = Inches(0.55 if ri == 0 else 0.70)
    for ci, val in enumerate(row):
        cell = tbl.cell(ri, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = HEAD if ri == 0 else (CARD if ri % 2 else RGBColor(20, 34, 64))
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = cell.margin_right = Inches(0.09)
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = ""
        r = p.add_run()
        r.text = val
        r.font.name = FONT
        if ri == 0:
            r.font.size, r.font.bold = Pt(12.5), True
            r.font.color.rgb = LIME if ci == 2 else WHITE
        else:
            r.font.size = Pt(11.5)
            r.font.bold = ci != 1
            r.font.color.rgb = TEAL if ci == 0 else (DIM if ci == 1 else WHITE)

# ================================================================ SLIDE 6 - MARKET STUDY & BUSINESS MODEL
s = prs.slides[5]
drop_placeholder(s)
subtitle(s, "Free basic emergency protection for citizens, supported by institutional healthcare subscriptions.",
         y=1.64, w=12.4)

cw, cy, ch = 3.977, 2.02, 2.58
market = [
    ("MARKET OPPORTUNITY", "Who needs E-Healthcare?", [
        ("Primary Customers: ", "Hospitals, emergency departments, ambulance operators and healthcare institutions."),
        ("Secondary Users: ", "Students, elderly individuals, chronic patients and their families."),
        ("Initial Target Market: ", "Multi-specialty hospitals, ambulance services and educational institutions in Chennai and Bengaluru."),
        ("Market Need: ", "Faster access to critical medical information, emergency communication and accountable patient-record access."),
    ]),
    ("B2B / B2G REVENUE MODEL", "How will it earn?", [
        ("Citizens: ", "Free basic emergency QR profile and emergency contact access."),
        ("Hospital ER Subscription: ", "Proposed ₹15,000/month for clinician access, emergency record retrieval, audit logs and lab-report flagging."),
        ("Ambulance Fleet License: ", "Annual subscription for emergency information access and paramedic support."),
        ("Campus & Corporate Plans: ", "Proposed ₹99/person/year for QR-based emergency identification and family SOS features."),
    ]),
    ("GO-TO-MARKET STRATEGY", "How will it grow?", [
        ("Phase 1 – Campus Pilot: ", "Introduce QR-based emergency IDs within our college community and evaluate usability."),
        ("Phase 2 – Hospital Pilot: ", "Approach partner hospitals to evaluate clinician name lookup and emergency record access."),
        ("Phase 3 – Ambulance Integration: ", "Explore partnerships with ambulance operators for emergency information sharing."),
        ("Phase 4 – Expansion: ", "Work towards FHIR-based interoperability and potential ABDM integration."),
    ]),
]
for i, (head, sub, pts) in enumerate(market):
    paras = [
        ([R(head, 12.5, True, LIME)],),
        ([R(sub, 10.5, False, TEAL, True)], PP_ALIGN.LEFT, 1),
    ]
    for b, t in pts:
        paras.append(bullet(b, t, 10.2, 3))
    card(s, 0.45 + i * (cw + 0.25), cy, cw, ch, paras, line=LIME if i == 1 else TEAL, margin=0.12)

alts = [
    ("ABHA / PHR Apps",
     "Focuses on health identity & record exchange. Our differentiation: emergency-first access to selected critical medical information."),
    ("Hospital EMRs",
     "Manages clinical records within an institution. Our differentiation: designed to support emergency access across institutional boundaries."),
    ("Static Medical ID Bracelets",
     "Displays fixed printed text only. Our differentiation: dynamic QR access, emergency communication and access accountability."),
]
card(s, 0.45, 4.68, 12.43, 1.48, [([R("EXISTING ALTERNATIVES & OUR SPECIFIC DIFFERENTIATION", 12, True, LIME)],)],
     line=LIME, margin=0.12)
aw = 12.1 / 3
for i, (a, gapt) in enumerate(alts):
    textbox(s, 0.62 + i * aw, 4.98, aw - 0.15, 0.74, [
        ([R(a, 11.5, True, WHITE)],),
        ([R(gapt, 10.3, False, LIGHT)], PP_ALIGN.LEFT, 2)])

textbox(s, 0.62, 5.76, 12.1, 0.34, [([
    R("Value Proposition:  ", 11, True, LIME),
    R("Reduce delays in accessing critical patient information, improve emergency communication, and provide "
      "accountable medical-record access.", 11, False, WHITE, True)],)])

# ================================================================ SLIDE 7 - RESEARCH AND REFERENCES
s = prs.slides[6]
drop_placeholder(s)
subtitle(s, "Every core feature of E-Healthcare is grounded in government accident data, Indian data-protection "
            "law, and clinical interoperability standards.", y=1.64, w=12.4)

left = [
    ("Ministry of Road Transport & Highways (MoRTH), ",
     "Road Accidents in India Annual Report (2022), Govt. of India — 4,61,312 accidents & 1,68,491 deaths.",
     "Validates the Golden Hour trauma identification gap (Slide 2 & Feature 1)"),
    ("Digital Personal Data Protection (DPDP) Act, 2023, ",
     "Section 7(d) — Legitimate Uses for Medical Emergencies Involving Threat to Life, Govt. of India.",
     "Legal basis for zero-OTP Doctor Name Lookup in emergencies (Feature 1 & 2)"),
    ("Supreme Court of India, ",
     "Pt. Parmanand Katara v. Union of India (AIR 1989 SC 2039) — Constitutional Right to Emergency Care.",
     "Mandates immediate clinical intervention without procedural/auth barriers"),
]
right = [
    ("IEEE Journal of Biomedical & Health Informatics, ",
     "Cryptographic Break-Glass Access Control for Emergency Electronic Health Records.",
     "Basis for our SHA-256 Break-Glass Audit Ledger & family SMS alert (Feature 2)"),
    ("HL7 International Standards, ",
     "FHIR Release 4 (v4.0.1) — International Patient Summary, AllergyIntolerance & Observation Profiles.",
     "Schema design for our Emergency Trauma Dossier & Lab Report Parser (Feature 3)"),
    ("National Health Authority (NHA), ",
     "Ayushman Bharat Digital Mission (ABDM) — Health Information Exchange & Consent Manager Blueprint.",
     "National hospital & ambulance interoperability roadmap (Slide 4 & 6)"),
]


def refs_card(x, items, start):
    paras = []
    for n, (who, what, used) in enumerate(items, start):
        paras.append(([R(f"[{n}]  ", 12.5, True, LIME), R(who, 12.5, True, WHITE), R(what, 12, False, LIGHT)],
                      PP_ALIGN.LEFT, 0 if n == start else 11))
        paras.append(([R("▸ Directly supports: " + used, 11.2, True, TEAL, False)], PP_ALIGN.LEFT, 3))
    card(s, x, 2.08, 6.09, 4.05, paras)


refs_card(0.45, left, 1)
refs_card(6.79, right, 4)

# ================================================================ SLIDE 8 - TEAM DETAILS
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
