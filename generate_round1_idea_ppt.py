"""Generates Team Proxy's Round 1 Idea Submission PPTX & PDF in a clean, minimalist editorial theme:
Slide 1: Title & Team Details (Yogeshwaran V M S, Sunku Joshika, Sampreetha S — no roles, no evaluation criteria list)
Slide 2: Problem Statement
Slide 3: Proposed Solution
Slide 4: Innovative Aspects
Slide 5: Implementation Approach
Slide 6: Security Component
"""
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

OUT_PPTX_WORKSPACE = r"c:\Users\yoges\Downloads\e-healthcare\Round1_Idea_Submission_Proxy.pptx"
OUT_PPTX_DOWNLOADS = r"C:\Users\yoges\Downloads\Round1_Idea_Submission_Proxy.pptx"

prs = pptx.Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

FONT = "Calibri"

# Minimalist, Restrained Editorial Clinical Palette (Off-White + Deep Slate + Single Navy Accent)
BG_PAGE = RGBColor(248, 250, 252)      # Crisp Alabaster / Off-White (#F8FAFC)
CARD_WHITE = RGBColor(255, 255, 255)   # Pure White surface (#FFFFFF)
CARD_TINT = RGBColor(241, 245, 249)    # Subtle Slate Tint (#F1F5F9)
BORDER_GRAY = RGBColor(203, 213, 225)  # Quiet Gray Border (#CBD5E1)
NAVY = RGBColor(30, 58, 138)           # Primary Deep Clinical Navy (#1E3A8A)
TEAL = RGBColor(15, 118, 110)          # Secondary Muted Clinical Teal (#0F766E)
INK_DARK = RGBColor(15, 23, 42)        # Primary Heading Ink (#0F172A)
INK_BODY = RGBColor(51, 65, 85)        # Body Text Slate (#334155)
INK_MUTED = RGBColor(100, 116, 139)    # Caption Muted Slate (#64748B)
WHITE = RGBColor(255, 255, 255)


def R(text, size=12, bold=False, color=INK_BODY, italic=False):
    return (text, size, bold, color, italic)


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


def add_bg(slide):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG_PAGE
    bg.line.fill.background()
    bg.shadow.inherit = False
    # Subtle top navy rule
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.06))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = NAVY
    top_bar.line.fill.background()
    top_bar.shadow.inherit = False


def add_header(slide, section_label, title_text, subtitle_text, slide_no):
    add_bg(slide)
    # Section overline text (clean typography, no boxy pill)
    tb_sec = slide.shapes.add_textbox(Inches(0.65), Inches(0.36), Inches(7.5), Inches(0.28))
    stf_sec = tb_sec.text_frame
    stf_sec.margin_left = stf_sec.margin_top = stf_sec.margin_bottom = 0
    write(stf_sec, [([R(section_label.upper(), 10.5, True, TEAL)],)])

    # Top-right header tag
    tb_meta = slide.shapes.add_textbox(Inches(8.5), Inches(0.36), Inches(4.18), Inches(0.28))
    mtf = tb_meta.text_frame
    mtf.margin_right = mtf.margin_top = mtf.margin_bottom = 0
    write(mtf, [([R("E-HEALTHCARE  ·  TEAM PROXY", 10, True, INK_MUTED)], PP_ALIGN.RIGHT)])

    # Main Title
    tb_t = slide.shapes.add_textbox(Inches(0.65), Inches(0.66), Inches(12.03), Inches(0.50))
    ttf = tb_t.text_frame
    ttf.word_wrap = True
    ttf.margin_left = ttf.margin_top = ttf.margin_bottom = 0
    write(ttf, [([R(title_text, 23, True, INK_DARK)],)])

    # Subtitle
    tb_s = slide.shapes.add_textbox(Inches(0.65), Inches(1.18), Inches(12.03), Inches(0.36))
    stf = tb_s.text_frame
    stf.word_wrap = True
    stf.margin_left = stf.margin_top = stf.margin_bottom = 0
    write(stf, [([R(subtitle_text, 13, False, INK_MUTED)],)])

    # Divider line under header
    div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.65), Inches(1.58), Inches(12.03), Inches(0.012))
    div.fill.solid()
    div.fill.fore_color.rgb = BORDER_GRAY
    div.line.fill.background()

    # Footer line & text
    foot_line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.65), Inches(7.02), Inches(12.03), Inches(0.012)
    )
    foot_line.fill.solid()
    foot_line.fill.fore_color.rgb = BORDER_GRAY
    foot_line.line.fill.background()

    tb_f = slide.shapes.add_textbox(Inches(0.65), Inches(7.08), Inches(8.5), Inches(0.28))
    ftf = tb_f.text_frame
    ftf.margin_left = 0
    write(ftf, [([R("Round 1 Idea Submission  ·  New Horizon College of Engineering  ·  Health Tech Track", 9.8, False, INK_MUTED)],)])

    tb_p = slide.shapes.add_textbox(Inches(10.5), Inches(7.08), Inches(2.18), Inches(0.28))
    ptf = tb_p.text_frame
    ptf.margin_right = 0
    write(ptf, [([R(f"Slide {slide_no} of 6", 9.8, True, NAVY)], PP_ALIGN.RIGHT)])


