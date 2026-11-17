"""Generates Team Proxy's Round 1 Idea Submission PPTX & PDF covering:
1. Problem Statement
2. Proposed Solution
3. Innovative Aspects
4. Implementation Approach
5. Security Component
6. Feasibility, Impact & Team Details (Yogeshwaran V M S, Sunku Joshika, Sampreetha S)
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

# Clean Clinical Dark Navy & Crisp Card Palette
BG_DARK = RGBColor(11, 19, 36)        # Deep Clinical Navy
BG_HEADER = RGBColor(16, 29, 54)      # Header Band Navy
CARD_BG = RGBColor(19, 33, 60)        # Card Surface
CARD_ALT = RGBColor(24, 43, 76)       # Highlight Card Surface
BORDER_SUBTLE = RGBColor(42, 67, 108) # Subtle Steel Border
CYAN = RGBColor(56, 201, 232)         # Clinical Teal / Cyan
LIME = RGBColor(190, 242, 100)        # Accent Lime Green
AMBER = RGBColor(251, 191, 36)        # Warning / Highlight Amber
CORAL = RGBColor(248, 113, 113)       # Emergency Red/Coral
WHITE = RGBColor(255, 255, 255)
TEXT_LIGHT = RGBColor(222, 231, 242)
TEXT_MUTED = RGBColor(156, 175, 201)


def R(text, size=12, bold=False, color=TEXT_LIGHT, italic=False):
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
    bg.fill.fore_color.rgb = BG_DARK
    bg.line.fill.background()
    bg.shadow.inherit = False
    # Top thin accent bar
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.07))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = CYAN
    top_bar.line.fill.background()
    top_bar.shadow.inherit = False


def add_header(slide, section_num, section_tag, title_text, subtitle_text, slide_no):
    add_bg(slide)
    # Section pill badge
    pill = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.55), Inches(0.32), Inches(3.65), Inches(0.34)
    )
    pill.adjustments[0] = 0.5
    pill.fill.solid()
    pill.fill.fore_color.rgb = CARD_ALT
    pill.line.color.rgb = CYAN
    pill.line.width = Pt(1)
    pill.shadow.inherit = False
    ptf = pill.text_frame
    ptf.vertical_anchor = MSO_ANCHOR.MIDDLE
    write(ptf, [([R(f"{section_num}  ·  {section_tag}", 10.5, True, CYAN)], PP_ALIGN.CENTER)])

    # Top-right metadata badge
    tb_meta = slide.shapes.add_textbox(Inches(8.5), Inches(0.32), Inches(4.28), Inches(0.34))
    mtf = tb_meta.text_frame
    mtf.vertical_anchor = MSO_ANCHOR.MIDDLE
    write(mtf, [([R("E-HEALTHCARE  |  TEAM PROXY  |  HEALTH TECH", 10, True, TEXT_MUTED)], PP_ALIGN.RIGHT)])

    # Main Title
    tb_t = slide.shapes.add_textbox(Inches(0.55), Inches(0.72), Inches(12.23), Inches(0.52))
    ttf = tb_t.text_frame
    ttf.word_wrap = True
    ttf.margin_left = ttf.margin_top = ttf.margin_bottom = 0
    write(ttf, [([R(title_text, 23, True, WHITE)],)])

    # Subtitle
    tb_s = slide.shapes.add_textbox(Inches(0.55), Inches(1.24), Inches(12.23), Inches(0.38))
    stf = tb_s.text_frame
    stf.word_wrap = True
    stf.margin_left = stf.margin_top = stf.margin_bottom = 0
    write(stf, [([R(subtitle_text, 13, False, TEXT_MUTED, True)],)])

    # Footer bar
    foot_line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.55), Inches(7.02), Inches(12.23), Inches(0.015)
    )
    foot_line.fill.solid()
    foot_line.fill.fore_color.rgb = BORDER_SUBTLE
    foot_line.line.fill.background()

    tb_f = slide.shapes.add_textbox(Inches(0.55), Inches(7.08), Inches(12.23), Inches(0.30))
    ftf = tb_f.text_frame
    ftf.margin_left = ftf.margin_right = 0
    write(ftf, [(
        [R("Round 1 Idea Submission  ·  New Horizon College of Engineering  ·  Team Proxy", 10, False, TEXT_MUTED),
         R(f"                                                                                                                Slide {slide_no} of 7", 10, True, CYAN)],
        PP_ALIGN.LEFT
    )])


def card(slide, x, y, w, h, paras, fill=CARD_BG, border=BORDER_SUBTLE, border_w=1.0,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, anchor=MSO_ANCHOR.TOP, margin=0.18, radius=0.04):
    sh = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        sh.adjustments[0] = radius
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
    tf.margin_top = tf.margin_bottom = Inches(margin * 0.8)
    write(tf, paras)
    return sh


def bullet(bold_lead, text, size=11.5, sb=6, bullet_color=CYAN):
    runs = [R("▪  ", size, True, bullet_color)]
    if bold_lead:
        runs.append(R(bold_lead, size, True, WHITE))
    runs.append(R(text, size, False, TEXT_LIGHT))
    return (runs, PP_ALIGN.LEFT, sb)


def arrow(slide, x, y, w=0.28, h=0.30, color=CYAN):
    a = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    a.shadow.inherit = False
    a.fill.solid()
    a.fill.fore_color.rgb = color
    a.line.fill.background()


# ==============================================================================
# SLIDE 1: TITLE & SUBMISSION OVERVIEW
# ==============================================================================
s1 = prs.slides.add_slide(blank_layout)
add_bg(s1)

# Top badge
card(s1, 0.70, 0.55, 4.30, 0.42, [
    ([R("ROUND 1 IDEA SUBMISSION  ·  HEALTH TECH TRACK", 11, True, CYAN)], PP_ALIGN.CENTER)
], fill=CARD_ALT, border=CYAN, anchor=MSO_ANCHOR.MIDDLE, radius=0.5)

# Main Title & Subtitle
tb1 = s1.shapes.add_textbox(Inches(0.70), Inches(1.18), Inches(11.9), Inches(1.65))
tf1 = tb1.text_frame
tf1.word_wrap = True
write(tf1, [
    ([R("E-HEALTHCARE", 42, True, WHITE)],),
    ([R("Instant, Privacy-Safe Emergency Medical Access & Vernacular Clinical Triage Platform", 20, True, CYAN)], PP_ALIGN.LEFT, 6),
    ([R("\"Delivering critical medical intelligence within the first 15 seconds of an emergency—without compromising patient privacy.\"",
       14, False, LIME, True)], PP_ALIGN.LEFT, 8),
])

# Left Box: Submission Scope (5 Evaluation Pillars)
scope_items = [
    ("01. Problem Statement: ", "Why life-saving medical data is unreachable during the Golden Hour."),
    ("02. Proposed Solution: ", "Three-tier emergency QR, doctor name-lookup & 6-language voice triage."),
    ("03. Innovative Aspects: ", "15-second Dual-Role Emergency Handshake & zero-OTP clinician access."),
    ("04. Implementation Approach: ", "FastAPI + SQLAlchemy + Bayesian triage + PDF lab biomarker parser."),
    ("05. Security Component: ", "Role-based data minimization, SHA-256 Break-Glass ledger & SMS alerts."),
]
s1_left = [([R("EVALUATION CRITERIA COVERED IN THIS DOCUMENT", 13, True, LIME)],)]
for b, t in scope_items:
    s1_left.append(bullet(b, t, 12, 8, CYAN))
card(s1, 0.70, 3.05, 6.85, 3.55, s1_left, fill=CARD_BG, border=CYAN, border_w=1.2)

# Right Box: Team Proxy Metadata
team_meta = [
    ([R("TEAM & INSTITUTION DETAILS", 13, True, LIME)],),
    ([R("Team Name:  ", 12.5, True, TEXT_MUTED), R("Team Proxy", 13, True, WHITE)], PP_ALIGN.LEFT, 10),
    ([R("Institution:  ", 12.5, True, TEXT_MUTED), R("New Horizon College of Engineering", 12.5, True, WHITE)], PP_ALIGN.LEFT, 6),
    ([R("Department:  ", 12.5, True, TEXT_MUTED), R("Artificial Intelligence & Machine Learning (AIML)", 12, False, TEXT_LIGHT)], PP_ALIGN.LEFT, 6),
    ([R("TEAM MEMBERS", 12, True, CYAN)], PP_ALIGN.LEFT, 14),
    bullet("Yogeshwaran V M S  —  ", "Team Lead & Full-Stack Architecture", 12, 6, LIME),
    bullet("Sunku Joshika  —  ", "ML & Clinical Intelligence Engine", 12, 6, LIME),
    bullet("Sampreetha S  —  ", "Backend APIs, Database & Security", 12, 6, LIME),
]
card(s1, 7.80, 3.05, 4.83, 3.55, team_meta, fill=CARD_ALT, border=LIME, border_w=1.2)

# Footer on Slide 1
tb_f1 = s1.shapes.add_textbox(Inches(0.70), Inches(6.95), Inches(11.9), Inches(0.35))
write(tb_f1.text_frame, [(
    [R("Working Prototype Built & Verified  ·  FastAPI + SQLite/PostgreSQL + Web Speech API + SHA-256 Break-Glass Audit", 11, False, TEXT_MUTED),
     R("                                                            Slide 1 of 7", 11, True, CYAN)],
)])


# ==============================================================================
# SLIDE 2: PROBLEM STATEMENT
# ==============================================================================
s2 = prs.slides.add_slide(blank_layout)
add_header(
    s2, "SECTION 01", "PROBLEM STATEMENT",
    "The Emergency Dead End: Why Medical History Is Missing When Seconds Count",
    "When an accident victim or acute patient arrives at an emergency room, the clinical facts needed to treat them safely are locked away.",
    2
)

# Top Scale Banner
card(s2, 0.55, 1.72, 12.23, 0.62, [([
    R("REAL-WORLD SCALE:  ", 12.5, True, CORAL),
    R("India recorded 4,61,312 road accidents and 1,68,491 deaths in 2022 (MoRTH). In critical trauma, treating a patient without knowing their blood group, allergies, or blood thinners leads to preventable complications during the Golden Hour.",
      12, False, WHITE)
],)], fill=CARD_ALT, border=CORAL, anchor=MSO_ANCHOR.MIDDLE)

# 3 Failure Point Columns
p_cols = [
    ("FAILURE POINT 01", "The Patient Cannot Speak", CORAL,
     "Physical & Medical Barrier",
     [("Unconscious or in shock: ", "Accident, stroke, or cardiac victims cannot state their blood group, severe drug allergies, or chronic conditions (diabetes, epilepsy, cardiac stents)."),
      ("No family contact at scene: ", "Good Samaritans and ambulance staff have no immediate way to identify or notify the patient's family.")]),

    ("FAILURE POINT 02", "The Phone & Apps Are Locked", AMBER,
     "Digital & Authentication Barrier",
     [("Locked smartphones: ", "99% of phones are secured by PINs or biometrics; emergency contacts and health cards stay trapped inside."),
      ("OTP & hash-code dead end: ", "Existing health portals and consent-first apps require the patient's own OTP, password, or 64-character access code—impossible when unconscious.")]),

    ("FAILURE POINT 03", "The Hospital Cannot Wait", CYAN,
     "Clinical Triage & Handover Barrier",
     [("Blind emergency treatment: ", "Doctors must act immediately; an unknown Penicillin allergy can trigger fatal anaphylaxis, and undisclosed blood thinners cause severe surgical bleeding."),
      ("Diagnostic & handover delays: ", "20–40 critical minutes are lost repeating baseline tests, and key details get lost during shift handovers.")]),
]
cw, gap = 3.91, 0.25
for i, (tag, title, col, sub, pts) in enumerate(p_cols):
    paras = [
        ([R(tag, 11, True, col)],),
        ([R(title, 15.5, True, WHITE)], PP_ALIGN.LEFT, 3),
        ([R(sub, 11, False, col, True)], PP_ALIGN.LEFT, 2),
    ]
    for b, t in pts:
        paras.append(bullet(b, t, 11.8, 8, col))
    card(s2, 0.55 + i * (cw + gap), 2.50, cw, 3.45, paras, border=col, border_w=1.2)

# Bottom Synthesis Banner
card(s2, 0.55, 6.12, 12.23, 0.72, [([
    R("CORE PROBLEM STATEMENT:  ", 13, True, LIME),
    R("There is currently no fast, privacy-safe mechanism that lets bystanders trigger emergency help AND lets verified ER doctors retrieve a patient's critical medical baseline in seconds without requiring OTPs or hash codes.",
      12.5, False, WHITE)
],)], fill=BG_HEADER, border=LIME, anchor=MSO_ANCHOR.MIDDLE)


# ==============================================================================
# SLIDE 3: PROPOSED SOLUTION
# ==============================================================================
s3 = prs.slides.add_slide(blank_layout)
add_header(
    s3, "SECTION 02", "PROPOSED SOLUTION",
    "E-Healthcare: Role-Based Emergency Medical Access & Vernacular Triage",
    "A unified web platform that delivers the exact right level of medical information to bystanders, ER clinicians, and patients.",
    3
)

sol_cols = [
    ("MODULE 01  ·  PUBLIC RESPONDER", "Lock-Screen Emergency QR", LIME,
     "For Bystanders at the Accident Scene (< 15 Seconds)",
     [("Zero App / Zero Login: ", "Anyone can scan the QR sticker on the patient's phone lock-screen, helmet, or college/office ID card using a standard camera."),
      ("Survival-Only View: ", "Displays ONLY Name, Age, Blood Group (e.g., O+ Positive), and one-touch emergency family call buttons."),
      ("1-Tap Live GPS SMS Alert: ", "Tapping 'Notify Family' dispatches an automated cellular SMS with a live Google Maps location link to family members."),
      ("Strict Privacy: ", "Zero diagnoses, prescriptions, or lab reports are ever shown to the public.")]),

    ("MODULE 02  ·  VERIFIED CLINICIAN", "Doctor Name-Based Lookup", CYAN,
     "For Paramedics & ER Doctors (< 3 Seconds)",
     [("No Hash Code or OTP Needed: ", "Verified doctors log into the hospital console and search directly by the patient's name, phone, or ID."),
      ("Critical Trauma Baseline: ", "Instantly surfaces Drug Allergies (Penicillin/Sulfa), Active High-Risk Meds (blood thinners, insulin), Implants, and Chronic Conditions."),
      ("Complete Clinical Dossier: ", "Provides latest vitals (BP, SpO2, HR, glucose), past consultations, active prescriptions, and uploaded lab reports."),
      ("SBAR Continuity: ", "Generates structured Situation-Background-Assessment-Recommendation handover notes.")]),

    ("MODULE 03  ·  PATIENT & FAMILY", "6-Language Voice & Lab AI", AMBER,
     "For Everyday Preventive & Diagnostic Care",
     [("Vernacular Voice Triage: ", "Patients speak or type symptoms in Tamil, Telugu, Kannada, Malayalam, Hindi, or English; our Bayesian engine predicts urgency and department."),
      ("Automated Lab Flagging: ", "Uploads of blood/scan reports (CBC, LFT, glucose, platelets) are parsed automatically to highlight abnormal biomarkers."),
      ("Family Dependent Vault: ", "Manage emergency profiles for elderly parents and children from a single account with granular consent controls.")]),
]
for i, (tag, title, col, sub, pts) in enumerate(sol_cols):
    paras = [
        ([R(tag, 10.5, True, col)],),
        ([R(title, 15, True, WHITE)], PP_ALIGN.LEFT, 3),
        ([R(sub, 11, False, col, True)], PP_ALIGN.LEFT, 2),
    ]
    for b, t in pts:
        paras.append(bullet(b, t, 11.3, 6, col))
    card(s3, 0.55 + i * (cw + gap), 1.72, cw, 4.25, paras, border=col, border_w=1.2)

card(s3, 0.55, 6.12, 12.23, 0.72, [([
    R("SOLUTION OUTCOME:  ", 13, True, LIME),
    R("Bridges pre-hospital rescue and hospital ER care—connecting bystander GPS alerts, 3-second doctor record retrieval by name, and vernacular patient triage in one cohesive platform.",
      12.5, False, WHITE)
],)], fill=BG_HEADER, border=LIME, anchor=MSO_ANCHOR.MIDDLE)


# ==============================================================================
# SLIDE 4: INNOVATIVE ASPECTS
# ==============================================================================
s4 = prs.slides.add_slide(blank_layout)
add_header(
    s4, "SECTION 03", "INNOVATIVE ASPECTS",
    "Core Innovations: Solving the Speed vs. Privacy Trade-Off in Emergencies",
    "Instead of forcing an all-or-nothing choice between open QR cards and locked portals, E-Healthcare introduces three practical innovations.",
    4
)

# Left Side: 3 Innovation Cards stacked
inno_items = [
    ("INNOVATION 01  ·  THE 15-SECOND DUAL-ROLE HANDSHAKE", LIME,
     "Same Patient Profile, Two Completely Separate Role Views: ",
     "When a stranger scans the QR code, our server returns only Blood Group and 1-tap GPS family calling (0% medical history leaked). When an authenticated ER doctor queries the patient, the server unlocks severe allergies, blood thinners, stents, and vitals."),
    ("INNOVATION 02  ·  ZERO-HASH, ZERO-OTP DOCTOR NAME LOOKUP", CYAN,
     "Decoupled from Patient Phone & Cryptographic Keys: ",
     "During trauma, patients cannot read out OTPs or 64-character SHA-256 hashes. We engineered a clinician directory resolver that lets verified ER doctors pull the full medical dossier simply by typing the patient's name—backed by automatic break-glass auditing."),
    ("INNOVATION 03  ·  VERNACULAR VOICE TRIAGE + LAB BIOMARKER AI", AMBER,
     "Inclusive Pre-Care & Rapid Diagnostic Parsing: ",
     "Combines 6-language speech-to-symptom intake (Tamil, Telugu, Kannada, Malayalam, Hindi, English) with automated regex/PDF biomarker extraction that flags critical platelet, WBC, hemoglobin, and glucose anomalies in seconds."),
]
for idx, (head, col, lead, body) in enumerate(inno_items):
    card(s4, 0.55, 1.72 + idx * 1.72, 6.15, 1.58, [
        ([R(head, 12, True, col)],),
        bullet(lead, body, 11.2, 5, col),
    ], border=col, border_w=1.2, margin=0.14)

# Right Side: Head-to-Head Differentiation Table
rows = [
    ("Evaluation Dimension", "Standard Health Apps / Static QR", "E-Healthcare Innovation"),
    ("Unconscious Patient Access", "Blocked by phone lock, OTP, or hash key", "15s QR scan + <3s Doctor lookup by Name"),
    ("Bystander Privacy Control", "Static QR exposes all conditions publicly", "Dual-Role Split View (Blood + SOS only)"),
    ("Clinician Accountability", "Unlogged or unverified record viewing", "Tamper-proof SHA-256 Break-Glass + SMS alert"),
    ("Regional Accessibility", "English-heavy forms & menus", "Voice triage in 6 Indian languages"),
    ("Lab Report Review in ER", "Manual reading of multi-page PDFs", "Automated critical biomarker flagging"),
    ("Inter-Shift Continuity", "Unstructured free-text doctor notes", "Built-in WHO SBAR handover generator"),
]
tbl_sh = s4.shapes.add_table(len(rows), 3, Inches(6.95), Inches(1.72), Inches(5.83), Inches(5.02))
tbl = tbl_sh.table
tbl.first_row = True
for ci, wdt in enumerate([1.68, 1.95, 2.20]):
    tbl.columns[ci].width = Inches(wdt)
for ri, row in enumerate(rows):
    tbl.rows[ri].height = Inches(0.56 if ri == 0 else 0.63)
    for ci, val in enumerate(row):
        cell = tbl.cell(ri, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = CARD_ALT if ri == 0 else (CARD_BG if ri % 2 == 1 else BG_HEADER)
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
            r.font.size, r.font.bold = Pt(11.5), True
            r.font.color.rgb = LIME if ci == 2 else WHITE
        else:
            r.font.size = Pt(10.8)
            r.font.bold = ci != 1
            r.font.color.rgb = CYAN if ci == 0 else (TEXT_MUTED if ci == 1 else WHITE)


# ==============================================================================
# SLIDE 5: IMPLEMENTATION APPROACH
# ==============================================================================
s5 = prs.slides.add_slide(blank_layout)
add_header(
    s5, "SECTION 04", "IMPLEMENTATION APPROACH",
    "System Architecture, Technology Stack & End-to-End Execution Pipeline",
    "Built as a modular, working full-stack web application using open-source technologies and standard clinical data models.",
    5
)

top_lbl = 1.72
bt, bh = 2.00, 3.05
mid = bt + bh / 2 - 0.15

# Stage 1: Client Portals
s5.shapes.add_textbox(Inches(0.55), Inches(top_lbl), Inches(2.40), Inches(0.26)).text_frame.paragraphs[0].text = ""
write(s5.shapes[-1].text_frame, [([R("1. CLIENT PORTALS", 11, True, LIME)],)])
c_boxes = [
    ("Public Emergency View", "Camera QR scan · HTML5 + GPS API · 0 install"),
    ("Doctor Trauma Console", "Name search · Dossier · SBAR · Vitals charts"),
    ("Patient & Family Portal", "6-language Web Speech API · Lab upload · QR"),
]
for j, (ct, cd) in enumerate(c_boxes):
    card(s5, 0.55, bt + j * 1.05, 2.40, 0.95, [
        ([R(ct, 11.8, True, WHITE)],),
        ([R(cd, 10.2, False, CYAN)], PP_ALIGN.LEFT, 3),
    ], anchor=MSO_ANCHOR.MIDDLE, margin=0.10)
arrow(s5, 3.01, mid)

# Stage 2: FastAPI Application Server
tb = s5.shapes.add_textbox(Inches(3.35), Inches(top_lbl), Inches(2.85), Inches(0.26))
write(tb.text_frame, [([R("2. API GATEWAY (FastAPI)", 11, True, LIME)],)])
card(s5, 3.35, bt, 2.85, bh, [
    ([R("Python 3.11 + FastAPI", 13, True, LIME)],),
    ([R("Async Uvicorn ASGI Server", 10.5, False, CYAN, True)], PP_ALIGN.LEFT, 2),
    bullet("REST Endpoints: ", "/api/doctors/patient-records, /api/emergency/live-passport, /api/blockchain/break-glass.", 10.8, 7),
    bullet("Pydantic Schemas: ", "Strict request/response validation mapped to HL7 FHIR R4 concepts.", 10.8, 6),
    bullet("Sub-50ms Name Search: ", "Case-insensitive tokenized ILIKE resolver across Patient & Family tables.", 10.8, 6),
], border=CYAN)
arrow(s5, 6.26, mid)

# Stage 3: Core Intelligence & Clinical Engines
tb = s5.shapes.add_textbox(Inches(6.60), Inches(top_lbl), Inches(3.65), Inches(0.26))
write(tb.text_frame, [([R("3. CLINICAL & ML ENGINES", 11, True, LIME)],)])
eng_boxes = [
    ("Bayesian Symptom Triage Engine", "Computes posterior disease & urgency probabilities across 6 languages."),
    ("Diagnostic Lab Report Parser", "Extracts CBC, platelet, WBC, Hb & glucose values from PDFs/text & flags anomalies."),
    ("SBAR & Vitals Grading Engine", "Generates structured handover notes & grades BP/SpO2/HR for shock alerts."),
]
for j, (et, ed) in enumerate(eng_boxes):
    card(s5, 6.60, bt + j * 1.05, 3.65, 0.95, [
        ([R(et, 11.8, True, LIME if j == 0 else CYAN)],),
        ([R(ed, 10.2, False, TEXT_LIGHT)], PP_ALIGN.LEFT, 3),
    ], fill=CARD_ALT if j == 0 else CARD_BG, anchor=MSO_ANCHOR.MIDDLE, margin=0.10)
arrow(s5, 10.31, mid)

# Stage 4: Data & External Services
tb = s5.shapes.add_textbox(Inches(10.65), Inches(top_lbl), Inches(2.13), Inches(0.26))
write(tb.text_frame, [([R("4. DATA & SMS LAYER", 11, True, LIME)],)])
card(s5, 10.65, bt, 2.13, 1.46, [
    ([R("Relational DB", 12, True, LIME)],),
    ([R("PostgreSQL / SQLite via SQLAlchemy 2.0 ORM with ACID transactions & audit tables.", 10.5, False, TEXT_LIGHT)], PP_ALIGN.LEFT, 4),
])
card(s5, 10.65, bt + 1.59, 2.13, 1.46, [
    ([R("Live Gateways", 12, True, LIME)],),
    ([R("Fast2SMS cellular API for GPS family alerts + APScheduler for medication reminders.", 10.5, False, TEXT_LIGHT)], PP_ALIGN.LEFT, 4),
])

# Bottom Implementation Workflow Bar
tb = s5.shapes.add_textbox(Inches(0.55), Inches(5.22), Inches(6.0), Inches(0.26))
write(tb.text_frame, [([R("END-TO-END IMPLEMENTATION WORKFLOW (PROTOTYPE VERIFIED)", 11, True, LIME)],)])
w_steps = [
    "1. Patient Registers & Generates QR",
    "2. Bystander Scans QR (GPS SMS Sent)",
    "3. ER Doctor Enters Patient Name",
    "4. Allergies, Meds & Labs Loaded (<3s)",
    "5. Break-Glass Block & Family Alert Logged",
]
sw = 12.23 / 5
for k, st in enumerate(w_steps):
    shp = MSO_SHAPE.PENTAGON if k == 0 else MSO_SHAPE.CHEVRON
    card(s5, 0.55 + k * sw, 5.52, sw + 0.04, 0.62,
         [([R(st, 10.8, True, WHITE if k % 2 == 0 else BG_DARK)], PP_ALIGN.CENTER)],
         shape=shp, fill=CARD_ALT if k % 2 == 0 else CYAN, border=None, anchor=MSO_ANCHOR.MIDDLE, margin=0.20)

card(s5, 0.55, 6.26, 12.23, 0.58, [([
    R("Prototype Status:  ", 12, True, LIME),
    R("Fully functional full-stack codebase with 17 modular route controllers, automated integration tests, and FHIR-compatible JSON payloads.",
      11.8, False, WHITE)
],)], fill=BG_HEADER, border=BORDER_SUBTLE, anchor=MSO_ANCHOR.MIDDLE)


# ==============================================================================
# SLIDE 6: SECURITY COMPONENT
# ==============================================================================
s6 = prs.slides.add_slide(blank_layout)
add_header(
    s6, "SECTION 05", "SECURITY COMPONENT",
    "Defense-in-Depth Security, Privacy Controls & Cryptographic Accountability",
    "How E-Healthcare enables 3-second emergency access while strictly protecting patient privacy and preventing unauthorized snooping.",
    6
)

sec_cards = [
    ("SECURITY PILLAR 01  ·  ROLE-SCOPED DATA MINIMIZATION", LIME, 0.55, 1.72,
     [("Server-Side Field Stripping: ", "Public QR endpoints never query or return diagnoses, prescriptions, or lab reports—only Name, Blood Group, and family SOS triggers."),
      ("Strict JWT Role Guards: ", "Full clinical dossiers (/api/doctors/patient-records) require a cryptographically signed clinician JWT (HS256) with verified role permissions."),
      ("Password & Session Hardening: ", "All user credentials are salted and hashed; API routes enforce strict schema validation and rate limiting.")]),

    ("SECURITY PILLAR 02  ·  TAMPER-PROOF SHA-256 BREAK-GLASS LEDGER", CYAN, 6.78, 1.72,
     [("Mandatory Clinical Justification: ", "Every emergency record lookup requires the clinician's identity, hospital name, and clinical reason for access."),
      ("Cryptographic Hash Chaining: ", "Each access writes an immutable block containing SHA-256(block_index + timestamp + doctor_id + patient_id + justification + previous_hash)."),
      ("Tamper Detection: ", "Any attempt to alter or delete a past access log invalidates the subsequent hash chain and is flagged immediately.")]),

    ("SECURITY PILLAR 03  ·  REAL-TIME FAMILY TRANSPARENCY ALERTS", AMBER, 0.55, 4.02,
     [("Instant SMS Notification to Patient/Family: ", "The moment an ER doctor unlocks a patient's record during an emergency, an automated SMS is sent to the family emergency contact."),
      ("Full Audit Visibility: ", "Patients can view a complete, human-readable log in their portal showing which doctor accessed their record, from which hospital, and why."),
      ("Deters Unauthorized Browsing: ", "Guaranteed real-time visibility stops curiosity lookups before they happen.")]),

    ("SECURITY PILLAR 04  ·  GRANULAR CONSENT & DPDP ACT 2023 ALIGNMENT", CORAL, 6.78, 4.02,
     [("Time-Bound Category Consent: ", "For non-emergency care, patients toggle access by category (medical history, lab reports, mental health, genetic data) with auto-expiring windows."),
      ("One-Click Revocation: ", "Patients can revoke any active doctor consent token immediately from their Sovereign Vault."),
      ("Legally Grounded (DPDP Act 2023, Sec. 7(d)): ", "Aligns with Indian law permitting data processing during a medical threat to life, paired with strict post-access accountability.")]),
]
for title, col, x, y, pts in sec_cards:
    paras = [([R(title, 12.2, True, col)],)]
    for b, t in pts:
        paras.append(bullet(b, t, 11.0, 5, col))
    card(s6, x, y, 6.00, 2.16, paras, border=col, border_w=1.2, margin=0.14)

card(s6, 0.55, 6.28, 12.23, 0.58, [([
    R("SECURITY SUMMARY:  ", 12, True, LIME),
    R("Public Bystander = Zero Medical History Exposed  |  ER Clinician = Instant Access + Mandatory SHA-256 Audit Block + Instant Family SMS Alert.",
      11.8, False, WHITE)
],)], fill=BG_HEADER, border=LIME, anchor=MSO_ANCHOR.MIDDLE)


# ==============================================================================
# SLIDE 7: FEASIBILITY, IMPACT & TEAM DETAILS
# ==============================================================================
s7 = prs.slides.add_slide(blank_layout)
add_header(
    s7, "SECTION 06", "FEASIBILITY, IMPACT & TEAM DETAILS",
    "Practical Deployment Roadmap, Measurable Impact & Team Proxy",
    "A low-cost, immediately deployable solution built by an interdisciplinary AIML engineering team.",
    7
)

# Top Row: 3 Cards (Feasibility, Impact, Adoption Roadmap)
top_cards = [
    ("DEPLOYMENT FEASIBILITY", LIME,
     [("Zero Special Hardware: ", "Works on any smartphone browser; printed QR stickers cost < ₹5 per citizen."),
      ("Free Basic Access for Citizens: ", "Supported by a proposed ₹15,000/month Hospital ER subscription and ₹99/year campus safety plans."),
      ("Offline Cellular Fallback: ", "Family SOS uses standard cellular SMS with GPS coordinates, working even in weak data zones.")]),

    ("CLINICAL & SOCIAL IMPACT", CYAN,
     [("Saves Golden Hour Minutes: ", "Eliminates blind treatment by surfacing fatal drug allergies and blood thinners in < 3 seconds."),
      ("Protects Vulnerable Groups: ", "Empowers solo commuters, elderly citizens, and chronic patients with a 15-second safety net."),
      ("Breaks Language Barriers: ", "6-language voice triage makes digital healthcare accessible across diverse regional populations.")]),

    ("PHASED ROLLOUT PLAN", AMBER,
     [("Phase 1 – Campus Pilot: ", "Deploy QR emergency IDs across students at New Horizon College of Engineering."),
      ("Phase 2 – Hospital ER Pilot: ", "Partner with multi-specialty hospital ERs in Bengaluru & Chennai to evaluate clinician name-lookup."),
      ("Phase 3 – ABDM & Fleet Scale: ", "Integrate with ambulance operators and HL7 FHIR R4 / ABDM national interfaces.")]),
]
for i, (head, col, pts) in enumerate(top_cards):
    paras = [([R(head, 12.5, True, col)],)]
    for b, t in pts:
        paras.append(bullet(b, t, 10.8, 5, col))
    card(s7, 0.55 + i * (cw + gap), 1.72, cw, 2.25, paras, border=col, border_w=1.2, margin=0.14)

# Bottom Half: Team Details Table
tb_team = s7.shapes.add_textbox(Inches(0.55), Inches(4.10), Inches(12.23), Inches(0.32))
write(tb_team.text_frame, [([
    R("TEAM DETAILS  —  TEAM PROXY  (NEW HORIZON COLLEGE OF ENGINEERING)", 13, True, LIME)
],)])

team_rows = [
    ("ROLE", "TEAM MEMBER NAME", "STREAM / DEPT", "YEAR", "CORE CONTRIBUTION IN E-HEALTHCARE"),
    ("Team Lead & Full-Stack Architect", "Yogeshwaran V M S", "B.E. — AIML", "3rd Year",
     "System architecture, 15-second Dual-Role QR Handshake, Doctor Name-Lookup console & UI integration"),
    ("Machine Learning & Clinical AI", "Sunku Joshika", "B.E. — AIML", "3rd Year",
     "Bayesian multi-symptom triage engine, 6-language voice workflow & automated lab report biomarker parser"),
    ("Backend, Database & Security", "Sampreetha S", "B.E. — AIML", "3rd Year",
     "FastAPI REST services, SQLAlchemy database models, JWT role guards & SHA-256 Break-Glass audit ledger"),
]
t_sh = s7.shapes.add_table(len(team_rows), 5, Inches(0.55), Inches(4.46), Inches(12.23), Inches(2.38))
tt = t_sh.table
tt.first_row = True
for ci, wdt in enumerate([2.55, 2.15, 1.45, 1.05, 5.03]):
    tt.columns[ci].width = Inches(wdt)
for ri, row in enumerate(team_rows):
    tt.rows[ri].height = Inches(0.46 if ri == 0 else 0.64)
    for ci, val in enumerate(row):
        cell = tt.cell(ri, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = CARD_ALT if ri == 0 else (CARD_BG if ri % 2 == 1 else BG_HEADER)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = cell.margin_right = Inches(0.10)
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = ""
        p.alignment = PP_ALIGN.CENTER if ci in (2, 3) else PP_ALIGN.LEFT
        r = p.add_run()
        r.text = val
        r.font.name = FONT
        if ri == 0:
            r.font.size, r.font.bold = Pt(11.2), True
            r.font.color.rgb = LIME
        else:
            r.font.size = Pt(11.2 if ci < 4 else 10.6)
            r.font.bold = ci in (0, 1)
            r.font.color.rgb = CYAN if ci == 0 else (WHITE if ci == 1 else TEXT_LIGHT)

for out in (OUT_PPTX_WORKSPACE, OUT_PPTX_DOWNLOADS):
    prs.save(out)
    print("Saved:", out)