def panel(slide, x, y, w, h, paras, fill=CARD_WHITE, border=BORDER_GRAY, border_w=0.75,
          top_bar_color=None, anchor=MSO_ANCHOR.TOP, margin=0.20):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.shadow.inherit = False
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if border is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = border
        sh.line.width = Pt(border_w)
    tf = sh.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin + (0.04 if top_bar_color else 0))
    tf.margin_bottom = Inches(margin * 0.85)
    write(tf, paras)

    if top_bar_color is not None:
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(0.045))
        bar.fill.solid()
        bar.fill.fore_color.rgb = top_bar_color
        bar.line.fill.background()
        bar.shadow.inherit = False
    return sh


def bullet(bold_lead, text, size=11.5, sb=7):
    runs = [R("•  ", size, True, NAVY)]
    if bold_lead:
        runs.append(R(bold_lead, size, True, INK_DARK))
    runs.append(R(text, size, False, INK_BODY))
    return (runs, PP_ALIGN.LEFT, sb)


def arrow(slide, x, y, w=0.26, h=0.26):
    a = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    a.shadow.inherit = False
    a.fill.solid()
    a.fill.fore_color.rgb = NAVY
    a.line.fill.background()


# ==============================================================================
# SLIDE 1: TITLE & TEAM DETAILS (Minimalist, Clean, No Clutter)
# ==============================================================================
s1 = prs.slides.add_slide(blank_layout)
add_bg(s1)

# Left vertical accent strip
strip = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.85), Inches(1.15), Inches(0.07), Inches(2.25))
strip.fill.solid()
strip.fill.fore_color.rgb = NAVY
strip.line.fill.background()
strip.shadow.inherit = False

# Title & Subtitle block
tb1 = s1.shapes.add_textbox(Inches(1.12), Inches(1.08), Inches(11.3), Inches(2.40))
tf1 = tb1.text_frame
tf1.word_wrap = True
write(tf1, [
    ([R("ROUND 1 IDEA SUBMISSION  ·  HEALTH TECH TRACK", 11.5, True, TEAL)],),
    ([R("E-Healthcare", 44, True, INK_DARK)], PP_ALIGN.LEFT, 8),
    ([R("Instant, Privacy-Safe Emergency Medical Access & Vernacular Clinical Triage", 19, False, NAVY)], PP_ALIGN.LEFT, 6),
    ([R("Delivering critical medical intelligence within the first 15 seconds of an emergency—without compromising patient privacy.",
       13.5, False, INK_MUTED, True)], PP_ALIGN.LEFT, 10),
])

# Clean Team Details Panel (No roles, no evaluation criteria)
team_paras = [
    ([R("TEAM DETAILS", 11.5, True, TEAL)],),
    ([R("Team Name:        ", 13.5, True, INK_MUTED), R("Team Proxy", 14, True, INK_DARK)], PP_ALIGN.LEFT, 12),
    ([R("College Name:    ", 13.5, True, INK_MUTED), R("New Horizon College of Engineering", 14, True, INK_DARK)], PP_ALIGN.LEFT, 8),
    ([R("Department:       ", 13.5, True, INK_MUTED), R("Artificial Intelligence & Machine Learning (AIML)", 13.5, False, INK_BODY)], PP_ALIGN.LEFT, 8),
    ([R("Team Members:", 13.5, True, INK_MUTED)], PP_ALIGN.LEFT, 14),
    ([R("      1.  Yogeshwaran V M S", 14, True, INK_DARK)], PP_ALIGN.LEFT, 6),
    ([R("      2.  Sunku Joshika", 14, True, INK_DARK)], PP_ALIGN.LEFT, 5),
    ([R("      3.  Sampreetha S", 14, True, INK_DARK)], PP_ALIGN.LEFT, 5),
]
panel(s1, 1.12, 3.68, 7.60, 3.05, team_paras, fill=CARD_WHITE, border=BORDER_GRAY, top_bar_color=NAVY, margin=0.22)

# Footer on Slide 1
foot1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.85), Inches(7.02), Inches(11.63), Inches(0.012))
foot1.fill.solid()
foot1.fill.fore_color.rgb = BORDER_GRAY
foot1.line.fill.background()

tb_f1 = s1.shapes.add_textbox(Inches(0.85), Inches(7.08), Inches(11.63), Inches(0.28))
write(tb_f1.text_frame, [([R("E-Healthcare  ·  Team Proxy  ·  New Horizon College of Engineering", 10, False, INK_MUTED)],)])


# ==============================================================================
# SLIDE 2: PROBLEM STATEMENT
# ==============================================================================
s2 = prs.slides.add_slide(blank_layout)
add_header(
    s2, "01 · Problem Statement",
    "The Emergency Dead End: Three Points of Failure",
    "When an accident victim or acute patient reaches an emergency room, the clinical facts needed to treat them safely are unreachable.",
    2
)

# Context bar
panel(s2, 0.65, 1.78, 12.03, 0.64, [([
    R("Context & Scale:  ", 12.5, True, NAVY),
    R("India recorded 4,61,312 road accidents and 1,68,491 deaths in 2022 (MoRTH). In critical trauma, treating an unconscious patient without knowing their blood group, drug allergies, or blood thinners leads to preventable complications during the Golden Hour.",
      12, False, INK_BODY)
],)], fill=CARD_TINT, border=BORDER_GRAY, anchor=MSO_ANCHOR.MIDDLE, margin=0.14)

p_cols = [
    ("01 · PHYSICAL BARRIER", "The Patient Cannot Speak",
     [("Unconscious or in shock: ", "Accident, stroke, or cardiac victims cannot state their blood group, severe drug allergies, or chronic conditions such as diabetes, epilepsy, or heart disease."),
      ("No family contact at scene: ", "Bystanders and ambulance staff have no immediate way to identify or notify the patient's family members.")]),

    ("02 · DIGITAL BARRIER", "The Phone & Apps Are Locked",
     [("Locked smartphones: ", "99% of phones are secured with PINs or biometrics; emergency contacts and health cards remain trapped behind the lock screen."),
      ("OTP & access-code dead end: ", "Existing health portals and consent-first apps require the patient's own OTP, password, or 64-character access code—impossible when the patient is unconscious.")]),

    ("03 · CLINICAL BARRIER", "The Hospital Cannot Wait",
     [("Blind emergency treatment: ", "Doctors must act immediately; an unknown Penicillin allergy can trigger fatal anaphylaxis, and undisclosed blood thinners cause severe surgical bleeding."),
      ("Diagnostic & handover delays: ", "20–40 critical minutes are lost repeating baseline tests, and key details get lost during shift handovers.")]),
]
cw, gap = 3.84, 0.255
for i, (tag, title, pts) in enumerate(p_cols):
    paras = [
        ([R(tag, 10.5, True, TEAL)],),
        ([R(title, 15.5, True, INK_DARK)], PP_ALIGN.LEFT, 4),
    ]
    for b, t in pts:
        paras.append(bullet(b, t, 11.8, 9))
    panel(s2, 0.65 + i * (cw + gap), 2.58, cw, 3.38, paras, top_bar_color=NAVY)

panel(s2, 0.65, 6.12, 12.03, 0.72, [([
    R("Core Problem Statement:  ", 12.5, True, NAVY),
    R("There is currently no fast, privacy-safe mechanism that lets bystanders trigger emergency help AND lets verified ER doctors retrieve a patient's critical medical baseline in seconds without requiring OTPs or hash codes.",
      12, False, INK_DARK)
],)], fill=CARD_TINT, border=BORDER_GRAY, anchor=MSO_ANCHOR.MIDDLE, margin=0.14)


# ==============================================================================
# SLIDE 3: PROPOSED SOLUTION
# ==============================================================================
s3 = prs.slides.add_slide(blank_layout)
add_header(
    s3, "02 · Proposed Solution",
    "Role-Based Emergency Medical Access & Vernacular Triage Platform",
    "E-Healthcare delivers the right level of medical information to bystanders, ER clinicians, and patients within seconds.",
    3
)

sol_cols = [
    ("MODULE 01 · PUBLIC RESPONDER", "Lock-Screen Emergency QR",
     "For Bystanders at the Scene (< 15 Seconds)",
     [("Zero App / Zero Login: ", "Anyone can scan the QR sticker on the patient's phone lock-screen, helmet, or college/office ID card using a standard phone camera."),
      ("Survival-Only View: ", "Displays ONLY Name, Age, Blood Group (e.g., O+ Positive), and one-touch emergency family call buttons."),
      ("1-Tap Live GPS SMS Alert: ", "Tapping 'Notify Family' dispatches an automated cellular SMS with a live Google Maps location link to family members."),
      ("Strict Privacy: ", "Zero diagnoses, prescriptions, or lab reports are ever shown to the public.")]),

    ("MODULE 02 · VERIFIED CLINICIAN", "Doctor Name-Based Lookup",
     "For Paramedics & ER Doctors (< 3 Seconds)",
     [("No Hash Code or OTP Needed: ", "Verified doctors log into the hospital console and search directly by the patient's name, phone, or ID."),
      ("Critical Trauma Baseline: ", "Instantly surfaces Drug Allergies (Penicillin/Sulfa), Active High-Risk Meds (blood thinners, insulin), Implants, and Chronic Conditions."),
      ("Complete Clinical Dossier: ", "Provides latest vitals (BP, SpO2, HR, glucose), past consultations, active prescriptions, and uploaded lab reports."),
      ("SBAR Continuity: ", "Generates structured Situation-Background-Assessment-Recommendation handover notes.")]),

    ("MODULE 03 · PATIENT & FAMILY", "6-Language Voice & Lab AI",
     "For Everyday Preventive & Diagnostic Care",
     [("Vernacular Voice Triage: ", "Patients speak or type symptoms in Tamil, Telugu, Kannada, Malayalam, Hindi, or English; our Bayesian engine predicts urgency and department."),
      ("Automated Lab Flagging: ", "Uploads of blood/scan reports (CBC, LFT, glucose, platelets) are parsed automatically to highlight abnormal biomarkers."),
      ("Family Dependent Vault: ", "Manage emergency profiles for elderly parents and children from a single account with granular consent controls.")]),
]
for i, (tag, title, sub, pts) in enumerate(sol_cols):
    paras = [
        ([R(tag, 10.5, True, TEAL)],),
        ([R(title, 15, True, INK_DARK)], PP_ALIGN.LEFT, 4),
        ([R(sub, 11, False, NAVY, True)], PP_ALIGN.LEFT, 2),
    ]
    for b, t in pts:
        paras.append(bullet(b, t, 11.3, 7))
    panel(s3, 0.65 + i * (cw + gap), 1.78, cw, 4.18, paras, top_bar_color=NAVY)

panel(s3, 0.65, 6.12, 12.03, 0.72, [([
    R("Solution Outcome:  ", 12.5, True, NAVY),
    R("Connects pre-hospital bystander GPS alerts, 3-second clinician record retrieval by name, and 6-language patient symptom triage in one unified workflow.",
      12, False, INK_DARK)
],)], fill=CARD_TINT, border=BORDER_GRAY, anchor=MSO_ANCHOR.MIDDLE, margin=0.14)


# ==============================================================================
# SLIDE 4: INNOVATIVE ASPECTS
# ==============================================================================
s4 = prs.slides.add_slide(blank_layout)
add_header(
    s4, "03 · Innovative Aspects",
    "Core Innovations: Solving the Speed vs. Privacy Trade-Off",
    "Instead of forcing an all-or-nothing choice between open QR cards and locked portals, E-Healthcare introduces three practical innovations.",
    4
)

inno_items = [
    ("INNOVATION 01 · THE 15-SECOND DUAL-ROLE HANDSHAKE",
     "Same Patient Profile, Two Separate Role Views: ",
     "When a bystander scans the QR code, our server returns only Blood Group and 1-tap GPS family calling (0% medical history exposed). When an authenticated ER doctor queries the patient, the server unlocks drug allergies, blood thinners, implants, and vitals."),
    ("INNOVATION 02 · ZERO-HASH, ZERO-OTP DOCTOR NAME LOOKUP",
     "Decoupled from Patient Phone & Cryptographic Keys: ",
     "During trauma, patients cannot read out OTPs or 64-character SHA-256 hashes. We engineered a clinician directory resolver that lets verified ER doctors pull the full medical dossier simply by typing the patient's name—backed by automatic break-glass auditing."),
    ("INNOVATION 03 · VERNACULAR VOICE TRIAGE + LAB BIOMARKER AI",
     "Inclusive Pre-Care & Rapid Diagnostic Parsing: ",
     "Combines 6-language speech-to-symptom intake (Tamil, Telugu, Kannada, Malayalam, Hindi, English) with automated regex/PDF biomarker extraction that flags critical platelet, WBC, hemoglobin, and glucose anomalies in seconds."),
]
for idx, (head, lead, body) in enumerate(inno_items):
    panel(s4, 0.65, 1.78 + idx * 1.70, 6.00, 1.56, [
        ([R(head, 11.2, True, TEAL)],),
        bullet(lead, body, 11.2, 5),
    ], top_bar_color=NAVY, margin=0.15)

rows = [
    ("Evaluation Dimension", "Standard Health Apps / Static QR", "E-Healthcare Innovation"),
    ("Unconscious Patient Access", "Blocked by phone lock, OTP, or hash key", "15s QR scan + <3s Doctor lookup by Name"),
    ("Bystander Privacy Control", "Static QR exposes all conditions publicly", "Dual-Role Split View (Blood + SOS only)"),
    ("Clinician Accountability", "Unlogged or unverified record viewing", "Tamper-proof SHA-256 Break-Glass + SMS alert"),
    ("Regional Accessibility", "English-heavy forms & menus", "Voice triage in 6 Indian languages"),
    ("Lab Report Review in ER", "Manual reading of multi-page PDFs", "Automated critical biomarker flagging"),
    ("Inter-Shift Continuity", "Unstructured free-text doctor notes", "Built-in WHO SBAR handover generator"),
]
tbl_sh = s4.shapes.add_table(len(rows), 3, Inches(6.88), Inches(1.78), Inches(5.80), Inches(4.96))
tbl = tbl_sh.table
tbl.first_row = True
for ci, wdt in enumerate([1.68, 1.95, 2.17]):
    tbl.columns[ci].width = Inches(wdt)
for ri, row in enumerate(rows):
    tbl.rows[ri].height = Inches(0.55 if ri == 0 else 0.63)
    for ci, val in enumerate(row):
        cell = tbl.cell(ri, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY if ri == 0 else (CARD_WHITE if ri % 2 == 1 else CARD_TINT)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = cell.margin_right = Inches(0.08)
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = ""
        r = p.add_run()
        r.text = val
        r.font.name = FONT
        if ri == 0:
            r.font.size, r.font.bold = Pt(11.2), True
            r.font.color.rgb = WHITE
        else:
            r.font.size = Pt(10.8)
            r.font.bold = ci != 1
            r.font.color.rgb = INK_DARK if ci == 0 else (INK_MUTED if ci == 1 else TEAL)


# ==============================================================================
# SLIDE 5: IMPLEMENTATION APPROACH
# ==============================================================================
s5 = prs.slides.add_slide(blank_layout)
add_header(
    s5, "04 · Implementation Approach",
    "System Architecture, Technology Stack & Execution Pipeline",
    "Implemented as a modular full-stack web application using open-source technologies and standard clinical data models.",
    5
)

top_lbl = 1.74
bt, bh = 2.02, 3.04
mid = bt + bh / 2 - 0.13

# Stage 1: Client Portals
tb = s5.shapes.add_textbox(Inches(0.65), Inches(top_lbl), Inches(2.35), Inches(0.26))
write(tb.text_frame, [([R("1. CLIENT PORTALS", 10.5, True, TEAL)],)])
c_boxes = [
    ("Public Emergency View", "Camera QR scan · HTML5 + GPS API · 0 install"),
    ("Doctor Trauma Console", "Name search · Dossier · SBAR · Vitals charts"),
    ("Patient & Family Portal", "6-language Web Speech API · Lab upload · QR"),
]
for j, (ct, cd) in enumerate(c_boxes):
    panel(s5, 0.65, bt + j * 1.04, 2.35, 0.94, [
        ([R(ct, 11.5, True, INK_DARK)],),
        ([R(cd, 10.2, False, INK_MUTED)], PP_ALIGN.LEFT, 3),
    ], top_bar_color=NAVY, anchor=MSO_ANCHOR.MIDDLE, margin=0.10)
arrow(s5, 3.06, mid)

# Stage 2: FastAPI Application Server
tb = s5.shapes.add_textbox(Inches(3.38), Inches(top_lbl), Inches(2.80), Inches(0.26))
write(tb.text_frame, [([R("2. API GATEWAY (FastAPI)", 10.5, True, TEAL)],)])
panel(s5, 3.38, bt, 2.80, bh, [
    ([R("Python 3.11 + FastAPI", 13, True, INK_DARK)],),
    ([R("Async Uvicorn ASGI Server", 10.5, False, TEAL, True)], PP_ALIGN.LEFT, 2),
    bullet("REST Endpoints: ", "/api/doctors/patient-records, /api/emergency/live-passport, /api/blockchain/break-glass.", 10.8, 7),
    bullet("Pydantic Schemas: ", "Strict request/response validation mapped to HL7 FHIR R4 concepts.", 10.8, 6),
    bullet("Sub-50ms Name Search: ", "Case-insensitive tokenized ILIKE resolver across Patient & Family tables.", 10.8, 6),
], top_bar_color=NAVY, margin=0.14)
arrow(s5, 6.24, mid)

# Stage 3: Clinical & ML Engines
tb = s5.shapes.add_textbox(Inches(6.56), Inches(top_lbl), Inches(3.55), Inches(0.26))
write(tb.text_frame, [([R("3. CLINICAL & ML ENGINES", 10.5, True, TEAL)],)])
eng_boxes = [
    ("Bayesian Symptom Triage Engine", "Computes posterior disease & urgency probabilities across 6 languages."),
    ("Diagnostic Lab Report Parser", "Extracts CBC, platelet, WBC, Hb & glucose values from PDFs/text & flags anomalies."),
    ("SBAR & Vitals Grading Engine", "Generates structured handover notes & grades BP/SpO2/HR for shock alerts."),
]
for j, (et, ed) in enumerate(eng_boxes):
    panel(s5, 6.56, bt + j * 1.04, 3.55, 0.94, [
        ([R(et, 11.5, True, INK_DARK)],),
        ([R(ed, 10.2, False, INK_BODY)], PP_ALIGN.LEFT, 3),
    ], top_bar_color=TEAL, anchor=MSO_ANCHOR.MIDDLE, margin=0.10)
arrow(s5, 10.17, mid)

# Stage 4: Data & SMS Layer
tb = s5.shapes.add_textbox(Inches(10.49), Inches(top_lbl), Inches(2.19), Inches(0.26))
write(tb.text_frame, [([R("4. DATA & SMS LAYER", 10.5, True, TEAL)],)])
panel(s5, 10.49, bt, 2.19, 1.46, [
    ([R("Relational DB", 12, True, INK_DARK)],),
    ([R("PostgreSQL / SQLite via SQLAlchemy 2.0 ORM with ACID transactions & audit tables.", 10.5, False, INK_BODY)], PP_ALIGN.LEFT, 4),
], top_bar_color=NAVY, margin=0.12)
panel(s5, 10.49, bt + 1.58, 2.19, 1.46, [
    ([R("Live Gateways", 12, True, INK_DARK)],),
    ([R("Fast2SMS cellular API for GPS family alerts + APScheduler for medication reminders.", 10.5, False, INK_BODY)], PP_ALIGN.LEFT, 4),
], top_bar_color=NAVY, margin=0.12)

# Bottom Workflow
tb = s5.shapes.add_textbox(Inches(0.65), Inches(5.22), Inches(6.0), Inches(0.26))
write(tb.text_frame, [([R("END-TO-END EXECUTION WORKFLOW", 10.5, True, TEAL)],)])
w_steps = [
    "1. Patient Generates QR ID",
    "2. Bystander Scans QR (GPS SMS)",
    "3. ER Doctor Enters Name",
    "4. Allergies & Labs Loaded (<3s)",
    "5. Break-Glass Block Logged",
]
sw = 12.03 / 5
for k, st in enumerate(w_steps):
    shp = MSO_SHAPE.PENTAGON if k == 0 else MSO_SHAPE.CHEVRON
    sh = s5.shapes.add_shape(shp, Inches(0.65 + k * sw), Inches(5.52), Inches(sw + 0.04), Inches(0.58))
    sh.shadow.inherit = False
    sh.fill.solid()
    sh.fill.fore_color.rgb = NAVY if k % 2 == 0 else TEAL
    sh.line.fill.background()
    tf = sh.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.18)
    write(tf, [([R(st, 10.8, True, WHITE)], PP_ALIGN.CENTER)])

panel(s5, 0.65, 6.24, 12.03, 0.60, [([
    R("Implementation Status:  ", 12, True, NAVY),
    R("Working full-stack prototype built and tested with 17 modular route controllers, automated integration tests, and HL7 FHIR-aligned JSON schemas.",
      11.5, False, INK_BODY)
],)], fill=CARD_TINT, border=BORDER_GRAY, anchor=MSO_ANCHOR.MIDDLE, margin=0.12)


# ==============================================================================
# SLIDE 6: SECURITY COMPONENT
# ==============================================================================
s6 = prs.slides.add_slide(blank_layout)
add_header(
    s6, "05 · Security Component",
    "Defense-in-Depth Security, Privacy Controls & Cryptographic Accountability",
    "How E-Healthcare enables 3-second emergency access while strictly protecting patient privacy and preventing unauthorized snooping.",
    6
)

sec_cards = [
    ("01 · ROLE-SCOPED DATA MINIMIZATION", 0.65, 1.78,
     [("Server-Side Field Stripping: ", "Public QR endpoints never query or return diagnoses, prescriptions, or lab reports—only Name, Blood Group, and family SOS triggers."),
      ("Strict JWT Role Guards: ", "Full clinical dossiers (/api/doctors/patient-records) require a cryptographically signed clinician JWT (HS256) with verified role permissions."),
      ("Password & Session Hardening: ", "All user credentials are salted and hashed; API routes enforce strict schema validation and rate limiting.")]),

    ("02 · TAMPER-PROOF SHA-256 BREAK-GLASS LEDGER", 6.78, 1.78,
     [("Mandatory Clinical Justification: ", "Every emergency record lookup requires the clinician's identity, hospital name, and clinical reason for access."),
      ("Cryptographic Hash Chaining: ", "Each access writes an immutable block containing SHA-256(block_index + timestamp + doctor_id + patient_id + justification + previous_hash)."),
      ("Tamper Detection: ", "Any attempt to alter or delete a past access log invalidates the subsequent hash chain and is flagged immediately.")]),

    ("03 · REAL-TIME FAMILY TRANSPARENCY ALERTS", 0.65, 4.04,
     [("Instant SMS Notification to Family: ", "The moment an ER doctor unlocks a patient's record during an emergency, an automated SMS is sent to the family emergency contact."),
      ("Full Audit Visibility: ", "Patients can view a complete, human-readable log in their portal showing which doctor accessed their record, from which hospital, and why."),
      ("Deters Unauthorized Browsing: ", "Guaranteed real-time visibility stops curiosity lookups before they happen.")]),

    ("04 · GRANULAR CONSENT & DPDP ACT 2023 ALIGNMENT", 6.78, 4.04,
     [("Time-Bound Category Consent: ", "For non-emergency care, patients toggle access by category (medical history, lab reports, mental health, genetic data) with auto-expiring windows."),
      ("One-Click Revocation: ", "Patients can revoke any active doctor consent token immediately from their Sovereign Vault."),
      ("Legally Grounded (DPDP Act 2023, Sec. 7(d)): ", "Aligns with Indian law permitting data processing during a medical threat to life, paired with strict post-access accountability.")]),
]
for title, x, y, pts in sec_cards:
    paras = [([R(title, 11.8, True, TEAL)],)]
    for b, t in pts:
        paras.append(bullet(b, t, 11.0, 6))
    panel(s6, x, y, 5.90, 2.12, paras, top_bar_color=NAVY, margin=0.16)

panel(s6, 0.65, 6.28, 12.03, 0.58, [([
    R("Security Summary:  ", 12, True, NAVY),
    R("Public Bystander = Zero Medical History Exposed  |  ER Clinician = Instant Access + Mandatory SHA-256 Audit Block + Instant Family SMS Alert.",
      11.5, False, INK_DARK)
],)], fill=CARD_TINT, border=BORDER_GRAY, anchor=MSO_ANCHOR.MIDDLE, margin=0.12)

for out in (OUT_PPTX_WORKSPACE, OUT_PPTX_DOWNLOADS):
    prs.save(out)
    print("Saved:", out)
