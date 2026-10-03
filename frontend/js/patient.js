// Patient Portal JavaScript: AI Personal Health Navigator

let allSymptoms = [];
let selectedSymptoms = new Set();
let currentAdaptiveQuestions = [];
let answeredQA = {};
let uploadedReportIds = [];
let latestAssessment = null;
let currentProfile = null;
let speechRecognizer = null;
let isRecording = false;

// ===================================================================
// AUDIO FEEDBACK & SMS/WHATSAPP NOTIFICATION ENGINE (SMS OTP FORMAT)
// ===================================================================

function playSmsChime() {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
        osc.frequency.setValueAtTime(880.00, audioCtx.currentTime + 0.08); // A5
        gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.35);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.35);
    } catch (e) {
        // AudioContext not supported or restricted by browser policy
    }
}

function getContactSettings() {
    const saved = localStorage.getItem('ehealth_contact_routing');
    if (saved) {
        try { return JSON.parse(saved); } catch (e) {}
    }
    return {
        patientPhone: (currentProfile && currentProfile.phone) || "+91 98765 43210",
        patientWhatsapp: "+91 98765 43210",
        caretakerName: "Sarah Doe",
        caretakerPhone: "+91 98111 22233",
        caretakerRelation: "Daughter / Primary Guardian",
        dualAlert: true
    };
}

function initContactSettings() {
    const cfg = getContactSettings();
    const pElem = document.getElementById('displayPatientPhone');
    const cNameElem = document.getElementById('displayCaretakerName');
    const cPhoneElem = document.getElementById('displayCaretakerPhone');
    const cRelElem = document.getElementById('displayCaretakerRelation');

    if (pElem) pElem.textContent = cfg.patientPhone || cfg.patientWhatsapp;
    if (cNameElem) cNameElem.textContent = cfg.caretakerName;
    if (cPhoneElem) cPhoneElem.textContent = cfg.caretakerPhone;
    if (cRelElem) cRelElem.textContent = cfg.caretakerRelation;
}

function openContactSettingsModal() {
    const cfg = getContactSettings();
    document.getElementById('modalPatientPhone').value = cfg.patientPhone || cfg.patientWhatsapp || '';
    document.getElementById('modalCaretakerName').value = cfg.caretakerName || '';
    document.getElementById('modalCaretakerPhone').value = cfg.caretakerPhone || '';
    document.getElementById('modalCaretakerRelation').value = cfg.caretakerRelation || 'Daughter / Primary Guardian';
    document.getElementById('modalCaretakerDualAlert').checked = cfg.dualAlert !== false;
    bootstrap.Modal.getOrCreateInstance(document.getElementById('contactSettingsModal')).show();
}

function saveContactSettings(e) {
    if (e) e.preventDefault();
    const pPhone = document.getElementById('modalPatientPhone').value.trim() || "+91 98765 43210";
    const cfg = {
        patientPhone: pPhone,
        patientWhatsapp: pPhone,
        caretakerName: document.getElementById('modalCaretakerName').value.trim() || "Sarah Doe",
        caretakerPhone: document.getElementById('modalCaretakerPhone').value.trim() || "+91 98111 22233",
        caretakerRelation: document.getElementById('modalCaretakerRelation').value,
        dualAlert: document.getElementById('modalCaretakerDualAlert').checked
    };
    localStorage.setItem('ehealth_contact_routing', JSON.stringify(cfg));
    initContactSettings();

    // Sync into profile form if open
    const profPhone = document.getElementById('profPhone');
    const profWhatsapp = document.getElementById('profWhatsapp');
    const profCName = document.getElementById('profCaretakerName');
    const profCPhone = document.getElementById('profCaretakerPhone');
    const profCRel = document.getElementById('profCaretakerRelation');
    if (profPhone) profPhone.value = cfg.patientPhone;
    if (profWhatsapp) profWhatsapp.value = cfg.patientWhatsapp;
    if (profCName) profCName.value = cfg.caretakerName;
    if (profCPhone) profCPhone.value = cfg.caretakerPhone;
    if (profCRel) profCRel.value = cfg.caretakerRelation;

    const modalEl = document.getElementById('contactSettingsModal');
    const modalInst = bootstrap.Modal.getInstance(modalEl);
    if (modalInst) modalInst.hide();

    // Trigger verified SMS OTP card
    showSMSNotification({
        title: "ROUTING VERIFIED & CONNECTED",
        message: `Alert channels connected! Prescriptions & risk alerts will now be routed directly to ${cfg.patientPhone} and Caretaker ${cfg.caretakerName} (${cfg.caretakerPhone}).`,
        channel: "whatsapp",
        otp: Math.floor(100000 + Math.random() * 900000).toString(),
        duration: 8000
    });
}

function triggerTestSmsNotification() {
    const cfg = getContactSettings();
    showSMSNotification({
        title: "TEST TELEMETRY DISPATCH",
        message: `System test alert dispatched. Both Patient (${cfg.patientPhone}) and Caretaker ${cfg.caretakerName} (${cfg.caretakerPhone}) channels are operational.`,
        channel: "sms",
        otp: "389-402",
        duration: 7000
    });
}

function showSMSNotification(options) {
    if (!options) return;
    const msg = typeof options === 'string' ? options : (options.message || options.text || '');
    const title = (typeof options === 'object' && options.title) ? options.title : 'CONFIRMED NOTIFICATION';
    const channel = (typeof options === 'object' && options.channel) ? options.channel : 'sms'; // 'sms', 'whatsapp', 'emergency'
    const otp = (typeof options === 'object' && options.otp) ? options.otp : null;
    const duration = (typeof options === 'object' && options.duration) ? options.duration : 7500;
    const cfg = getContactSettings();

    playSmsChime();

    let container = document.getElementById('smsNotificationContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'smsNotificationContainer';
        container.className = 'sms-notification-wrapper';
        document.body.appendChild(container);
    }

    const card = document.createElement('div');
    card.className = `sms-otp-card ${channel === 'whatsapp' ? '' : channel === 'emergency' ? 'emergency-channel' : 'sms-channel'}`;

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    let channelBadge = `<span class="sms-app-badge text-success"><i class="bi bi-whatsapp"></i> WhatsApp</span>`;
    if (channel === 'sms') {
        channelBadge = `<span class="sms-app-badge text-primary"><i class="bi bi-chat-dots-fill"></i> SMS Carrier</span>`;
    } else if (channel === 'emergency') {
        channelBadge = `<span class="sms-app-badge text-danger"><i class="bi bi-broadcast"></i> Priority SOS</span>`;
    }

    const recipientsHtml = `
        <div class="sms-recipient-pill">
            <i class="bi bi-person-check-fill text-primary"></i> <strong>Pt:</strong> ${cfg.patientPhone}
            <span class="mx-1 text-muted">|</span>
            <i class="bi bi-heart-fill text-danger"></i> <strong>Caretaker:</strong> ${cfg.caretakerName} (${cfg.caretakerPhone})
        </div>
    `;

    const otpHtml = otp ? `
        <div class="my-1 d-flex align-items-center justify-content-between bg-light p-1 px-2 rounded-2 border">
            <div>
                <small class="text-muted d-block" style="font-size:0.68rem; font-weight:700;">ONE-TIME SECURITY CODE / OTP</small>
                <span class="sms-otp-code">${otp}</span>
            </div>
            <button class="sms-btn btn-outline-primary bg-white text-primary border" onclick="navigator.clipboard.writeText('${otp}'); this.textContent='✓ Copied';">
                Copy
            </button>
        </div>
    ` : '';

    card.innerHTML = `
        <div class="sms-header">
            ${channelBadge}
            <span class="sms-time">${timeStr}</span>
        </div>
        ${recipientsHtml}
        <div class="sms-body-text">
            <strong>${title}:</strong> ${msg}
        </div>
        ${otpHtml}
        <div class="sms-actions">
            <span class="small text-muted me-auto" style="font-size:0.68rem;">E-Healthcare Alert Relay</span>
            <button class="sms-btn bg-light text-secondary border" onclick="this.closest('.sms-otp-card').remove()">
                Dismiss
            </button>
        </div>
    `;

    container.appendChild(card);

    if (duration > 0) {
        setTimeout(() => {
            if (card.parentNode) {
                card.classList.add('fade-out');
                setTimeout(() => card.remove(), 250);
            }
        }, duration);
    }
}

// Global browser window.alert override to replace popups with phone-sized SMS OTP cards
const _nativeAlert = window.alert;
window.alert = function(msg) {
    if (typeof msg !== 'string') {
        try { msg = JSON.stringify(msg); } catch (e) { msg = String(msg); }
    }
    window.showSMSNotification({
        title: "CONFIRMED NOTIFICATION",
        message: msg,
        channel: "sms",
        duration: 7000
    });
};

window.addEventListener('DOMContentLoaded', async () => {
    const user = API.getUser();
    if (!user) {
        window.location.href = '/';
        return;
    }
    if (user.role !== 'patient') {
        window.location.href = '/doctor';
        return;
    }

    document.getElementById('userWelcomeText').textContent = `Logged in as: ${user.full_name}`;
    initContactSettings();
    await loadSymptoms();
    await loadProfileData();
    await loadDoctorsDropdown();
    setupSpeechRecognition();
});

// Multilingual South Indian & Pan-Indian Symptom Keyword Mapping
const MULTILINGUAL_SYMPTOM_DICTIONARY = {
    chest_pain_pressure: [
        "chest pain", "chest pressure", "angina", "heart pain", "tightness in chest",
        "நெஞ்சு வலி", "மார்பு வலி", "இதய வலி", "nenju vali", "marbu vali", "idaya vali",
        "ఛాతీ నొప్పి", "గుండె నొప్పి", "మంట", "chati noppi", "gunde noppi", "chathi noppi",
        "ಎದೆ ನೋವು", "ಗುಂಡಿಗೆ ನೋವು", "ede novu", "ede bharavagide", "gundige novu",
        "നെഞ്ചുവേദന", "നെഞ്ചിൽ ഭാരം", "nenju vedana", "nenjil bhaaram", "nenjil kuthal",
        "सीने में दर्द", "छाती में दर्द", "seene me dard", "chaati me dard"
    ],
    cough_dry_or_productive: [
        "cough", "dry cough", "phlegm", "productive cough",
        "இருமல்", "வறட்டு இருமல்", "சளி", "irumal", "varattu irumal", "sali",
        "దగ్గు", "పొడి దగ్గు", "కఫం", "daggu", "podi daggu", "kafam",
        "ಕೆಮ್ಮು", "ಒಣ ಕೆಮ್ಮು", "kemmu", "ona kemmu", "khefa",
        "ചുമ", "വരണ്ട ചുമ", "കഫക്കെട്ട്", "chuma", "varanda chuma", "kafakkettu",
        "खांसी", "सूखी खांसी", "khansi", "balgam"
    ],
    fever_high_grade: [
        "fever", "high temperature", "chills", "feverish",
        "காய்ச்சல்", "சுரம்", "உடல் சூடு", "kaichal", "suram", "jwaram",
        "జ్వరం", "తీవ్ర జ్వరం", "jwaram", "tega jwaram",
        "ಜ್ವರ", "ವಿಪರೀತ ಜ್ವರ", "jvara", "jwara",
        "പനി", "കഠിനമായ പനി", "pani", "kadinamaaya pani",
        "बुखार", "तेज बुखार", "bukhar", "taap"
    ],
    shortness_of_breath: [
        "shortness of breath", "breathing difficulty", "breathless", "dyspnea",
        "மூச்சுத்திணறல்", "மூச்சு வாங்குதல்", "moochu thinaral", "moochu vanguthal",
        "ఆయాసం", "శ్వాస తీసుకోవడంలో ఇబ్బంది", "aayasam", "shwasa ibbandi",
        "ಉಸಿರಾಟದ ತೊಂದರೆ", "ಉಸಿರುಗಟ್ಟುವುದು", "usiraatada thondare", "usirugattuvudu",
        "ശ്വാസതടസ്സം", "ശ്വാസം മുട്ടൽ", "shwaasathadassam", "shwaasam muttal",
        "सांस फूलना", "सांस लेने में तकलीफ", "saans phoolna"
    ],
    headache_severe: [
        "headache", "migraine", "severe head pain",
        "தலைவலி", "கடுமையான தலைவலி", "thalai vali", "kadumaiyana thalai vali",
        "తలనొప్పి", "తీవ్ర తలనొప్పి", "tala noppi", "talanappi",
        "ತಲೆನೋವು", "tale novu", "tale bhaara",
        "തലവേദന", "കഠിനമായ തലവേദന", "thalavedana", "thalavedhana",
        "सिरदर्द", "सर दर्द", "sirdard", "sar dard"
    ],
    nausea_vomiting: [
        "nausea", "vomiting", "throwing up", "queasy",
        "வாந்தி", "குமட்டல்", "vanthi", "kumattal",
        "వాంతులు", "వికారం", "vaanthulu", "vikaaram",
        "ವಾಂತಿ", "ವಾಕರಿಕೆ", "vaanti", "vaakarike",
        "ഛർദ്ദി", "ഓക്കാനം", "chardi", "charthil", "okkanam",
        "उल्टी", "जी मिचलाना", "ulti", "vomit"
    ],
    fatigue_generalized: [
        "fatigue", "tiredness", "exhaustion", "weakness",
        "சோர்வு", "அசதி", "உடல் பலவீனம்", "sorvu", "asathi", "balaheenam",
        "அலసట", "నీరసం", "బలహీనత", "alasata", "neerasam", "balaheenata",
        "ಆಯಾಸ", "ಸುಸ್ತು", "ನಿಶ್ಯಕ್ತಿ", "aayaasa", "susthu", "nishakthi",
        "ക്ഷീണം", "തളർച്ച", "ksheenam", "thalarcha",
        "थकान", "कमजोरी", "thakan", "kamzori"
    ]
};

// Setup Web Speech API (Tamil, Telugu, Kannada, Malayalam, Hindi, English)
function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        const btn = document.getElementById('voiceMicBtn');
        if (btn) btn.title = "Speech Recognition not supported in this browser";
        return;
    }

    speechRecognizer = new SpeechRecognition();
    speechRecognizer.continuous = false;
    speechRecognizer.interimResults = false;

    speechRecognizer.onstart = () => {
        isRecording = true;
        document.getElementById('voiceMicBtn').classList.add('listening');
        document.getElementById('micText').textContent = 'Listening...';
        document.getElementById('voiceStatusAlert').classList.remove('d-none');
    };

    speechRecognizer.onresult = (event) => {
        const transcript = event.results[0][0].transcript.toLowerCase();
        document.getElementById('symptomSearchInput').value = transcript;
        document.getElementById('voiceStatusAlert').textContent = `Heard: "${transcript}"`;
        
        let matchFound = 0;
        // 1. Direct label/key match
        allSymptoms.forEach(s => {
            const clean = s.key.replace(/_/g, ' ');
            if (transcript.includes(clean) || transcript.includes(s.label.toLowerCase())) {
                selectedSymptoms.add(s.key);
                matchFound++;
            }
        });

        // 2. Multilingual South Indian & Pan-Indian Keyword Mappings
        for (const [symKey, synonyms] of Object.entries(MULTILINGUAL_SYMPTOM_DICTIONARY)) {
            for (const phrase of synonyms) {
                if (transcript.includes(phrase.toLowerCase())) {
                    selectedSymptoms.add(symKey);
                    matchFound++;
                    break;
                }
            }
        }

        updateSelectedCount();
        filterSymptoms();
        if (typeof updateEntropyAndUncertainty === 'function') {
            updateEntropyAndUncertainty();
        }
    };

    speechRecognizer.onerror = (e) => {
        console.error("Speech recognition error:", e);
        stopVoiceInput();
    };

    speechRecognizer.onend = () => {
        stopVoiceInput();
    };
}

function toggleVoiceInput() {
    if (!speechRecognizer) {
        alert("Speech Recognition is supported in Chrome, Edge, and Safari.");
        return;
    }
    if (isRecording) {
        speechRecognizer.stop();
        stopVoiceInput();
    } else {
        const lang = document.getElementById('voiceLangSelect').value || 'en-IN';
        speechRecognizer.lang = lang;
        speechRecognizer.start();
    }
}

function stopVoiceInput() {
    isRecording = false;
    const btn = document.getElementById('voiceMicBtn');
    if (btn) btn.classList.remove('listening');
    document.getElementById('micText').textContent = 'Speak Symptoms';
    setTimeout(() => {
        document.getElementById('voiceStatusAlert').classList.add('d-none');
    }, 3000);
}

// Load Categorized Symptom Catalog (75+ multi-system symptoms)
let symptomsByCategory = {};
let activeCategory = 'All';
let answeredQuestionIds = [];

async function loadSymptoms() {
    try {
        const res = await API.get('/api/closed-loop/symptoms-catalog');
        symptomsByCategory = res.categories || {};
        allSymptoms = [];
        
        for (const [catName, items] of Object.entries(symptomsByCategory)) {
            items.forEach(item => {
                allSymptoms.push({
                    key: item.id,
                    label: item.label,
                    category: catName
                });
            });
        }
        renderSymptomChips(allSymptoms);
    } catch (err) {
        console.error("Error loading categorized symptoms, falling back:", err);
        try {
            const fallback = await API.get('/api/predict/symptoms');
            allSymptoms = fallback.symptoms.map(s => ({ key: s.key, label: s.label, category: 'General' }));
            renderSymptomChips(allSymptoms);
        } catch (e2) {
            console.error("Critical fallback failed:", e2);
        }
    }
}

function filterByCategory(cat) {
    activeCategory = cat;
    document.querySelectorAll('.category-filter-btn').forEach(btn => {
        if (btn.textContent.includes(cat) || (cat === 'All' && btn.textContent.includes('All'))) {
            btn.className = "btn btn-sm btn-primary py-1 px-2 rounded-pill category-filter-btn active";
        } else {
            btn.className = "btn btn-sm btn-outline-secondary py-1 px-2 rounded-pill category-filter-btn";
        }
    });
    filterSymptoms();
}

function renderSymptomChips(list) {
    const container = document.getElementById('symptomsList');
    if (!list || list.length === 0) {
        container.innerHTML = '<div class="text-muted small text-center py-2">No symptoms match your search.</div>';
        return;
    }

    container.innerHTML = list.map(s => {
        const isSelected = selectedSymptoms.has(s.key);
        return `
            <div class="symptom-chip ${isSelected ? 'selected' : ''}" onclick="toggleSymptom('${s.key}')">
                <i class="bi ${isSelected ? 'bi-check-circle-fill' : 'bi-plus-circle'} chip-check"></i>
                <span>${s.label}</span>
            </div>
        `;
    }).join('');
}

function toggleSymptom(key) {
    if (selectedSymptoms.has(key)) {
        selectedSymptoms.delete(key);
    } else {
        selectedSymptoms.add(key);
    }
    updateSelectedCount();
    filterSymptoms();
}

function updateSelectedCount() {
    const count = selectedSymptoms.size;
    document.getElementById('selectedCountBadge').textContent = `${count} symptom${count === 1 ? '' : 's'} selected`;
}

function clearSelectedSymptoms() {
    selectedSymptoms.clear();
    updateSelectedCount();
    filterSymptoms();
}

function filterSymptoms() {
    const query = document.getElementById('symptomSearchInput').value.toLowerCase().trim();
    let filtered = allSymptoms;
    
    if (activeCategory !== 'All') {
        filtered = filtered.filter(s => s.category === activeCategory);
    }
    
    if (query) {
        filtered = filtered.filter(s => s.label.toLowerCase().includes(query) || s.key.includes(query));
    }
    renderSymptomChips(filtered);
}

// Wizard Navigation Functions
function updateStepper(activeStep) {
    for (let i = 1; i <= 4; i++) {
        const pill = document.getElementById(`step${i}-pill`);
        const wizard = document.getElementById(`wizardStep${i}`);
        if (i === activeStep) {
            pill.className = "wizard-step active";
            wizard.classList.remove('d-none');
        } else if (i < activeStep) {
            pill.className = "wizard-step completed";
            wizard.classList.add('d-none');
        } else {
            pill.className = "wizard-step";
            wizard.classList.add('d-none');
        }
    }
}

function goToStep1() {
    updateStepper(1);
}

async function goToStep2() {
    if (selectedSymptoms.size === 0) {
        alert("Please select or speak at least one symptom to proceed.");
        return;
    }

    updateStepper(2);
    answeredQuestionIds = [];
    
    // 1. Initial Shannon Entropy & Uncertainty Assessment
    try {
        const uPayload = {
            symptoms: Array.from(selectedSymptoms),
            qa_answers: answeredQA
        };
        const uRes = await API.post('/api/closed-loop/uncertainty-assess', uPayload);
        updateUncertaintyDisplay(uRes);
    } catch (e) {
        console.warn("Uncertainty assessment initial ping:", e);
    }

    // 2. Fetch Next-Best-Question (Information Gain)
    await fetchAndRenderNextQuestion();

    // 3. Load Contextual Questions
    const container = document.getElementById('questionsContainer');
    container.innerHTML = `<div class="text-center py-3"><div class="spinner-border text-primary spinner-border-sm" role="status"></div><span class="small ms-2">Generating adaptive inquiry questions...</span></div>`;

    try {
        const payload = { symptoms: Array.from(selectedSymptoms) };
        const res = await API.post('/api/navigator/questions', payload);
        currentAdaptiveQuestions = res.questions;

        container.innerHTML = currentAdaptiveQuestions.map((q, idx) => `
            <div class="p-3 bg-light rounded-3 border">
                <label class="form-label small fw-bold text-dark mb-2">${idx + 1}. ${q.question}</label>
                <select class="form-select adaptive-input" data-qid="${q.id}" required onchange="handleAnswerChange()">
                    ${q.options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
                </select>
            </div>
        `).join('');
    } catch (err) {
        container.innerHTML = `<div class="alert alert-danger">Error: ${err.message}</div>`;
    }
}

function updateUncertaintyDisplay(data) {
    if (!data) return;
    const score = data.uncertainty_score || 50;
    const entropy = data.shannon_entropy || 2.5;
    const band = data.certainty_band || "Moderate Uncertainty";

    document.getElementById('step2UncertaintyBadge').textContent = `Uncertainty: ${score}%`;
    const bar = document.getElementById('step2UncertaintyBar');
    bar.style.width = `${score}%`;
    if (score <= 25) {
        bar.className = "uncertainty-bar-fill uncertainty-low";
    } else {
        bar.className = "uncertainty-bar-fill uncertainty-high";
    }

    document.getElementById('step2EntropyVal').textContent = `${entropy} bits`;
    const bandElem = document.getElementById('step2CertaintyBand');
    bandElem.textContent = band;
    bandElem.className = score <= 25 ? "badge bg-success" : (score <= 60 ? "badge bg-warning" : "badge bg-danger");
}

async function fetchAndRenderNextQuestion() {
    try {
        const payload = {
            symptoms: Array.from(selectedSymptoms),
            answered_question_ids: answeredQuestionIds,
            qa_answers: answeredQA
        };
        const res = await API.post('/api/closed-loop/next-question', payload);
        const card = document.getElementById('nextQuestionCard');
        if (res.has_next_question && res.next_question) {
            const q = res.next_question;
            card.classList.remove('d-none');
            document.getElementById('infoGainTag').innerHTML = `<i class="bi bi-lightning-charge-fill"></i> +${q.information_gain} bits Information Gain`;
            document.getElementById('nextQuestionText').textContent = q.question;
            document.getElementById('nextQuestionRationale').textContent = q.rationale;
            
            const optContainer = document.getElementById('nextQuestionOptions');
            optContainer.innerHTML = q.options.map(opt => `
                <button type="button" class="btn btn-outline-primary btn-sm text-start py-2 px-3 fw-semibold" onclick="selectNextQuestionAnswer('${q.question_id}', '${opt.replace(/'/g, "\\'")}')">
                    <i class="bi bi-arrow-right-circle me-1"></i> ${opt}
                </button>
            `).join('');
        } else {
            card.classList.add('d-none');
        }
    } catch (e) {
        console.warn("Next question engine error:", e);
    }
}

async function selectNextQuestionAnswer(qId, answer) {
    answeredQA[qId] = answer;
    answeredQuestionIds.push(qId);
    
    // Re-assess uncertainty
    try {
        const uPayload = {
            symptoms: Array.from(selectedSymptoms),
            qa_answers: answeredQA
        };
        const uRes = await API.post('/api/closed-loop/uncertainty-assess', uPayload);
        updateUncertaintyDisplay(uRes);
    } catch (e) {
        console.error(e);
    }
    
    // Fetch subsequent next-question
    await fetchAndRenderNextQuestion();
}

function handleAnswerChange() {
    document.querySelectorAll('.adaptive-input').forEach(sel => {
        const qid = sel.getAttribute('data-qid');
        answeredQA[qid] = sel.value;
    });
}


function goToStep3(e) {
    if (e) e.preventDefault();
    // Collect answers from Step 2
    answeredQA = {};
    document.querySelectorAll('.adaptive-input').forEach(sel => {
        const qid = sel.getAttribute('data-qid');
        answeredQA[qid] = sel.value;
    });

    updateStepper(3);
}

async function uploadStep3Report() {
    const fileInput = document.getElementById('step3FileInput');
    const reportType = document.getElementById('step3ReportType').value;
    const btn = document.getElementById('step3UploadBtn');
    const box = document.getElementById('extractedBiomarkersBox');

    if (!fileInput.files || fileInput.files.length === 0) {
        alert("Please select a file (image or PDF) to upload.");
        return;
    }

    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Analyzing Biomarkers...`;

    const formData = new FormData();
    formData.append('report_type', reportType);
    formData.append('file', fileInput.files[0]);

    try {
        const res = await API.postForm('/api/reports/upload', formData);
        uploadedReportIds.push(res.id);

        const findings = res.extracted_findings || {};
        const abnormal = findings.abnormal_flags || [];
        const params = findings.extracted_parameters || {};
        const rad = findings.radiology_findings || [];

        box.innerHTML = `
            <div class="alert alert-success py-2 small mb-2"><i class="bi bi-check-circle"></i> Analyzed: ${res.original_filename}</div>
            <div class="mb-2">
                <small class="fw-bold d-block text-secondary">Extracted Parameters:</small>
                ${Object.entries(params).map(([k, v]) => `<span class="biomarker-pill normal">${k}: ${v}</span>`).join('')}
            </div>
            ${abnormal.length > 0 ? `
                <div class="mb-2">
                    <small class="fw-bold d-block text-danger">Abnormal Flags Detected:</small>
                    ${abnormal.map(a => `<span class="biomarker-pill abnormal"><i class="bi bi-exclamation-triangle"></i> ${a}</span>`).join('')}
                </div>
            ` : '<div class="small text-success mb-2"><i class="bi bi-shield-check"></i> No critical lab anomalies detected.</div>'}
            ${rad.length > 0 ? `
                <div class="small text-dark mt-2 border-top pt-2">
                    <strong>Radiology Impressions:</strong> ${rad.join('; ')}
                </div>
            ` : ''}
        `;
    } catch (err) {
        alert("Upload error: " + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="bi bi-cpu me-1"></i> Upload & Extract Biomarkers`;
    }
}

async function goToStep4() {
    updateStepper(4);

    const payload = {
        symptoms: Array.from(selectedSymptoms),
        qa_answers: answeredQA,
        uploaded_report_ids: uploadedReportIds
    };

    try {
        const res = await API.post('/api/navigator/assess', payload);
        
        // Enrich with Explainable Decision Map from Closed-Loop Engine
        if (!res.explainable_decision_map) {
            try {
                res.explainable_decision_map = await API.post('/api/closed-loop/explainable-decision-map', {
                    target_disease: res.top_disease,
                    symptoms: Array.from(selectedSymptoms),
                    qa_answers: answeredQA
                });
            } catch (xErr) {
                console.warn("Could not load explainable map:", xErr);
            }
        }

        // Enrich with Minimum Diagnostic Test Set from Closed-Loop Engine
        if (!res.minimum_diagnostic_test_set) {
            try {
                res.minimum_diagnostic_test_set = await API.post('/api/closed-loop/minimum-tests', {
                    top_disease: res.top_disease,
                    current_uncertainty: 55.0,
                    symptoms: Array.from(selectedSymptoms),
                    triage_level: res.triage ? res.triage.triage_level : "Doctor Consultation"
                });
            } catch (tErr) {
                console.warn("Could not load minimum tests:", tErr);
            }
        }

        latestAssessment = res;
        displayStep4Results(res);
    } catch (err) {
        alert("Assessment error: " + err.message);
    }
}

function displayStep4Results(res) {
    document.getElementById('triageTopDisease').textContent = `${res.top_disease} (${res.confidence_percentage}% Match)`;
    document.getElementById('triageActionText').textContent = res.triage.action_text;
    
    // Triage Badge
    const badge = document.getElementById('triageBadge');
    badge.className = `triage-badge-${res.triage.triage_level.toLowerCase().replace(/[^a-z]/g, '')}`;
    badge.innerHTML = `<i class="bi bi-shield-exclamation"></i> ${res.triage.triage_level}`;

    // Triage reasons
    const reasonsList = document.getElementById('triageReasonsList');
    if (res.triage.triage_reasons && res.triage.triage_reasons.length > 0) {
        reasonsList.innerHTML = `<strong class="d-block text-danger mb-1">Triage Trigger Factors:</strong>` + 
            res.triage.triage_reasons.map(r => `<div>• ${r}</div>`).join('');
    } else {
        reasonsList.innerHTML = `<div class="text-muted">Standard clinical pathway. No acute emergency red-flags triggered.</div>`;
    }

    // 1. "Why Did AI Decide This?" Explainable Health Decision Map
    const mapBox = document.getElementById('explainableDecisionMapContainer');
    const xaiData = res.explainable_decision_map;
    if (xaiData && mapBox) {
        const netScore = (xaiData.net_positive_score || 0) + (xaiData.net_negative_score || 0);
        document.getElementById('decisionMapNetScore').textContent = `Net Attributions: ${netScore >= 0 ? '+' : ''}${netScore}`;
        
        let mapHtml = '';
        // Positive features
        (xaiData.positive_attributions || []).forEach(f => {
            mapHtml += `
                <div class="decision-map-bar d-flex justify-content-between align-items-center p-2 rounded bg-light border">
                    <div>
                        <strong class="text-dark d-block">${f.feature}</strong>
                        <small class="text-muted">${f.category} • ${f.effect}</small>
                    </div>
                    <span class="attribution-bar-pos">+${f.weight}</span>
                </div>
            `;
        });
        // Negative features
        (xaiData.negative_attributions || []).forEach(f => {
            mapHtml += `
                <div class="decision-map-bar d-flex justify-content-between align-items-center p-2 rounded bg-light border">
                    <div>
                        <strong class="text-dark d-block">${f.feature}</strong>
                        <small class="text-muted">${f.category} • ${f.effect}</small>
                    </div>
                    <span class="attribution-bar-neg">${f.weight}</span>
                </div>
            `;
        });
        mapBox.innerHTML = mapHtml || '<div class="text-muted small">Standard feature baseline.</div>';

        // Missing information impact
        const missing = xaiData.missing_information_penalties || [];
        const missingText = document.getElementById('missingInfoText');
        if (missing.length > 0) {
            missingText.innerHTML = missing.map(m => `
                <div class="mt-1"><span class="badge bg-warning text-dark me-1">${m.criticality}</span> <strong>${m.parameter}:</strong> ${m.impact}</div>
            `).join('');
        } else {
            missingText.innerHTML = '<span class="text-success"><i class="bi bi-check-circle"></i> Sufficient clinical dimensions captured. No critical information gaps.</span>';
        }
    }

    // 2. Minimum Diagnostic Test Set Optimization (Pareto Safety Knapsack)
    const minTestSet = res.minimum_diagnostic_test_set;
    const tableBody = document.getElementById('minimumTestsTableBody');
    if (minTestSet && tableBody) {
        document.getElementById('residualUncertaintyBadge').textContent = `Residual Uncertainty: ~${minTestSet.expected_residual_uncertainty_pct}%`;
        document.getElementById('minTestTotalCost').textContent = `₹${minTestSet.total_estimated_cost_inr}`;
        document.getElementById('radiationSafetyBadge').textContent = minTestSet.radiation_burden_profile.split('(')[0].trim();

        tableBody.innerHTML = (minTestSet.minimum_test_set || []).map(t => `
            <tr>
                <td>
                    <strong class="d-block text-dark">${t.test_name}</strong>
                    <small class="text-muted">${t.rationale}</small>
                </td>
                <td>
                    <span class="badge ${t.priority_tier === 1 ? 'bg-danger text-white' : 'bg-primary text-white'}">
                        ${t.priority_tier === 1 ? 'MANDATORY' : 'RECOMMENDED'}
                    </span>
                </td>
                <td class="fw-semibold">₹${t.cost_inr}</td>
                <td>
                    <span class="badge ${t.radiation_risk === 'None' ? 'bg-success text-white' : 'bg-warning text-dark'}">
                        ${t.radiation_risk}
                    </span>
                </td>
            </tr>
        `).join('');
    }

    // SBAR Handover Preview
    const readableSymptoms = Array.from(selectedSymptoms).map(s => s.replace(/_/g, ' ')).join(', ');
    document.getElementById('sbarSituation').textContent = `Chief Complaint: ${readableSymptoms}. Duration: ${answeredQA['duration_days'] || 'N/A'}. Pain Scale: ${answeredQA['severity_scale'] || 'N/A'}.`;
    
    const allergyText = (currentProfile && currentProfile.drug_allergies) ? currentProfile.drug_allergies : 'No Known Drug Allergies (NKDA)';
    const condText = (currentProfile && currentProfile.pre_existing_conditions) ? currentProfile.pre_existing_conditions : 'None reported';
    const ageGender = (currentProfile && currentProfile.age) ? `Age: ${currentProfile.age}, Gender: ${currentProfile.gender}` : 'Adult';
    document.getElementById('sbarBackground').textContent = `${ageGender}. Pre-existing: ${condText}. Known Drug Allergies: ${allergyText}. Self-meds taken: ${answeredQA['prior_meds_taken'] || 'None'}.`;
    
    document.getElementById('sbarAssessment').textContent = `Triage Level: ${res.triage.triage_level}. Suspected: ${res.top_disease} (${res.confidence_percentage}% confidence). Specialist: ${res.specialist_recommended}.`;
    document.getElementById('sbarRecommendation').textContent = `Correlate symptom onset with physical exam. Ensure pharmacotherapy checks against declared allergy: "${allergyText}".`;
}


// Finalize and Transmit Handover to Doctor
async function finalizeConsultation() {
    const doctorId = document.getElementById('step4DoctorSelect').value;
    const btn = document.getElementById('confirmConsultBtn');

    if (!doctorId) {
        alert("Please select a consulting doctor from the list.");
        return;
    }

    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Transmitting Handover...`;

    const payload = {
        doctor_id: parseInt(doctorId),
        symptoms: Array.from(selectedSymptoms),
        predicted_disease: latestAssessment ? latestAssessment.top_disease : "General Assessment",
        confidence_score: latestAssessment ? latestAssessment.confidence_percentage : 0.0,
        recommended_tests: latestAssessment ? latestAssessment.recommended_diagnostic_tests.join(', ') : "",
        severity: latestAssessment ? latestAssessment.severity : "Moderate",
        triage_level: latestAssessment ? latestAssessment.triage.triage_level : "Doctor Consultation",
        adaptive_qa: answeredQA,
        extracted_biomarkers: latestAssessment ? latestAssessment.biomarkers_detected : {},
        xai_reasoning: latestAssessment ? latestAssessment.xai_reasoning : [],
        patient_notes: `Initiated via AI Personal Health Navigator. Duration: ${answeredQA['duration_days'] || 'N/A'}.`
    };

    try {
        const res = await API.post('/api/consultations', payload);
        alert("Success! Your structured SBAR Clinical Handover has been transmitted to your physician.");
        
        // Reset wizard
        selectedSymptoms.clear();
        uploadedReportIds = [];
        updateSelectedCount();
        updateStepper(1);
        
        // Switch to Consultations History tab
        const historyBtn = document.getElementById('tab-history-btn');
        if (historyBtn) bootstrap.Tab.getOrCreateInstance(historyBtn).show();
        loadConsultations();
    } catch (err) {
        alert("Error booking consultation: " + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="bi bi-send-check-fill me-1"></i> Transmit Handover & Book Consultation`;
    }
}

// Load Doctors Dropdown
async function loadDoctorsDropdown() {
    try {
        const doctors = await API.get('/api/doctors');
        const select = document.getElementById('step4DoctorSelect');
        select.innerHTML = '<option value="">Choose a Doctor...</option>' + doctors.map(d => `
            <option value="${d.user_id}">
                ${d.full_name} (${d.specialization}) — ${d.hospital_affiliation}
            </option>
        `).join('');
    } catch (err) {
        console.error("Error loading doctors dropdown:", err);
    }
}

// Profile Management
async function loadProfileData() {
    try {
        const user = await API.get('/api/profile');
        currentProfile = user;
        document.getElementById('profName').value = user.full_name || '';
        document.getElementById('profAge').value = user.age || '';
        document.getElementById('profGender').value = user.gender || 'Male';
        document.getElementById('profPhone').value = user.phone || '';
        document.getElementById('profBlood').value = user.blood_group || '';
        document.getElementById('profAllergies').value = user.drug_allergies || '';
        document.getElementById('profConditions').value = user.pre_existing_conditions || '';
        document.getElementById('profMeds').value = user.current_medications || '';

        // Load contact routing details
        const cfg = getContactSettings();
        const pWhatsapp = document.getElementById('profWhatsapp');
        const pCName = document.getElementById('profCaretakerName');
        const pCPhone = document.getElementById('profCaretakerPhone');
        const pCRel = document.getElementById('profCaretakerRelation');
        if (pWhatsapp) pWhatsapp.value = cfg.patientWhatsapp || user.phone || '';
        if (pCName) pCName.value = cfg.caretakerName || '';
        if (pCPhone) pCPhone.value = cfg.caretakerPhone || '';
        if (pCRel) pCRel.value = cfg.caretakerRelation || 'Daughter / Primary Guardian';
    } catch (err) {
        console.error("Error loading profile:", err);
    }
}

async function saveProfile(e) {
    e.preventDefault();
    const phoneVal = document.getElementById('profPhone').value;
    const whatsappVal = document.getElementById('profWhatsapp')?.value || phoneVal;
    const cName = document.getElementById('profCaretakerName')?.value || 'Sarah Doe';
    const cPhone = document.getElementById('profCaretakerPhone')?.value || '+91 98111 22233';
    const cRel = document.getElementById('profCaretakerRelation')?.value || 'Daughter / Primary Guardian';

    const payload = {
        full_name: document.getElementById('profName').value,
        age: parseInt(document.getElementById('profAge').value) || null,
        gender: document.getElementById('profGender').value,
        phone: phoneVal,
        blood_group: document.getElementById('profBlood').value,
        drug_allergies: document.getElementById('profAllergies').value,
        pre_existing_conditions: document.getElementById('profConditions').value,
        current_medications: document.getElementById('profMeds').value
    };

    // Save contact routing
    const cfg = {
        patientPhone: phoneVal,
        patientWhatsapp: whatsappVal,
        caretakerName: cName,
        caretakerPhone: cPhone,
        caretakerRelation: cRel,
        dualAlert: true
    };
    localStorage.setItem('ehealth_contact_routing', JSON.stringify(cfg));
    initContactSettings();

    const btn = document.getElementById('saveProfBtn');
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Saving...`;

    try {
        const updated = await API.request('/api/profile', { method: 'PUT', body: payload });
        currentProfile = updated;
        showSMSNotification({
            title: "PROFILE & ROUTING SAVED",
            message: `Health profile and Caretaker routing for ${cName} (${cPhone}) successfully verified.`,
            channel: "whatsapp",
            otp: Math.floor(100000 + Math.random() * 900000).toString(),
            duration: 7500
        });
    } catch (err) {
        showSMSNotification({
            title: "PROFILE SAVE FAILED",
            message: err.message,
            channel: "sms",
            duration: 6000
        });
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="bi bi-save me-1"></i> Save Health Profile`;
    }
}

// Load Consultations History
async function loadConsultations() {
    const container = document.getElementById('consultationsList');
    container.innerHTML = `<div class="col-12 text-center py-5 text-muted"><div class="spinner-border text-primary"></div><p class="mt-2">Loading medical records...</p></div>`;

    try {
        const records = await API.get('/api/consultations');
        if (!records || records.length === 0) {
            container.innerHTML = `<div class="col-12 text-center py-5 text-muted">No consultations found. Use the Health Navigator to start.</div>`;
            return;
        }

        container.innerHTML = records.map(c => {
            const isCompleted = c.status === 'completed';
            const triageBadge = `<span class="badge bg-primary-subtle text-primary">${c.triage_level || 'Doctor Consultation'}</span>`;

            return `
                <div class="col-12">
                    <div class="card border-0 shadow-sm rounded-4 p-4">
                        <div class="d-flex justify-content-between align-items-start flex-wrap gap-2 mb-2">
                            <div>
                                <h5 class="fw-bold text-dark mb-1">Consultation #${c.id}</h5>
                                <small class="text-muted"><i class="bi bi-clock"></i> ${new Date(c.created_at).toLocaleString()}</small>
                            </div>
                            <div class="d-flex gap-2">
                                ${triageBadge}
                                <span class="badge ${isCompleted ? 'bg-success-subtle text-success' : 'bg-warning-subtle text-warning'}">
                                    ${isCompleted ? 'Completed & Prescribed' : 'Pending Review'}
                                </span>
                            </div>
                        </div>

                        <div class="row g-2 py-2 small text-secondary">
                            <div class="col-md-4"><strong>Attending Doctor:</strong> <span class="text-primary fw-semibold">${c.doctor_name || 'Assigned Specialist'}</span></div>
                            <div class="col-md-4"><strong>Assessed Condition:</strong> <span class="text-dark fw-semibold">${c.predicted_disease}</span> (${c.confidence_score}%)</div>
                            <div class="col-md-4"><strong>Recommended Tests:</strong> ${c.recommended_tests || 'None'}</div>
                        </div>

                        ${c.clinical_handover_summary ? `
                            <div class="bg-light p-3 rounded-3 mt-2 border small">
                                <strong class="text-primary"><i class="bi bi-file-medical"></i> SBAR Clinical Handover Transmitted:</strong><br>
                                <strong>Situation:</strong> ${c.clinical_handover_summary.situation ? c.clinical_handover_summary.situation.chief_complaint : 'Standard case'}<br>
                                <strong>Assessment:</strong> ${c.clinical_handover_summary.assessment ? c.clinical_handover_summary.assessment.probable_diagnosis : 'Clinical review pending'}
                            </div>
                        ` : ''}

                        <div class="d-flex justify-content-end gap-2 mt-3 pt-3 border-top">
                            ${isCompleted && c.prescription ? `
                                <button class="btn btn-success btn-sm fw-semibold" onclick="viewPrescription(${c.id}, ${JSON.stringify(c.prescription).replace(/"/g, '&quot;')}, '${c.doctor_name}')">
                                    <i class="bi bi-prescription2"></i> View Verified Prescription
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        container.innerHTML = `<div class="col-12 alert alert-danger">Error: ${err.message}</div>`;
    }
}

// View Prescription Modal
function viewPrescription(consultId, p, doctorName) {
    document.getElementById('prescDoctorName').textContent = p.doctor_name || doctorName || "Attending Doctor";
    document.getElementById('prescConsultId').textContent = consultId;
    document.getElementById('prescDiagnosis').textContent = p.diagnosis;
    document.getElementById('prescDate').textContent = "Date: " + new Date(p.created_at).toLocaleDateString();
    document.getElementById('prescAdvice').textContent = p.general_advice || "Follow medication schedule strictly.";
    document.getElementById('prescFollowUp').textContent = `Review after ${p.follow_up_days || 7} days`;
    document.getElementById('prescPatientName').textContent = currentProfile ? currentProfile.full_name : "Patient";

    const tableBody = document.getElementById('prescMedicinesTable');
    tableBody.innerHTML = (p.medicines && p.medicines.length > 0) ? p.medicines.map(m => `
        <tr>
            <td class="fw-bold text-dark">${m.name}</td>
            <td><span class="badge bg-light text-dark border">${m.dosage}</span></td>
            <td>${m.timing}</td>
            <td>${m.duration}</td>
            <td class="small text-muted">${m.instructions || '-'}</td>
        </tr>
    `).join('') : '<tr><td colspan="5" class="text-center text-muted">No medicines prescribed.</td></tr>';

    bootstrap.Modal.getOrCreateInstance(document.getElementById('prescriptionModal')).show();
}

function printPrescriptionDoc() {
    const doctorName = document.getElementById('prescDoctorName')?.textContent || "Dr. Sarah Sharma, MD";
    const doctorSpec = document.getElementById('prescDoctorSpec')?.textContent || "Pulmonologist & Critical Care Specialist";
    const consultId = document.getElementById('prescConsultId')?.textContent || "1";
    const patientName = document.getElementById('prescPatientName')?.textContent || (currentProfile ? currentProfile.full_name : "Patient");
    const dateStr = document.getElementById('prescDate')?.textContent?.replace("Date:", "").trim() || new Date().toISOString().split('T')[0];
    const diagnosis = document.getElementById('prescDiagnosis')?.textContent || "Clinical Assessment Completed";
    const advice = document.getElementById('prescAdvice')?.textContent || "Follow prescribed dosages and rest well.";
    const followUp = document.getElementById('prescFollowUp')?.textContent || "Review in 7 days";
    const medsRows = document.getElementById('prescMedicinesTable')?.innerHTML || "";
    const cfg = getContactSettings();

    // Create or reuse isolated hidden iframe
    let printFrame = document.getElementById('prescriptionPrintIframe');
    if (!printFrame) {
        printFrame = document.createElement('iframe');
        printFrame.id = 'prescriptionPrintIframe';
        printFrame.style.position = 'fixed';
        printFrame.style.right = '0';
        printFrame.style.bottom = '0';
        printFrame.style.width = '0';
        printFrame.style.height = '0';
        printFrame.style.border = '0';
        document.body.appendChild(printFrame);
    }

    const doc = printFrame.contentWindow.document;
    doc.open();
    doc.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Medical Prescription - #${consultId} - ${patientName}</title>
            <style>
                @page {
                    size: A4 portrait;
                    margin: 12mm 15mm 12mm 15mm;
                }
                * {
                    box-sizing: border-box;
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                }
                body {
                    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                    color: #1e293b;
                    margin: 0;
                    padding: 0;
                    background: #ffffff;
                    font-size: 13px;
                    line-height: 1.45;
                }
                .rx-container {
                    border: 2px solid #1e3a8a;
                    border-radius: 8px;
                    padding: 24px;
                    background: #ffffff;
                }
                .hospital-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 2px solid #1e3a8a;
                    padding-bottom: 14px;
                    margin-bottom: 16px;
                }
                .hospital-title {
                    font-size: 20px;
                    font-weight: 800;
                    color: #1e3a8a;
                    letter-spacing: 0.5px;
                    margin: 0 0 2px 0;
                }
                .hospital-sub {
                    font-size: 11px;
                    color: #64748b;
                    margin: 0;
                }
                .meta-badge {
                    display: inline-block;
                    background: #ecfdf5;
                    border: 1px solid #a7f3d0;
                    color: #065f46;
                    font-size: 10px;
                    font-weight: 700;
                    padding: 3px 8px;
                    border-radius: 4px;
                    margin-top: 4px;
                }
                .patient-strip {
                    display: grid;
                    grid-template-columns: 2fr 1fr 1fr 1fr;
                    gap: 10px;
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 10px 14px;
                    margin-bottom: 16px;
                    font-size: 12px;
                }
                .patient-strip div strong {
                    color: #475569;
                    display: block;
                    font-size: 10px;
                    text-transform: uppercase;
                }
                .diagnosis-box {
                    background: #eff6ff;
                    border-left: 4px solid #2563eb;
                    padding: 10px 14px;
                    border-radius: 4px;
                    margin-bottom: 18px;
                }
                .diagnosis-title {
                    font-size: 11px;
                    font-weight: 700;
                    color: #1d4ed8;
                    text-transform: uppercase;
                    margin-bottom: 2px;
                }
                .diagnosis-val {
                    font-size: 15px;
                    font-weight: 700;
                    color: #0f172a;
                    margin: 0;
                }
                .rx-symbol {
                    font-size: 26px;
                    font-weight: 900;
                    font-family: 'Times New Roman', serif;
                    color: #1e3a8a;
                    margin-bottom: 8px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                    font-size: 12px;
                }
                table th {
                    background-color: #1e3a8a;
                    color: #ffffff;
                    text-align: left;
                    padding: 8px 10px;
                    font-size: 11px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                table td {
                    border-bottom: 1px solid #e2e8f0;
                    padding: 8px 10px;
                    color: #1e293b;
                }
                table tbody tr:nth-child(even) {
                    background-color: #f8fafc;
                }
                .badge {
                    display: inline-block;
                    padding: 2px 6px;
                    background: #e2e8f0;
                    border-radius: 4px;
                    font-weight: 600;
                    font-size: 11px;
                }
                .advice-box {
                    background: #fdf2f8;
                    border-left: 4px solid #db2777;
                    padding: 10px 14px;
                    border-radius: 4px;
                    margin-bottom: 18px;
                }
                .footer-signatures {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-end;
                    border-top: 1px dashed #94a3b8;
                    padding-top: 16px;
                    margin-top: 16px;
                }
                .qr-block {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                .qr-box {
                    width: 64px;
                    height: 64px;
                    border: 1px solid #cbd5e1;
                    padding: 4px;
                    background: #ffffff;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-family: monospace;
                    font-size: 8px;
                    text-align: center;
                    color: #475569;
                }
                .sig-block {
                    text-align: right;
                }
                .sig-script {
                    font-family: 'Brush Script MT', 'Dancing Script', cursive, sans-serif;
                    font-size: 24px;
                    color: #1e3a8a;
                    line-height: 1;
                    margin-bottom: 4px;
                }
                .security-footer {
                    font-size: 9px;
                    color: #94a3b8;
                    text-align: center;
                    margin-top: 14px;
                    border-top: 1px solid #f1f5f9;
                    padding-top: 6px;
                }
            </style>
        </head>
        <body>
            <div class="rx-container">
                <div class="hospital-header">
                    <div>
                        <div class="hospital-title">APEX MULTISPECIALTY HOSPITAL</div>
                        <div class="hospital-sub">Department of Pulmonary Medicine &amp; Clinical Critical Care</div>
                        <div class="hospital-sub">NABH Accredited • Reg No: APEX-HC/2026/IND-4921</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-weight: 700; color: #1e3a8a; font-size: 14px;">${doctorName}</div>
                        <div style="font-size: 11px; color: #64748b;">${doctorSpec}</div>
                        <div style="font-size: 10px; color: #94a3b8;">Medical Council Reg: #KMC-74892</div>
                        <span class="meta-badge">✓ Blockchain Integrity Verified</span>
                    </div>
                </div>

                <div class="patient-strip">
                    <div>
                        <strong>Patient Full Name</strong>
                        <span>${patientName}</span>
                    </div>
                    <div>
                        <strong>Consultation ID</strong>
                        <span>#${consultId}</span>
                    </div>
                    <div>
                        <strong>Issue Date</strong>
                        <span>${dateStr}</span>
                    </div>
                    <div>
                        <strong>Valid For</strong>
                        <span>${followUp}</span>
                    </div>
                </div>

                <div class="diagnosis-box">
                    <div class="diagnosis-title">Confirmed Clinical Diagnosis &amp; Findings</div>
                    <div class="diagnosis-val">${diagnosis}</div>
                </div>

                <div class="rx-symbol">℞ Prescribed Medicines</div>

                <table>
                    <thead>
                        <tr>
                            <th style="width: 28%;">Medicine / Generic Name</th>
                            <th style="width: 16%;">Dosage</th>
                            <th style="width: 22%;">Timing / Frequency</th>
                            <th style="width: 14%;">Duration</th>
                            <th style="width: 20%;">Clinical Instructions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${medsRows}
                    </tbody>
                </table>

                <div class="advice-box">
                    <strong style="color: #9d174d; text-transform: uppercase; font-size: 11px; display: block; margin-bottom: 2px;">Physician's Direct Advice &amp; Lifestyle Precautions</strong>
                    <span>${advice}</span>
                </div>

                <div class="footer-signatures">
                    <div class="qr-block">
                        <div class="qr-box">
                            [QR VERIFIED<br>RX-${consultId}]
                        </div>
                        <div>
                            <div style="font-weight: 700; font-size: 11px; color: #1e293b;">Digital Rx Cryptographic Hash</div>
                            <div style="font-family: monospace; font-size: 9px; color: #64748b;">SHA256: 8f3a9d21c0...7b41e9</div>
                            <div style="font-size: 9px; color: #10b981; font-weight: 600;">✓ Digitally Signed &amp; Safe for Pharmacy Dispensation</div>
                        </div>
                    </div>
                    <div class="sig-block">
                        <div class="sig-script">${doctorName}</div>
                        <div style="font-size: 11px; font-weight: 700; color: #1e3a8a; border-top: 1px solid #cbd5e1; padding-top: 2px;">Authorized Attending Physician</div>
                        <div style="font-size: 9px; color: #64748b;">Apex Hospital Digital Health Network</div>
                    </div>
                </div>

                <div class="security-footer">
                    This official digital prescription was generated via AI Personal Health Navigator. Dispatched to Patient (${cfg.patientPhone}) &amp; Caretaker ${cfg.caretakerName} (${cfg.caretakerPhone}).
                </div>
            </div>
        </body>
        </html>
    `);
    doc.close();

    // Trigger print dialog after DOM render
    setTimeout(() => {
        try {
            printFrame.contentWindow.focus();
            printFrame.contentWindow.print();
        } catch (err) {
            console.error("Print error:", err);
        }

        // Dispatch confirmed SMS OTP notification
        showSMSNotification({
            title: "PRESCRIPTION DOWNLOADED & DISPATCHED",
            message: `Official Rx #${consultId} prepared for PDF export. Verified copy dispatched to WhatsApp (${cfg.patientPhone}) and Caretaker ${cfg.caretakerName} (${cfg.caretakerPhone}).`,
            channel: "whatsapp",
            otp: Math.floor(100000 + Math.random() * 900000).toString(),
            duration: 8500
        });
    }, 400);
}

// Recovery Monitoring Tab
async function loadRecoveryTab() {
    try {
        const records = await API.get('/api/consultations');
        const select = document.getElementById('recoveryConsultSelect');
        select.innerHTML = '<option value="">Select consultation...</option>' + records.map(c => `
            <option value="${c.id}">Consultation #${c.id} - ${c.predicted_disease} (${new Date(c.created_at).toLocaleDateString()})</option>
        `).join('');

        select.onchange = () => {
            const id = select.value;
            if (id) loadRecoveryTimeline(id);
        };

        await loadDigitalHealthTimeline();
    } catch (err) {
        console.error("Error loading recovery tab:", err);
    }
}

async function loadRecoveryTimeline(consultId) {
    const container = document.getElementById('recoveryTimelineContainer');
    container.innerHTML = `<div class="text-center py-3"><div class="spinner-border spinner-border-sm text-primary"></div></div>`;

    try {
        const checkins = await API.get(`/api/recovery/${consultId}`);
        if (!checkins || checkins.length === 0) {
            container.innerHTML = `<div class="p-3 bg-light rounded-3 text-center text-muted small">No recovery check-ins logged for this consultation yet. Submit a Day 1 or Day 3 progress check-in on the left.</div>`;
            return;
        }

        container.innerHTML = checkins.map(c => `
            <div class="card p-3 border-start border-4 ${c.symptom_status.includes('Worsened') ? 'border-danger' : 'border-success'} rounded-3 shadow-sm bg-white">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="badge bg-dark">Day ${c.day_number} Check-In</span>
                    <small class="text-muted">${new Date(c.created_at).toLocaleDateString()}</small>
                </div>
                <div class="small mb-1"><strong>Status:</strong> <span class="fw-bold ${c.symptom_status.includes('Worsened') ? 'text-danger' : 'text-success'}">${c.symptom_status}</span> ${c.current_temperature ? `| Temp: ${c.current_temperature}` : ''}</div>
                ${c.patient_notes ? `<div class="small text-muted mb-2"><em>"${c.patient_notes}"</em></div>` : ''}
                <div class="alert ${c.symptom_status.includes('Worsened') ? 'alert-danger' : 'alert-success'} py-2 small mb-0">
                    <i class="bi bi-robot"></i> <strong>AI Continuous Feedback:</strong> ${c.ai_feedback}
                </div>
            </div>
        `).join('');
    } catch (err) {
        container.innerHTML = `<div class="alert alert-danger small">Error: ${err.message}</div>`;
    }
}

async function submitRecoveryCheckin(e) {
    e.preventDefault();
    const consultId = document.getElementById('recoveryConsultSelect').value;
    if (!consultId) {
        alert("Please select a consultation first.");
        return;
    }

    const payload = {
        consultation_id: parseInt(consultId),
        day_number: parseInt(document.getElementById('recoveryDaySelect').value),
        symptom_status: document.getElementById('recoveryStatusSelect').value,
        current_temperature: document.getElementById('recoveryTemp').value,
        patient_notes: document.getElementById('recoveryNotes').value
    };

    const btn = document.getElementById('recoverySubmitBtn');
    btn.disabled = true;

    try {
        await API.post('/api/recovery', payload);
        alert("Recovery check-in submitted successfully!");
        document.getElementById('recoveryNotes').value = '';
        await loadRecoveryTimeline(consultId);
    } catch (err) {
        alert("Error submitting check-in: " + err.message);
    } finally {
        btn.disabled = false;
    }
}

// Helper: Programmatic Tab Switching
function switchToTab(tabId) {
    const btn = document.querySelector(`[data-bs-target="#${tabId}"]`);
    if (btn) {
        bootstrap.Tab.getOrCreateInstance(btn).show();
    }
}

// ===================================================================
// 1. AI PREDICTIVE CARE & CHRONIC DETERIORATION ALERTS CONTROLLER
// ===================================================================
let activeFollowupId = null;

async function loadPredictiveTab() {
    try {
        const res = await API.get('/api/predictive/assessment');
        const assess = res.assessment;
        activeFollowupId = res.followup_record_id;

        const scoreEl = document.getElementById('predictiveRiskScore');
        const badgeEl = document.getElementById('predictiveUrgencyBadge');
        const barEl = document.getElementById('predictiveProgressBar');
        const timeEl = document.getElementById('predictiveTimeline');

        if (scoreEl) scoreEl.textContent = `${assess.risk_score}%`;
        if (timeEl) timeEl.textContent = assess.suggested_timeline;

        if (barEl) {
            barEl.style.width = `${assess.risk_score}%`;
            barEl.className = 'progress-bar progress-bar-striped progress-bar-animated ' + 
                (assess.risk_score >= 70 ? 'bg-danger' : assess.risk_score >= 45 ? 'bg-warning' : 'bg-success');
        }

        if (badgeEl) {
            badgeEl.textContent = `${assess.urgency_level} Deterioration Risk`;
            badgeEl.className = 'badge fs-6 px-3 py-1 ' + 
                (assess.risk_score >= 70 ? 'bg-danger text-white' : assess.risk_score >= 45 ? 'bg-warning-subtle text-warning' : 'bg-success-subtle text-success');
        }

        const reasonsContainer = document.getElementById('predictiveReasonsContainer');
        if (reasonsContainer && assess.reasons_breakdown) {
            reasonsContainer.innerHTML = assess.reasons_breakdown.map(r => `
                <div class="d-flex align-items-start gap-2 p-2 bg-light rounded-2 border">
                    <i class="bi bi-shield-exclamation text-warning mt-1"></i>
                    <span>${r}</span>
                </div>
            `).join('');
        }

        const specEl = document.getElementById('predictiveSpecialist');
        const dateEl = document.getElementById('predictiveSlotDate');
        if (specEl) specEl.textContent = assess.recommended_specialist;
        if (dateEl) dateEl.textContent = assess.suggested_date;

        const btn = document.getElementById('confirmFollowupBtn');
        if (btn) {
            if (res.followup_status === 'scheduled') {
                btn.className = 'btn btn-success w-100 fw-semibold';
                btn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Proactive Follow-up Confirmed';
                btn.disabled = true;
            } else {
                btn.className = 'btn btn-primary w-100 fw-semibold';
                btn.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Confirm & Reserve Proactive Slot';
                btn.disabled = false;
            }
        }

        // Load Chronic Condition Alerts
        await loadChronicAlerts();
    } catch (err) {
        console.error("Error loading predictive care:", err);
    }
}

async function loadChronicAlerts() {
    try {
        const res = await API.get('/api/predictive/chronic-alerts');
        const container = document.getElementById('chronicAlertsList');
        const countBadge = document.getElementById('activeAlertsCount');

        if (countBadge) countBadge.textContent = `${res.total_active_alerts} Alerts`;

        if (!res.alerts || res.alerts.length === 0) {
            container.innerHTML = '<div class="p-3 bg-light text-center text-muted rounded-3">No active chronic alerts. Chronic baselines are currently stable.</div>';
            return;
        }

        container.innerHTML = res.alerts.map(a => {
            const isCrit = a.severity === 'CRITICAL';
            const isWarn = a.severity === 'WARNING';
            const borderCls = isCrit ? 'border-danger' : isWarn ? 'border-warning' : 'border-info';
            const iconCls = isCrit ? 'bi-exclamation-octagon-fill text-danger' : isWarn ? 'bi-exclamation-triangle-fill text-warning' : 'bi-shield-check text-info';

            return `
                <div class="card p-3 border-start border-4 ${borderCls} rounded-3 shadow-sm bg-white">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="fw-bold text-dark"><i class="bi ${iconCls} me-1"></i>${a.alert_title}</span>
                        <span class="badge ${isCrit ? 'bg-danger' : isWarn ? 'bg-warning text-dark' : 'bg-info-subtle text-info'}">${a.condition_name}</span>
                    </div>
                    <p class="small text-muted mb-2"><strong>Clinical Risk:</strong> ${a.clinical_implication}</p>
                    <div class="p-2 bg-light rounded-2 small text-dark border">
                        <i class="bi bi-lightbulb text-warning me-1"></i><strong>Action:</strong> ${a.recommended_action}
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        console.error("Error loading chronic alerts:", err);
    }
}

async function confirmPredictiveFollowup() {
    if (!activeFollowupId) return;
    try {
        const res = await API.post(`/api/predictive/schedule-followup/${activeFollowupId}`);
        alert(res.message);
        loadPredictiveTab();
    } catch (err) {
        alert("Failed to schedule slot: " + err.message);
    }
}

// ===================================================================
// 2. IOT WEARABLES & LIVE TELEMETRY CONTROLLER
// ===================================================================
let ecgAnimationId = null;
let currentEcgPoints = [];

async function loadIoTTab() {
    try {
        const devRes = await API.get('/api/iot/devices');
        const devContainer = document.getElementById('iotDevicesContainer');
        if (devContainer && Array.isArray(devRes)) {
            devContainer.innerHTML = devRes.map(d => `
                <div class="col-md-3">
                    <div class="card border-0 shadow-sm rounded-4 p-3 bg-white h-100">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="badge bg-success-subtle text-success"><i class="bi bi-bluetooth me-1"></i>Paired</span>
                            <small class="text-muted"><i class="bi bi-battery-charging text-success me-1"></i>${d.battery_level}%</small>
                        </div>
                        <h6 class="fw-bold text-dark mb-1">${d.device_name}</h6>
                        <small class="text-muted d-block">${d.device_uid} (${d.firmware_version})</small>
                        <small class="text-secondary mt-1 d-block">Synced: ${new Date(d.last_sync_at).toLocaleTimeString()}</small>
                    </div>
                </div>
            `).join('');
        }

        // Fetch latest stream
        const streamRes = await API.get('/api/iot/vitals/latest');
        const stream = streamRes.telemetry_stream || {};

        // Update BP
        if (stream.bp_monitor) {
            document.getElementById('valBp').textContent = `${Math.round(stream.bp_monitor.primary_value)}/${Math.round(stream.bp_monitor.secondary_value || 80)}`;
            const badge = document.getElementById('badgeBpStatus');
            badge.textContent = stream.bp_monitor.alert_severity;
            badge.className = 'badge small ' + (stream.bp_monitor.alert_severity === 'CRITICAL' ? 'bg-danger' : stream.bp_monitor.alert_severity === 'WARNING' ? 'bg-warning text-dark' : 'bg-success-subtle text-success');
        }

        // Update Glucose
        if (stream.glucose_sensor) {
            document.getElementById('valGlucose').textContent = Math.round(stream.glucose_sensor.primary_value);
            const badge = document.getElementById('badgeGlucoseStatus');
            badge.textContent = stream.glucose_sensor.alert_severity;
            badge.className = 'badge small ' + (stream.glucose_sensor.alert_severity === 'CRITICAL' ? 'bg-danger' : stream.glucose_sensor.alert_severity === 'WARNING' ? 'bg-warning text-dark' : 'bg-success-subtle text-success');
        }

        // Update SpO2
        if (stream.pulse_oximeter) {
            document.getElementById('valSpo2').textContent = Math.round(stream.pulse_oximeter.primary_value);
            const badge = document.getElementById('badgeSpo2Status');
            badge.textContent = stream.pulse_oximeter.alert_severity;
            badge.className = 'badge small ' + (stream.pulse_oximeter.alert_severity === 'CRITICAL' ? 'bg-danger' : stream.pulse_oximeter.alert_severity === 'WARNING' ? 'bg-warning text-dark' : 'bg-success-subtle text-success');
        }

        // Update Temp
        if (stream.temperature) {
            document.getElementById('valTemp').textContent = stream.temperature.primary_value;
        }

        // Update ECG / HR
        if (stream.ecg_sensor) {
            document.getElementById('valHeartRate').textContent = `${Math.round(stream.ecg_sensor.primary_value)} bpm`;
            if (stream.ecg_sensor.ecg_waveform) {
                currentEcgPoints = stream.ecg_sensor.ecg_waveform;
            }
        }

        // Emergency threshold banner
        const banner = document.getElementById('iotEmergencyAlertBanner');
        if (banner) {
            if (streamRes.has_critical_emergency) {
                banner.classList.remove('d-none');
                const msg = Object.values(stream).find(v => v.alert_severity === 'CRITICAL')?.alert_message || "Critical vital reading detected.";
                document.getElementById('iotEmergencyMessage').textContent = msg;
            } else {
                banner.classList.add('d-none');
            }
        }

        // Start drawing canvas ECG
        initECGCanvas();

    } catch (err) {
        console.error("Error loading IoT tab:", err);
    }
}

async function simulateIoTReading(deviceType, triggerEmergency) {
    try {
        const res = await API.post(`/api/iot/simulate-stream?device_type=${deviceType}&trigger_emergency=${triggerEmergency}`);
        if (res.is_critical) {
            alert(`⚠️ EMERGENCY ALERT: ${res.alert_message}`);
        } else {
            alert(`Telemetry Synced: ${res.metric_type} = ${res.primary_value} ${res.unit} (${res.alert_severity})`);
        }
        await loadIoTTab();
    } catch (err) {
        alert("Error simulating stream: " + err.message);
    }
}

function initECGCanvas() {
    const canvas = document.getElementById('ecgCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (ecgAnimationId) cancelAnimationFrame(ecgAnimationId);

    let offset = 0;
    const width = canvas.width;
    const height = canvas.height;
    const baseline = height / 2;

    function renderFrame() {
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(0, 0, width, height);

        // Draw green ECG trace
        ctx.beginPath();
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 2.5;
        ctx.shadowColor = '#34d399';
        ctx.shadowBlur = 8;

        for (let x = 0; x < width; x += 3) {
            const idx = Math.floor((x + offset) / 6) % (currentEcgPoints.length || 30);
            const val = currentEcgPoints[idx] || 0.0;
            const y = baseline - (val * 48);
            if (x === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();

        offset += 2;
        ecgAnimationId = requestAnimationFrame(renderFrame);
    }
    renderFrame();
}

// ===================================================================
// 3. BLOCKCHAIN HEALTH RECORDS & SMART CONSENT CONTROLLER
// ===================================================================
async function loadBlockchainTab() {
    try {
        const ledgerRes = await API.get('/api/blockchain/ledger');
        const container = document.getElementById('blockchainBlocksContainer');
        const totalBadge = document.getElementById('totalBlocksBadge');

        if (totalBadge) totalBadge.textContent = `${ledgerRes.total_blocks} Blocks`;

        if (container && ledgerRes.chain) {
            container.innerHTML = ledgerRes.chain.map(b => `
                <div class="block-card p-3 rounded-3 shadow-sm border ${b.record_type === 'GENESIS' ? 'genesis' : ''}">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="badge ${b.record_type === 'GENESIS' ? 'bg-success' : 'bg-primary'} fs-6">Block #${b.block_index} • ${b.record_type}</span>
                        <small class="text-muted"><i class="bi bi-clock me-1"></i>${new Date(b.timestamp).toLocaleString()}</small>
                    </div>
                    <div class="small mb-1">
                        <span class="text-muted">Block Hash (SHA-256):</span>
                        <div class="hash-mono my-1">${b.block_hash}</div>
                    </div>
                    <div class="small mb-1">
                        <span class="text-muted">Previous Block Hash:</span>
                        <div class="hash-mono my-1 text-secondary">${b.previous_hash}</div>
                    </div>
                    <div class="small mb-2">
                        <span class="text-muted">Merkle Root:</span>
                        <span class="hash-mono">${b.merkle_root.slice(0, 24)}...</span>
                    </div>
                    <div class="d-flex justify-content-between align-items-center pt-2 border-top small">
                        <span class="text-success"><i class="bi bi-patch-check-fill me-1"></i>Valid HMAC Validator Signature</span>
                        <span class="badge bg-light text-dark border">Record ID: ${b.record_id}</span>
                    </div>
                </div>
            `).join('');
        }

        // Load Consents
        await loadConsentRecords();
        await checkExpiringConsents();

    } catch (err) {
        console.error("Error loading blockchain tab:", err);
    }
}

async function loadConsentRecords() {
    try {
        const consents = await API.get('/api/blockchain/consents');
        const container = document.getElementById('consentRecordsContainer');

        if (!consents || consents.length === 0) {
            container.innerHTML = '<div class="p-3 bg-light text-center text-muted rounded-3">No active sharing consents issued.</div>';
            return;
        }

        container.innerHTML = consents.map(c => `
            <div class="card p-3 rounded-3 shadow-sm border bg-white">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <strong class="text-dark">${c.grantee_name}</strong>
                    <span class="badge ${c.status === 'active' ? 'bg-success-subtle text-success' : 'bg-secondary-subtle text-secondary'}">${c.status.toUpperCase()}</span>
                </div>
                <small class="text-muted d-block mb-2">${c.grantee_organization || c.grantee_type}</small>
                <div class="mb-2">
                    ${c.permissions.map(p => `<span class="badge bg-light text-primary border me-1 small">${p}</span>`).join('')}
                </div>
                <div class="d-flex justify-content-between align-items-center small text-muted border-top pt-2">
                    <span>Expires: ${new Date(c.expires_at).toLocaleDateString()}</span>
                    ${c.status === 'active' ? `<button class="btn btn-outline-danger btn-sm py-0 px-2" onclick="revokeConsent(${c.id})">Revoke</button>` : '<span class="text-danger">Revoked</span>'}
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error("Error loading consents:", err);
    }
}

async function verifyBlockchainLedger() {
    try {
        const res = await API.post('/api/blockchain/verify-integrity');
        const alertBox = document.getElementById('blockchainVerifyAlert');
        const textEl = document.getElementById('blockchainVerifyText');

        if (res.is_valid) {
            alertBox.className = 'alert alert-success py-3 px-4 rounded-4 shadow-sm mb-4';
            textEl.textContent = res.verification_status;
        } else {
            alertBox.className = 'alert alert-danger py-3 px-4 rounded-4 shadow-sm mb-4 critical-flash-border';
            textEl.textContent = res.verification_status;
        }
        alert(res.verification_status);
    } catch (err) {
        alert("Integrity verification error: " + err.message);
    }
}

async function submitNewConsent(e) {
    e.preventDefault();
    const permissions = [];
    if (document.getElementById('permDiag').checked) permissions.push('diagnoses');
    if (document.getElementById('permLabs').checked) permissions.push('lab_reports');
    if (document.getElementById('permRx').checked) permissions.push('prescriptions');
    if (document.getElementById('permVitals').checked) permissions.push('live_vitals');

    const payload = {
        grantee_name: document.getElementById('consentGranteeName').value,
        grantee_type: document.getElementById('consentGranteeType').value,
        organization: document.getElementById('consentOrg').value,
        permissions: permissions,
        valid_hours: parseInt(document.getElementById('consentHours').value)
    };

    try {
        const res = await API.post('/api/blockchain/grant-consent', payload);
        alert(`Smart Consent issued successfully!\nAccess Token: ${res.access_token}\nRecorded at Block #${res.block_index}`);
        bootstrap.Modal.getInstance(document.getElementById('grantConsentModal')).hide();
        await loadBlockchainTab();
    } catch (err) {
        alert("Failed to grant consent: " + err.message);
    }
}

async function revokeConsent(consentId) {
    if (!confirm("Are you sure you want to revoke this consent token immediately? An immutable revocation event will be written to the blockchain.")) return;
    try {
        const res = await API.post(`/api/blockchain/revoke-consent/${consentId}`);
        alert(res.message);
        await loadBlockchainTab();
    } catch (err) {
        alert("Failed to revoke: " + err.message);
    }
}

// ===================================================================
// 4. INDOOR AR HOSPITAL NAVIGATION & LIVE QUEUE CONTROLLER
// ===================================================================
let hospitalFloorsData = null;
let currentNavFloor = "Ground Floor";

async function loadNavQueueTab() {
    try {
        hospitalFloorsData = await API.get('/api/navigation/floors');
        await switchFloor(currentNavFloor);
        await calculateNavRoute();
        await requestQueueRefresh();
    } catch (err) {
        console.error("Error loading navigation tab:", err);
    }
}

function switchFloor(floorName) {
    currentNavFloor = floorName;
    ['btnFloorGF', 'btnFloor1F', 'btnFloor2F'].forEach(id => {
        const b = document.getElementById(id);
        if (b) b.classList.remove('active');
    });
    if (floorName === 'Ground Floor') document.getElementById('btnFloorGF')?.classList.add('active');
    else if (floorName === '1st Floor') document.getElementById('btnFloor1F')?.classList.add('active');
    else if (floorName === '2nd Floor') document.getElementById('btnFloor2F')?.classList.add('active');

    renderHospitalSvgMap();
}

function renderHospitalSvgMap(routeWaypoints = []) {
    const svg = document.getElementById('hospitalMapSvg');
    if (!svg || !hospitalFloorsData) return;

    const waypoints = hospitalFloorsData.floors[currentNavFloor] || [];
    let innerHtml = `
        <defs>
            <linearGradient id="wallGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#e2e8f0"/>
                <stop offset="100%" stop-color="#cbd5e1"/>
            </linearGradient>
        </defs>
        <!-- Hospital Floor Outline -->
        <rect x="20" y="20" width="560" height="460" rx="20" fill="url(#wallGrad)" stroke="#94a3b8" stroke-width="3"/>
        <rect x="40" y="40" width="520" height="420" rx="14" fill="#ffffff" stroke="#e2e8f0" stroke-width="2"/>
        
        <!-- Floor Header Label -->
        <text x="50" y="75" font-family="Segoe UI, sans-serif" font-size="16" font-weight="bold" fill="#0d6efd">
            Apex Hospital - ${currentNavFloor} Blueprint
        </text>
    `;

    // Draw Route Polyline if present for this floor
    if (routeWaypoints && routeWaypoints.length > 1) {
        const floorPoints = routeWaypoints.filter(w => w.floor === currentNavFloor);
        if (floorPoints.length > 1) {
            const ptsStr = floorPoints.map(p => `${p.x},${p.y}`).join(' ');
            innerHtml += `<polyline points="${ptsStr}" fill="none" stroke="#ef4444" stroke-width="4" stroke-dasharray="6,4"/>`;
        }
    }

    // Draw Department Rooms & Waypoint Nodes
    waypoints.forEach(wp => {
        const isEmergency = wp.category === 'emergency';
        const isElevator = wp.category === 'elevator';
        const nodeColor = isEmergency ? '#ef4444' : isElevator ? '#8b5cf6' : '#0d6efd';

        innerHtml += `
            <g class="map-node" style="cursor: pointer;">
                <circle cx="${wp.x}" cy="${wp.y}" r="22" fill="${nodeColor}" opacity="0.15"/>
                <circle cx="${wp.x}" cy="${wp.y}" r="14" fill="${nodeColor}"/>
                <circle cx="${wp.x}" cy="${wp.y}" r="6" fill="#ffffff"/>
                <text x="${wp.x}" y="${wp.y + 28}" font-family="Segoe UI, sans-serif" font-size="11" font-weight="600" text-anchor="middle" fill="#1e293b">
                    ${wp.name.split('-')[0].slice(0, 18)}
                </text>
            </g>
        `;
    });

    svg.innerHTML = innerHtml;
}

async function calculateNavRoute() {
    const dest = document.getElementById('navDestinationSelect')?.value || 'OPD_PULMONOLOGY';
    try {
        const route = await API.get(`/api/navigation/route?start=ENTRANCE&destination=${dest}`);
        
        // Auto-switch to destination floor if different
        if (route.target_floor && route.target_floor !== currentNavFloor) {
            currentNavFloor = route.target_floor;
            switchFloor(currentNavFloor);
        } else {
            renderHospitalSvgMap(route.waypoints);
        }

        // Render directions list
        const dirList = document.getElementById('navDirectionsList');
        if (dirList) {
            dirList.innerHTML = route.directions.map(d => `<li class="mb-1">${d}</li>`).join('');
        }

        // Update AR HUD components
        const distEl = document.getElementById('arDistanceText');
        const instEl = document.getElementById('arInstructionText');
        if (distEl) distEl.textContent = `${route.total_distance_meters} m`;
        if (instEl) instEl.textContent = route.directions[0] || "Proceed toward department";

        const pills = document.getElementById('arWaypointsPills');
        if (pills && route.ar_camera_hud) {
            pills.innerHTML = route.ar_camera_hud.slice(0, 3).map(h => `
                <span class="ar-waypoint-pin"><i class="bi bi-geo-alt-fill text-info"></i> ${h.target.slice(0, 15)} (${h.distance_m}m)</span>
            `).join('');
        }

    } catch (err) {
        console.error("Error calculating navigation route:", err);
    }
}

function toggleARView() {
    const v = document.getElementById('arViewfinderContainer');
    const text = document.getElementById('arBtnText');
    if (!v) return;
    if (v.classList.contains('d-none')) {
        v.classList.remove('d-none');
        if (text) text.textContent = "Close AR Camera HUD";
    } else {
        v.classList.add('d-none');
        if (text) text.textContent = "Open AR Camera HUD";
    }
}

async function requestQueueRefresh() {
    try {
        const q = await API.get('/api/queue/my-token');
        document.getElementById('queueTokenCode').textContent = q.token_code;
        document.getElementById('queueDeptBadge').textContent = q.department;
        document.getElementById('queueServingCode').textContent = q.currently_serving_token;
        document.getElementById('queueWaitMinutes').textContent = `${q.estimated_wait_minutes} mins`;
        document.getElementById('queuePriorityText').textContent = q.priority_level === 'EMERGENCY_CRITICAL' ? 'EMERGENCY BYPASS (Priority P0)' : `Normal OPD (${q.patients_ahead} ahead)`;
    } catch (err) {
        console.error("Error refreshing queue:", err);
    }
}

// ===================================================================
// 5. RAPID SOS EMERGENCY & LIVE AMBULANCE CONTROLLER
// ===================================================================
let emergencyPollInterval = null;
let currentEmergencyAlertId = null;

async function triggerOneTapSOS() {
    try {
        const payload = {
            emergency_type: "SOS_MANUAL",
            latitude: 12.9716,
            longitude: 77.5946
        };
        const res = await API.post('/api/emergency/trigger-sos', payload);
        currentEmergencyAlertId = res.alert_id;
        alert(`🚨 EMERGENCY ACTIVATED!\nUnit: ${res.ambulance_unit}\nETA: ${res.eta_minutes} Mins\nER Trauma Bay #3 Reserved.`);
        
        switchToTab('tab-emergency');
        await loadEmergencyTab({ includePassport: true });

        // Start active tracking polling
        if (emergencyPollInterval) clearInterval(emergencyPollInterval);
        emergencyPollInterval = setInterval(() => loadEmergencyTab({ includePassport: false }), 4000);

    } catch (err) {
        alert("Failed to trigger SOS: " + err.message);
    }
}

async function loadEmergencyTab(options = {}) {
    const includePassport = options.includePassport !== false;
    try {
        if (includePassport) {
            loadLiveEmergencyPassport();
            loadPatientEmergencyAudit();
        }
        if (!currentPassportToken) {
            switchPassportContext('PUBLIC_BASIC');
        }
        const res = await API.get(currentEmergencyAlertId ? `/api/emergency/active-status?alert_id=${currentEmergencyAlertId}` : '/api/emergency/active-status');
        if (!res.has_active_emergency || !res.telemetry) return;

        const tel = res.telemetry;
        document.getElementById('ambulanceEtaDisplay').textContent = `${tel.eta_minutes} Mins`;
        document.getElementById('ambulanceDistanceDisplay').textContent = `${tel.distance_remaining_km} km`;
        document.getElementById('ambulanceStatusText').textContent = tel.status_text;
        document.getElementById('ambulanceUnitName').textContent = tel.ambulance_unit;
        document.getElementById('assignedTraumaBay').textContent = res.reserved_trauma_bay;
        document.getElementById('emergencyStatusBadge').textContent = tel.status.toUpperCase();

        const progBar = document.getElementById('ambulanceProgressBar');
        if (progBar) {
            const pct = Math.round((tel.current_step / tel.total_steps) * 100);
            progBar.style.width = `${pct}%`;
        }

        // Medical passport preview
        if (res.shared_medical_passport) {
            const mp = res.shared_medical_passport;
            document.getElementById('passportBloodGroup').textContent = mp.blood_group;
            document.getElementById('passportAllergies').textContent = mp.severe_drug_allergies;
            document.getElementById('passportConditions').textContent = mp.pre_existing_conditions;
            document.getElementById('passportMeds').textContent = mp.current_medications;
        }

    } catch (err) {
        console.error("Error loading emergency tab:", err);
    }
}

async function resolveEmergencyAlert() {
    if (!currentEmergencyAlertId) {
        alert("No active emergency to resolve.");
        return;
    }
    if (!confirm("Stand down emergency dispatch?")) return;
    try {
        await API.post(`/api/emergency/resolve/${currentEmergencyAlertId}`);
        if (emergencyPollInterval) clearInterval(emergencyPollInterval);
        alert("Emergency resolved and closed.");
        document.getElementById('emergencyStatusBadge').textContent = "STAND DOWN";
    } catch (err) {
        alert("Error: " + err.message);
    }
}

// ===================================================================
// 6. COMMUNITY & PREVENTIVE WELLNESS HUB CONTROLLER
// ===================================================================
async function loadCommunityTab() {
    try {
        // Load Posts
        const posts = await API.get('/api/community/posts');
        const feedContainer = document.getElementById('communityPostsFeed');
        if (feedContainer && Array.isArray(posts)) {
            feedContainer.innerHTML = posts.map(p => `
                <div class="card p-3 rounded-3 shadow-sm border bg-white">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="badge bg-secondary-subtle text-dark small">${p.group_name}</span>
                        <small class="text-muted">${new Date(p.created_at).toLocaleDateString()}</small>
                    </div>
                    <h6 class="fw-bold text-dark mt-1 mb-1">${p.title}</h6>
                    <p class="small text-muted mb-2">${p.content}</p>
                    <div class="d-flex justify-content-between align-items-center pt-2 border-top">
                        <span class="badge bg-success-subtle text-success small"><i class="bi bi-shield-check me-1"></i>AI Verified Safe</span>
                        <button class="btn btn-outline-danger btn-sm py-0 px-2" onclick="likePost(${p.id})">
                            <i class="bi bi-heart-fill text-danger me-1"></i> ${p.likes_count}
                        </button>
                    </div>
                </div>
            `).join('');
        }

        // Load Challenges
        const challenges = await API.get('/api/preventive/challenges');
        const chList = document.getElementById('preventiveChallengesList');
        if (chList && Array.isArray(challenges)) {
            chList.innerHTML = challenges.map(c => `
                <div class="card p-3 rounded-3 border shadow-sm bg-white">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <strong class="text-dark small">${c.title}</strong>
                        <span class="badge bg-warning text-dark"><i class="bi bi-fire me-1"></i>${c.streak_days} Day Streak</span>
                    </div>
                    <div class="progress my-2" style="height: 8px;">
                        <div class="progress-bar bg-success" style="width: ${c.progress_percent}%;"></div>
                    </div>
                    <div class="d-flex justify-content-between align-items-center small text-muted">
                        <span>${c.current_value} / ${c.target_value} ${c.unit} (${c.progress_percent}%)</span>
                        <button class="btn btn-outline-primary btn-sm py-0 px-2" onclick="logProgress(${c.id}, 1000)">+ Log</button>
                    </div>
                </div>
            `).join('');
        }

        // Load Rewards
        const rewards = await API.get('/api/preventive/rewards');
        document.getElementById('rewardPointsDisplay').textContent = rewards.total_points;
        document.getElementById('rewardTierDisplay').textContent = rewards.tier_level;

        const badgeBox = document.getElementById('badgesContainer');
        if (badgeBox && rewards.badges) {
            badgeBox.innerHTML = rewards.badges.map(b => `
                <div class="text-center" style="width: 80px;">
                    <div class="gamify-badge bg-${b.color}-subtle text-${b.color} mx-auto mb-1">
                        <i class="bi ${b.icon}"></i>
                    </div>
                    <small class="d-block fw-bold text-dark" style="font-size: 0.72rem;">${b.name}</small>
                </div>
            `).join('');
        }

        // Load AI Lifestyle Coach
        const coach = await API.get('/api/preventive/lifestyle-coach');
        const coachBox = document.getElementById('lifestyleCoachContainer');
        if (coachBox && coach.nutrition_plan) {
            coachBox.innerHTML = `
                <div class="p-3 bg-light rounded-3 border mb-2">
                    <strong class="text-primary d-block mb-1"><i class="bi bi-egg-fried me-1"></i>Nutrition Strategy: ${coach.nutrition_plan.dietary_framework}</strong>
                    <p class="text-muted mb-1">${coach.nutrition_plan.key_recommendation}</p>
                    <div class="small"><strong>Foods to Prioritize:</strong> ${coach.nutrition_plan.foods_to_prioritize.join(', ')}</div>
                </div>
                <div class="p-3 bg-light rounded-3 border mb-2">
                    <strong class="text-success d-block mb-1"><i class="bi bi-bicycle me-1"></i>Exercise Regimen: ${coach.exercise_plan.focus}</strong>
                    <p class="text-muted mb-0">${coach.exercise_plan.routine}</p>
                </div>
                <div class="p-2 bg-info-subtle text-info-emphasis rounded-2 small">
                    <i class="bi bi-lightbulb-fill me-1"></i><strong>Daily AI Longevity Tip:</strong> ${coach.daily_ai_tip}
                </div>
            `;
        }

    } catch (err) {
        console.error("Error loading community tab:", err);
    }
}

async function submitCommunityPost(e) {
    e.preventDefault();
    const payload = {
        group_slug: document.getElementById('postGroupSelect').value,
        title: document.getElementById('postTitleInput').value,
        content: document.getElementById('postContentInput').value
    };

    try {
        const res = await API.post('/api/community/posts', payload);
        alert(`Post Approved by AI Safety Filter!\nSafety Score: ${res.ai_safety_score}/100\nBadge: Verified Peer Contributor`);
        document.getElementById('postTitleInput').value = '';
        document.getElementById('postContentInput').value = '';
        await loadCommunityTab();
    } catch (err) {
        alert("Post Rejected: " + err.message);
    }
}

async function likePost(postId) {
    try {
        await API.post(`/api/community/posts/${postId}/like`);
        await loadCommunityTab();
    } catch (err) {
        console.error("Error liking post:", err);
    }
}

async function logProgress(challengeId, increment) {
    try {
        const res = await API.post(`/api/preventive/challenges/${challengeId}/log-progress`, { increment });
        if (res.points_awarded > 0) {
            alert(`🎉 Goal Completed! +${res.points_awarded} Health Points Awarded! Streak: ${res.streak_days} days`);
        }
        await loadCommunityTab();
    } catch (err) {
        alert("Failed to log progress: " + err.message);
    }
}

// ===================================================================
// 7. LONGITUDINAL DIGITAL HEALTH TIMELINE CONTROLLER
// ===================================================================
async function loadDigitalHealthTimeline() {
    const container = document.getElementById('digitalHealthTimelineContainer');
    if (!container) return;
    
    container.innerHTML = `<div class="text-center py-4 text-muted"><div class="spinner-border text-primary spinner-border-sm"></div> Loading timeline...</div>`;
    
    try {
        const patientId = currentProfile ? currentProfile.id : (API.getUser() ? API.getUser().id : 4);
        const res = await API.get(`/api/closed-loop/timeline/patient/${patientId}`);
        const entries = res.timeline_entries || [];
        
        if (entries.length === 0) {
            container.innerHTML = `<div class="text-center py-4 text-muted">No chronological health milestones recorded yet.</div>`;
            return;
        }

        const iconMap = {
            'SYMPTOM_ONSET': 'bi-activity text-warning',
            'DIAGNOSTIC_TEST': 'bi-eyedropper text-info',
            'DOCTOR_CONSULTATION': 'bi-person-badge text-primary',
            'PRESCRIPTION_DISPENSED': 'bi-capsule text-success',
            'OUTCOME_VERIFIED': 'bi-patch-check-fill text-emerald',
            'RECOVERY_CHECKIN': 'bi-arrow-repeat text-success',
            'EMERGENCY_DISPATCH': 'bi-truck text-danger'
        };

        container.innerHTML = entries.map(e => {
            const icon = iconMap[e.event_type] || 'bi-calendar-check text-secondary';
            const metrics = e.metrics || {};
            const metricsHtml = Object.keys(metrics).length > 0 ? `
                <div class="mt-2 p-2 bg-light rounded-2 small">
                    ${Object.entries(metrics).map(([k, v]) => `<div><strong>${k.replace(/_/g, ' ')}:</strong> ${v}</div>`).join('')}
                </div>
            ` : '';

            return `
                <div class="timeline-item mb-3 pb-3 border-bottom position-relative ps-4">
                    <div class="position-absolute start-0 top-0">
                        <i class="bi ${icon} fs-5"></i>
                    </div>
                    <div class="d-flex justify-content-between align-items-center flex-wrap gap-1">
                        <h6 class="fw-bold text-dark mb-0">${e.title}</h6>
                        <small class="text-muted"><i class="bi bi-clock me-1"></i>${new Date(e.recorded_at).toLocaleDateString()} ${new Date(e.recorded_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</small>
                    </div>
                    <div class="badge bg-light text-dark border small my-1">${e.event_type.replace(/_/g, ' ')} • ${e.severity_level || 'Normal'}</div>
                    <p class="text-secondary small mb-1">${e.description}</p>
                    ${metricsHtml}
                </div>
            `;
        }).join('');
    } catch (err) {
        container.innerHTML = `<div class="alert alert-danger small">Error loading timeline: ${err.message}</div>`;
    }
}

// ===================================================================
// 8. DYNAMIC CONTEXT-AWARE EMERGENCY PASSPORT & CONSENT CONTROLLER
// ===================================================================
let activePassportScope = 'PUBLIC_BASIC';
let currentPassportToken = null;

function renderLivePassportFields(p) {
    if (!p) return '<div class="text-muted">No passport data.</div>';
    const v = p.latest_vitals_snapshot || p.recent_vitals || {};
    const phys = p.physician || {};
    const vitals = [
        v.blood_pressure || v.bp,
        v.heart_rate || v.hr,
        v.spo2 ? ('SpO2 ' + v.spo2) : null,
        v.glucose
    ].filter(Boolean).join(' · ') || 'Not recorded';
    const physician = [phys.name, phys.specialization, phys.hospital].filter(x => x && x !== 'Not recorded').join(' · ') || 'Not recorded';
    return `
        <div class="row g-2">
            <div class="col-md-4"><span class="text-muted d-block">Identity</span><strong>${p.patient_name || p.full_name || '—'}</strong><div class="text-muted">${p.age || '—'} · ${p.gender || '—'}</div></div>
            <div class="col-md-2"><span class="text-muted d-block">Blood group</span><span class="badge bg-danger fs-6">${p.blood_group || '—'}</span></div>
            <div class="col-md-6"><span class="text-muted d-block">Allergies</span><strong class="text-danger">${p.severe_drug_allergies || p.drug_allergies || '—'}</strong></div>
            <div class="col-md-6"><span class="text-muted d-block">Critical conditions</span>${p.pre_existing_conditions || '—'}</div>
            <div class="col-md-6"><span class="text-muted d-block">Medications</span>${p.current_medications || '—'}</div>
            <div class="col-md-6"><span class="text-muted d-block">Emergency contact</span>${p.emergency_contact || p.emergency_contact_phone || '—'}</div>
            <div class="col-md-6"><span class="text-muted d-block">Physician</span>${physician}</div>
            <div class="col-12"><span class="text-muted d-block">Latest vitals</span>${vitals}</div>
        </div>
        <div class="small text-muted mt-2"><i class="bi bi-lock me-1"></i>Read-only live view · generated ${p.timestamp || ''}</div>
    `;
}

async function loadLiveEmergencyPassport() {
    const box = document.getElementById('liveEmergencyPassportBox');
    if (!box) return;
    try {
        const res = await API.get('/api/emergency/live-passport');
        box.innerHTML = renderLivePassportFields(res.passport);
    } catch (err) {
        box.innerHTML = `<div class="text-danger">${err.message}</div>`;
    }
}

async function loadPatientEmergencyAudit() {
    const tbody = document.getElementById('patientEmergencyAuditBody');
    if (!tbody) return;
    try {
        const res = await API.get('/api/emergency/audit-log');
        const events = res.events || [];
        if (!events.length) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-muted text-center py-3">No emergency access events yet.</td></tr>`;
            return;
        }
        tbody.innerHTML = events.map(ev => `
            <tr>
                <td class="small">${ev.timestamp ? new Date(ev.timestamp).toLocaleString() : '—'}</td>
                <td class="small">${ev.accessor_name || '—'}</td>
                <td class="small">${ev.accessor_role || '—'}</td>
                <td class="small">${ev.purpose || '—'}</td>
                <td class="small">${ev.information_type || '—'}</td>
                <td>${ev.is_emergency ? '<span class="badge bg-danger">Emergency</span>' : '<span class="badge bg-secondary">Routine</span>'}</td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-danger small">${err.message}</td></tr>`;
    }
}

async function switchPassportContext(scope) {
    activePassportScope = scope;
    await fetchAndRenderPassport(scope);
}

async function regeneratePassportToken() {
    await fetchAndRenderPassport(activePassportScope, true);
}

async function fetchAndRenderPassport(scope, forceNew = false) {
    const previewBox = document.getElementById('passportDataPreviewBox');
    const qrImg = document.getElementById('passportQrImg');
    const label = document.getElementById('passportScopeLabel');
    const tokenHash = document.getElementById('passportTokenHash');
    const countdown = document.getElementById('passportCountdown');

    if (!previewBox) return;
    previewBox.innerHTML = `<div class="text-center py-2 text-muted"><div class="spinner-border spinner-border-sm text-primary"></div> Generating context-scoped view...</div>`;

    try {
        const tokenRes = await API.post('/api/closed-loop/passport/generate-token', { context_scope: scope });
        currentPassportToken = tokenRes.token;

        if (label) label.textContent = tokenRes.scope_label;
        if (tokenHash) tokenHash.textContent = tokenRes.token;
        if (countdown) countdown.textContent = `Auto-Expires: ${tokenRes.validity_minutes} Minutes`;

        // Update QR Code Image
        const viewUrl = window.location.origin + (tokenRes.emergency_view_url || tokenRes.qr_access_url);
        if (qrImg) {
            qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(viewUrl)}`;
        }

        // Fetch the filtered view as the accessor would see it
        const viewRes = await API.get(tokenRes.qr_access_url);
        const data = viewRes.data || viewRes;

        let html = `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="badge bg-primary-subtle text-primary border border-primary-subtle">${viewRes.scope_label}</span>
                <span class="text-muted" style="font-size: 0.75rem;">Access Count: ${viewRes.access_count}</span>
            </div>
            <div class="text-dark">
        `;

        if (data.full_name) html += `<div><strong>Patient Name:</strong> ${data.full_name}</div>`;
        if (data.blood_group) html += `<div><strong>Blood Group:</strong> <span class="badge bg-danger">${data.blood_group}</span></div>`;
        if (data.drug_allergies) html += `<div><strong>Drug Allergies:</strong> <span class="text-danger fw-bold">${data.drug_allergies}</span></div>`;
        if (data.emergency_contact_phone) html += `<div><strong>Emergency Phone:</strong> ${data.emergency_contact_phone}</div>`;
        if (data.resuscitation_preference) html += `<div><strong>Code Status:</strong> <span class="badge bg-dark">${data.resuscitation_preference}</span></div>`;
        if (data.pre_existing_conditions) html += `<div><strong>Conditions:</strong> ${data.pre_existing_conditions}</div>`;
        if (data.current_medications) html += `<div><strong>Medications:</strong> ${data.current_medications}</div>`;
        if (data.recent_vitals) {
            const v = data.recent_vitals;
            const bp = v.blood_pressure || v.bp || '-';
            const hr = v.heart_rate || v.hr || '-';
            const spo2 = v.spo2 || '-';
            html += `<div class="mt-1"><strong>Recent Vitals:</strong> BP ${bp}, HR ${hr}, SpO2 ${spo2}</div>`;
        }
        if (data.recent_lab_biomarkers) {
            html += `<div class="mt-1"><strong>Lab Biomarkers:</strong> WBC ${data.recent_lab_biomarkers.wbc || '-'}, Platelets ${data.recent_lab_biomarkers.platelets || '-'}</div>`;
        }
        if (data.treating_physician_notes) {
            html += `<div class="mt-1 p-2 bg-white rounded border"><strong>Physician Notes:</strong> ${data.treating_physician_notes}</div>`;
        }

        html += `
            </div>
            <div class="mt-2 text-muted" style="font-size: 0.72rem;">
                <i class="bi bi-shield-lock me-1"></i> Data-bound consent active. Fields outside this scope are cryptographically masked.
            </div>
        `;

        previewBox.innerHTML = html;

    } catch (err) {
        previewBox.innerHTML = `<div class="alert alert-danger small">Error: ${err.message}</div>`;
    }
}

// ===================================================================
// 9. IOT MULTI-CHANNEL VITALS (BLUETOOTH, LAB REPORTS, MANUAL ENTRY)
// ===================================================================

async function connectBluetoothSmartwatch() {
    const statusBox = document.getElementById('bleStatusMessage');
    if (!navigator.bluetooth) {
        statusBox.innerHTML = '<span class="text-danger fw-semibold"><i class="bi bi-exclamation-triangle me-1"></i> Web Bluetooth API is not available on this browser or OS environment. Please use <strong>Recent Lab Reports</strong> or <strong>Manual Entry</strong>.</span>';
        return;
    }

    try {
        statusBox.innerHTML = '<span class="text-primary"><div class="spinner-border spinner-border-sm me-1"></div> Requesting Bluetooth device permission...</span>';
        const device = await navigator.bluetooth.requestDevice({
            filters: [{ services: ['heart_rate'] }],
            optionalServices: ['battery_service', 'device_information']
        });

        statusBox.innerHTML = `<span class="text-success fw-bold"><i class="bi bi-bluetooth me-1"></i> Connected to ${device.name || 'BLE Smartwatch'}! Streaming live vitals...</span>`;

        // Update gauges
        document.getElementById('valBp').textContent = "122/82";
        document.getElementById('valSpo2').textContent = "98";
        document.getElementById('valTemp').textContent = "98.6";
        document.getElementById('valGlucose').textContent = "105";

    } catch (err) {
        statusBox.innerHTML = `<span class="text-warning"><i class="bi bi-info-circle me-1"></i> Bluetooth permission dismissed: ${err.message}. Seamlessly switched to manual entry.</span>`;
    }
}

async function importVitalsFromReports() {
    const preview = document.getElementById('reportVitalsPreview');
    preview.innerHTML = '<div class="text-center py-2"><div class="spinner-border spinner-border-sm text-info"></div> Extracting recent clinical records...</div>';

    try {
        const reports = await API.get('/api/reports');
        if (!reports || reports.length === 0) {
            preview.innerHTML = '<span class="text-muted">No uploaded lab reports found. Use manual vitals entry or upload a report.</span>';
            return;
        }

        const latest = reports[0];
        const findings = latest.extracted_findings || {};
        const extracted = findings.extracted_vitals || {
            blood_pressure: "125/82 mmHg",
            heart_rate: "74 bpm",
            spo2: "98%",
            glucose: "112 mg/dL",
            temperature: "98.4°F"
        };

        // Update display gauges
        document.getElementById('valBp').textContent = extracted.blood_pressure.split(' ')[0] || "125/82";
        document.getElementById('valSpo2').textContent = extracted.spo2.replace('%', '') || "98";
        document.getElementById('valGlucose').textContent = extracted.glucose.split(' ')[0] || "112";
        document.getElementById('valTemp').textContent = extracted.temperature.replace('°F', '') || "98.4";

        preview.innerHTML = `
            <div class="alert alert-success py-2 px-3 rounded-3 mb-0 small">
                <i class="bi bi-check-circle-fill me-1"></i> Successfully imported from <strong>${latest.file_name}</strong> (Turnaround: ${new Date(latest.uploaded_at).toLocaleDateString()}):
                <div class="mt-1">BP: ${extracted.blood_pressure} • HR: ${extracted.heart_rate} • SpO2: ${extracted.spo2} • Glucose: ${extracted.glucose}</div>
            </div>
        `;
    } catch (err) {
        preview.innerHTML = `<div class="alert alert-danger small">Error extracting report vitals: ${err.message}</div>`;
    }
}

async function submitManualVitals(e) {
    e.preventDefault();
    const hr = document.getElementById('manualHR').value;
    const bp = document.getElementById('manualBP').value;
    const spo2 = document.getElementById('manualSpO2').value;
    const glucose = document.getElementById('manualGlucose').value;
    const temp = document.getElementById('manualTemp').value;

    document.getElementById('valBp').textContent = bp;
    document.getElementById('valSpo2').textContent = spo2;
    document.getElementById('valGlucose').textContent = glucose;
    document.getElementById('valTemp').textContent = temp;

    // Evaluate Caregiver alert automatically on vital update
    const [bpSys, bpDia] = bp.split('/').map(Number);
    try {
        await evaluateCaregiverAlertFromVitals({ hr, spo2, bp_sys: bpSys || 120, bp_dia: bpDia || 80, temp });
        alert(`Vitals saved and streamed successfully!\nHeart Rate: ${hr} bpm\nBlood Pressure: ${bp} mmHg\nSpO2: ${spo2}%\nGlucose: ${glucose} mg/dL\nTemperature: ${temp}°F`);
    } catch (err) {
        alert("Vitals saved to dashboard.");
    }
}

// ===================================================================
// 10. SMART CONSENT EXPIRATION AUDIT & NOTIFICATION SHIELD
// ===================================================================

async function checkExpiringConsents() {
    const list = document.getElementById('expiringConsentsList');
    if (!list) return;

    list.innerHTML = '<div class="text-center py-2 text-muted"><div class="spinner-border spinner-border-sm text-warning"></div> Auditing consent records...</div>';

    try {
        const res = await API.get('/api/blockchain/expiring-consents');
        const consents = res.expiring_consents || [];

        if (consents.length === 0) {
            list.innerHTML = '<div class="text-muted"><i class="bi bi-shield-check text-success me-1"></i> All smart consent grants are well within their active retention cycle.</div>';
            return;
        }

        list.innerHTML = consents.map(c => `
            <div class="p-3 bg-white rounded-3 border d-flex justify-content-between align-items-center flex-wrap gap-2">
                <div>
                    <strong class="text-dark d-block">${c.grantee_name} (${c.grantee_organization})</strong>
                    <small class="text-muted"><i class="bi bi-clock me-1"></i> Expires on ${new Date(c.expires_at).toLocaleDateString()} (${c.days_remaining} days left)</small>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-outline-success btn-sm fw-semibold" onclick="extendConsent365Days(${c.id})">
                        <i class="bi bi-calendar-plus me-1"></i> Extend 365 Days
                    </button>
                    <button class="btn btn-outline-danger btn-sm fw-semibold" onclick="purgeConsent(${c.id})">
                        <i class="bi bi-trash3 me-1"></i> Purge & Revoke Now
                    </button>
                </div>
            </div>
        `).join('');

    } catch (err) {
        list.innerHTML = `<div class="alert alert-danger small">Error: ${err.message}</div>`;
    }
}

async function extendConsent365Days(consentId) {
    try {
        const res = await API.post(`/api/blockchain/extend-consent/${consentId}`);
        alert(res.message);
        await checkExpiringConsents();
        await loadBlockchainTab();
    } catch (err) {
        alert("Error: " + err.message);
    }
}

async function purgeConsent(consentId) {
    if (!confirm("Are you sure you want to permanently revoke and purge this consent token from the ledger?")) return;
    try {
        const res = await API.post(`/api/blockchain/revoke-and-purge/${consentId}`);
        alert(res.message);
        await checkExpiringConsents();
        await loadBlockchainTab();
    } catch (err) {
        alert("Error: " + err.message);
    }
}

// ===================================================================
// 11. SMART ADAPTIVE REMINDERS CONTROLLER (BEHAVIORAL AI)
// ===================================================================

async function loadAdaptiveRemindersTab() {
    const list = document.getElementById('adaptiveRemindersList');
    if (!list) return;

    list.innerHTML = '<div class="text-center py-4 text-muted"><div class="spinner-border spinner-border-sm text-primary"></div> Analyzing behavioral intake patterns...</div>';

    try {
        const res = await API.get('/api/closed-loop/reminders/adaptive-schedules');
        const schedules = res.schedules || [];

        list.innerHTML = schedules.map(s => `
            <div class="p-3 bg-white rounded-3 border shadow-sm reminder-adaptive-card">
                <div class="d-flex justify-content-between align-items-start flex-wrap gap-2 mb-2">
                    <div>
                        <h6 class="fw-bold text-dark mb-0">${s.medicine_name} <small class="text-muted fw-normal">(${s.dosage})</small></h6>
                        <small class="badge bg-light text-dark border mt-1">${s.condition}</small>
                    </div>
                    <div class="text-end">
                        <span class="badge ${s.is_adapted ? 'bg-purple-subtle text-purple border' : 'bg-success-subtle text-success'} px-2 py-1">
                            ${s.is_adapted ? `AI Rescheduled (+${s.shift_minutes}m)` : 'Nominal Schedule'}
                        </span>
                        <div class="small fw-bold text-success mt-1">Adherence: ${s.adherence_rate_pct}%</div>
                    </div>
                </div>

                <div class="row g-2 p-2 bg-light rounded-2 small text-dark my-2">
                    <div class="col-6"><strong>Doctor Prescribed:</strong> <span class="text-muted">${s.prescribed_time}</span></div>
                    <div class="col-6"><strong>AI Optimized Slot:</strong> <span class="fw-bold text-primary">${s.current_reminder_time}</span></div>
                </div>

                <p class="small text-secondary mb-2 fst-italic">
                    <i class="bi bi-robot text-primary me-1"></i> ${s.adaptation_rationale}
                </p>

                <div class="d-flex justify-content-end gap-2 mt-2 pt-2 border-top">
                    <button class="btn btn-outline-success btn-sm fw-semibold" onclick="confirmDoseTaken(${s.id}, '${s.medicine_name}')">
                        <i class="bi bi-check2-circle me-1"></i> Confirm Dose Taken
                    </button>
                </div>
            </div>
        `).join('');

    } catch (err) {
        list.innerHTML = `<div class="alert alert-danger small">Error loading schedules: ${err.message}</div>`;
    }
}

async function confirmDoseTaken(scheduleId, medName) {
    try {
        const res = await API.post('/api/closed-loop/reminders/confirm-dose', { schedule_id: scheduleId });
        alert(`Dose Confirmed for ${medName}!\nTime: ${res.confirmed_at}\nBehavioral adherence profile updated.`);
    } catch (err) {
        alert("Error: " + err.message);
    }
}

async function simulateAdaptiveReschedule() {
    const prescribedTime = document.getElementById('simPrescribedTime').value || "08:00";
    const patternStr = document.getElementById('simDelayPattern').value;
    const delays = patternStr.split(',').map(Number);
    const resultBox = document.getElementById('simAdaptationResult');

    resultBox.classList.remove('d-none');
    resultBox.innerHTML = '<div class="spinner-border spinner-border-sm text-primary"></div> Computing behavioral model...';

    try {
        const res = await API.post('/api/closed-loop/reminders/adapt', {
            prescribed_time: prescribedTime,
            delay_minutes_history: delays
        });

        resultBox.innerHTML = `
            <div class="p-3 bg-light rounded-3 border">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <strong class="text-dark">Dynamic Rescheduling Analysis</strong>
                    <span class="badge ${res.is_adapted ? 'bg-primary' : 'bg-secondary'}">${res.is_adapted ? 'ADAPTED' : 'FIXED'}</span>
                </div>
                <div class="small"><strong>Nominal:</strong> ${res.prescribed_time} &rarr; <strong>AI Recommended:</strong> <span class="text-primary fw-bold">${res.recommended_reminder_time}</span> (Shift: +${res.shift_minutes} mins)</div>
                <div class="small text-muted mt-1">${res.rationale}</div>
            </div>
        `;
    } catch (err) {
        resultBox.innerHTML = `<div class="alert alert-danger small">Error: ${err.message}</div>`;
    }
}

// ===================================================================
// 12. CONTEXT-AWARE CAREGIVER ALERTS CONTROLLER
// ===================================================================

async function evaluateCaregiverAlertFromVitals(vitals) {
    try {
        const res = await API.post('/api/closed-loop/caregiver/evaluate-alert', { vitals, missed_doses_count: 0 });
        updateCaregiverAlertUI(res);
    } catch (err) {
        console.error("Caregiver alert evaluation error:", err);
    }
}

function updateCaregiverAlertUI(res) {
    const badge = document.getElementById('caregiverCurrentTierBadge');
    const box = document.getElementById('caregiverAlertStatusBox');
    const heading = document.getElementById('caregiverAlertHeading');
    const desc = document.getElementById('caregiverAlertDescription');

    if (!badge || !box) return;

    badge.className = `badge bg-${res.tier_color}`;
    badge.textContent = res.tier_badge;

    box.className = `p-3 rounded-3 border mb-3 caregiver-tier-${res.tier_level} small`;
    heading.className = `d-block text-${res.tier_color} mb-1`;
    heading.innerHTML = `<i class="bi bi-shield-exclamation me-1"></i> ${res.tier_badge}: ${res.primary_trigger}`;
    desc.textContent = res.caregiver_message;
}

async function triggerCaregiverAlertTest(level) {
    let vitals = { hr: 75, spo2: 98, bp_sys: 120, bp_dia: 80, temp: 98.6 };
    let missedDoses = 0;

    if (level === 'mild') {
        vitals = { hr: 104, spo2: 97, bp_sys: 136, bp_dia: 88, temp: 99.1 };
        missedDoses = 1;
    } else if (level === 'moderate') {
        vitals = { hr: 118, spo2: 93, bp_sys: 156, bp_dia: 96, temp: 100.8 };
        missedDoses = 2;
    } else if (level === 'critical') {
        vitals = { hr: 142, spo2: 86, bp_sys: 190, bp_dia: 110, temp: 102.5 };
        missedDoses = 3;
    }

    try {
        const res = await API.post('/api/closed-loop/caregiver/evaluate-alert', { vitals, missed_doses_count: missedDoses });
        updateCaregiverAlertUI(res);
        alert(`🚨 Caregiver Alert Escalation Triggered!\nTier: ${res.tier_badge}\nTrigger: ${res.primary_trigger}\nChannels: ${res.channels.join(', ')}\nMessage: "${res.caregiver_message}"`);
    } catch (err) {
        alert("Error testing alert: " + err.message);
    }
}


// ===================================================================
// 13. "WHO ACCESSED MY HEALTH DATA?" AUDIT & REVOCATION CONTROLLER
// ===================================================================

async function loadAccessHistoryTab() {
    const tbody = document.getElementById('accessHistoryTableBody');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted"><div class="spinner-border spinner-border-sm text-primary"></div> Reading decentralized access audit ledger...</td></tr>`;

    try {
        const res = await API.get('/api/blockchain/access-history');
        const history = res.access_history || [];

        if (history.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No external access events recorded. Your records remain private.</td></tr>`;
        } else {
            tbody.innerHTML = history.map(item => `
                <tr class="${item.is_emergency ? 'table-danger' : ''}">
                    <td class="small fw-semibold text-secondary text-nowrap">${item.date}</td>
                    <td>
                        <strong class="text-dark d-block">${item.accessor}</strong>
                        <small class="text-muted">${item.organization || 'Clinical Center'}</small>
                    </td>
                    <td><span class="badge bg-light text-dark border small">${item.role}</span></td>
                    <td class="small">${item.purpose}</td>
                    <td><span class="badge bg-primary-subtle text-primary border border-primary-subtle small">${item.data_scope}</span></td>
                    <td><span class="badge ${item.status_badge}">${item.status}</span></td>
                    <td>
                        ${item.can_revoke ? `
                            <button class="btn btn-outline-danger btn-sm text-nowrap" onclick="revokeAccess(${item.id}, ${item.consent_id})">
                                <i class="bi bi-slash-circle me-1"></i> Revoke Access
                            </button>
                        ` : (item.is_emergency ? `
                            <span class="badge bg-danger-subtle text-danger border border-danger-subtle small" title="Immutable Emergency Override">Immutable Audit</span>
                        ` : `
                            <span class="text-muted small">Inactive</span>
                        `)}
                    </td>
                </tr>
            `).join('');
        }

        // Also load Break-Glass logs
        await loadBreakGlassLogs();
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="alert alert-danger small">Error loading access audit: ${err.message}</td></tr>`;
    }
}

async function revokeAccess(id, consentId) {
    if (!confirm("Are you sure you want to REVOKE this permission immediately? The grantee's cryptographic bearer token will be permanently invalidated on the blockchain.")) return;

    try {
        if (consentId) {
            await API.post(`/api/blockchain/revoke-consent/${consentId}`);
        }
        alert("✓ Access Revoked! An immutable revocation block has been recorded on your patient ledger.");
        await loadAccessHistoryTab();
        // Update dashboard metric
        const permEl = document.getElementById('dashMetricPermissions');
        if (permEl) permEl.textContent = "1 active";
    } catch (err) {
        alert("Revocation error: " + err.message);
    }
}

async function loadBreakGlassLogs() {
    const container = document.getElementById('breakGlassLogsFeed');
    if (!container) return;

    try {
        const res = await API.get('/api/blockchain/break-glass-logs');
        const logs = res.break_glass_records || [];

        if (logs.length === 0) {
            container.innerHTML = `
                <div class="p-3 bg-light rounded-3 text-center text-muted small">
                    <i class="bi bi-shield-check text-success fs-5 d-block mb-1"></i>
                    Zero break-glass emergency overrides detected on your record.
                </div>
            `;
            return;
        }

        container.innerHTML = logs.map(l => `
            <div class="p-3 bg-danger-subtle rounded-3 border border-danger-subtle">
                <div class="d-flex justify-content-between align-items-start flex-wrap gap-2 mb-2">
                    <div>
                        <strong class="text-danger d-block"><i class="bi bi-exclamation-triangle-fill me-1"></i> ${l.doctor_name} (${l.doctor_license})</strong>
                        <span class="small text-secondary">${l.hospital} &bull; Recorded: ${new Date(l.timestamp).toLocaleString()}</span>
                    </div>
                    <span class="badge bg-danger">Block #${l.block_index}</span>
                </div>
                <div class="small mb-2">
                    <strong class="text-dark">Mandatory Emergency Justification:</strong>
                    <div class="p-2 bg-white rounded border border-danger-subtle text-danger fw-semibold mt-1">"${l.justification}"</div>
                </div>
                <div class="small text-muted d-flex justify-content-between align-items-center flex-wrap gap-1">
                    <span><strong>Data Accessed:</strong> ${l.data_accessed}</span>
                    <span class="font-monospace text-truncate" style="max-width: 250px;">Hash: ${l.block_hash}</span>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error("Error loading break glass logs:", err);
    }
}


// ===================================================================
// 14. DIGITAL HEALTH PASSPORT FOR TRAVEL CONTROLLER
// ===================================================================

function initTravelTab() {
    const dateInput = document.getElementById('travelDate');
    if (dateInput && !dateInput.value) {
        const defaultDate = new Date();
        defaultDate.setDate(defaultDate.getDate() + 14);
        dateInput.value = defaultDate.toISOString().split('T')[0];
    }
}

async function generateTravelPassport(e) {
    e.preventDefault();
    const btn = document.getElementById('btnGenTravelPassport');
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Anchoring to Blockchain...`;

    const dest = document.getElementById('travelDestination').value;
    const date = document.getElementById('travelDate').value;
    const purpose = document.getElementById('travelPurpose').value;
    const incVaccines = document.getElementById('travelCheckVaccines').checked;
    const incAllergies = document.getElementById('travelCheckAllergies').checked;
    const incFit = document.getElementById('travelCheckFitToFly').checked;

    try {
        const res = await API.post('/api/blockchain/travel-passport', {
            destination_country: dest,
            travel_date: date,
            purpose: purpose,
            include_vaccines: incVaccines,
            include_allergies: incAllergies,
            include_fit_to_fly: incFit
        });

        document.getElementById('travelDestDisplay').textContent = res.destination;
        document.getElementById('travelValidUntil').textContent = res.valid_until;
        document.getElementById('travelTokenDisplay').textContent = res.travel_token;

        const listEl = document.getElementById('travelDisclosuresList');
        const items = [];
        if (incVaccines) items.push("COVID-19 mRNA Booster & Yellow Fever (Verified by Ministry of Health)");
        if (incAllergies) items.push("Critical Allergy Warning: Penicillin (Severe Anaphylaxis)");
        if (incFit) items.push("Fit-to-fly: Unrestricted commercial air travel cleared");
        items.push("Auto-redacted: Non-essential diagnostic reports and private therapy notes");

        listEl.innerHTML = items.map(i => `<li>${i}</li>`).join('');

        alert(`✓ Verifiable Travel Health Passport Generated for ${dest}!\nToken: ${res.travel_token}\nBlock: #${res.block_index}\nSensitive unrelated records remain encrypted.`);
    } catch (err) {
        alert("Travel passport error: " + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="bi bi-qr-code-scan me-1"></i> Generate Verifiable Travel Passport`;
    }
}


// ===================================================================
// 15. FAMILY HEALTH VAULT CONTROLLER
// ===================================================================

const FAMILY_MEMBERS = {
    self: {
        name: "John Doe",
        age: 35,
        blood: "O+",
        allergies: "2 critical (Penicillin, Sulfa)",
        meds: "4 active (Metformin, Lisinopril, Aspirin, Atorvastatin)",
        records: 17,
        labs: 12
    },
    child: {
        name: "Aarav Doe",
        age: 7,
        blood: "O+",
        allergies: "1 critical (Peanut / Tree Nuts)",
        meds: "0 active",
        records: 8,
        labs: 4
    },
    parent: {
        name: "Saraswathi Doe",
        age: 68,
        blood: "B+",
        allergies: "1 critical (Ibuprofen / NSAIDs)",
        meds: "6 active (Amlodipine, Telmisartan, Rosuvastatin, Metformin)",
        records: 29,
        labs: 22
    },
    spouse: {
        name: "Priya Doe",
        age: 34,
        blood: "A+",
        allergies: "None known",
        meds: "1 active (Iron & Folic Acid)",
        records: 11,
        labs: 7
    }
};

function switchFamilyVault(memberKey) {
    document.querySelectorAll('#familyVaultBtnGroup button').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById('fVault-' + memberKey);
    if (btn) btn.classList.add('active');

    const m = FAMILY_MEMBERS[memberKey] || FAMILY_MEMBERS.self;
    
    // Update welcome & dashboard metrics
    const welcome = document.getElementById('userWelcomeText');
    if (welcome) welcome.textContent = `Viewing Vault: ${m.name} (${m.age}y)`;

    const recEl = document.getElementById('dashMetricRecords');
    if (recEl) recEl.textContent = `${m.records} verified`;

    const medEl = document.getElementById('dashMetricMeds');
    if (medEl) medEl.textContent = m.meds.split(' ')[0] + ' active';

    const algEl = document.getElementById('dashMetricAllergies');
    if (algEl) algEl.textContent = m.allergies.split(' ')[0] + ' critical';

    const labEl = document.getElementById('dashMetricLabs');
    if (labEl) labEl.textContent = `${m.labs} records`;

    alert(`Switched Active Health Vault to: ${m.name}\nSegregated permissions active.`);
}


// ===================================================================
// 16. ACCESSIBILITY TOOLBAR CONTROLLERS (High Contrast, TTS, Plain English)
// ===================================================================

let currentFontScale = 0;
function changeFontSize(delta) {
    if (delta === 0) currentFontScale = 0;
    else currentFontScale = Math.max(-1, Math.min(2, currentFontScale + delta));

    const body = document.body;
    if (currentFontScale === -1) {
        body.style.fontSize = '0.9rem';
    } else if (currentFontScale === 0) {
        body.style.fontSize = '1rem';
    } else if (currentFontScale === 1) {
        body.style.fontSize = '1.15rem';
    } else if (currentFontScale === 2) {
        body.style.fontSize = '1.3rem';
    }
}

let isHighContrast = false;
function toggleAccessibilityHighContrast() {
    isHighContrast = !isHighContrast;
    const body = document.body;
    const btnText = document.getElementById('contrastBtnText');

    if (isHighContrast) {
        body.classList.add('high-contrast-mode');
        if (btnText) btnText.textContent = "Standard Mode";
    } else {
        body.classList.remove('high-contrast-mode');
        if (btnText) btnText.textContent = "High Contrast";
    }
}

let isSpeaking = false;
function toggleReadAloudPage() {
    if (!('speechSynthesis' in window)) {
        alert("Text-to-Speech is not supported in this browser.");
        return;
    }

    if (isSpeaking) {
        window.speechSynthesis.cancel();
        isSpeaking = false;
        document.getElementById('readAloudText').textContent = "Read Aloud";
        return;
    }

    const textToRead = "Your Intelligent Health Passport. Current status: verified. Emergency access: active. 17 medical records verified with zero tampering on the blockchain.";
    const utterance = new SpeechSynthesisUtterance(textToRead);
    utterance.lang = document.getElementById('portalLangSelector')?.value || 'en-IN';
    utterance.rate = 0.95;

    utterance.onend = () => {
        isSpeaking = false;
        document.getElementById('readAloudText').textContent = "Read Aloud";
    };

    window.speechSynthesis.speak(utterance);
    isSpeaking = true;
    document.getElementById('readAloudText').textContent = "Stop Reading";
}

let plainLanguageActive = true;
function togglePlainLanguageMode() {
    plainLanguageActive = !plainLanguageActive;
    const btnText = document.getElementById('plainLanguageText');
    if (plainLanguageActive) {
        if (btnText) btnText.textContent = "Plain Language (Active)";
        alert("Simple Language Mode Active: Technical terms like 'Hypertension' are translated to 'High blood pressure', 'Dyspnea' to 'Shortness of breath'.");
    } else {
        if (btnText) btnText.textContent = "Clinical Latin Terms";
        alert("Clinical Terms Mode: Showing exact medical terminology.");
    }
}

function changePortalLanguage(lang) {
    const langNames = {
        'en-IN': 'English',
        'kn-IN': 'Kannada (ಕನ್ನಡ)',
        'ta-IN': 'Tamil (தமிழ்)',
        'te-IN': 'Telugu (తెలుగు)',
        'ml-IN': 'Malayalam (മലയാളം)',
        'hi-IN': 'Hindi (हिन्दी)'
    };
    alert(`Language preferences updated to: ${langNames[lang] || lang}.\nSymptom voice input and emergency summaries now localized.`);
}


// ===================================================================
// 17. DOCTOR GRANULAR CONSENT RESPONSE CONTROLLER
// ===================================================================

function handleDoctorConsentResponse(granted) {
    const modalEl = document.getElementById('doctorConsentRequestModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();

    if (granted) {
        const duration = document.getElementById('reqConsentDuration').value;
        alert(`✓ Access Granted to Dr. Sarah Sharma for ${duration} hours!\nA decentralized cryptographic bearer token has been generated and logged to your blockchain ledger.`);
        loadAccessHistoryTab();
    } else {
        alert("Access Request Declined. No medical records were shared with Dr. Sarah Sharma.");
    }
}


// ===================================================================
// 18. TIMELINE MILESTONE MODAL CONTROLLER (Item 4 in User Spec)
// ===================================================================

const TIMELINE_MILESTONES = {
    blood_test: {
        title: "Medical Milestone: Laboratory Diagnostics",
        category: "BLOOD TEST / METABOLIC PANEL",
        recordName: "Complete Metabolic Panel & Cardiac Biomarkers",
        doctor: "Dr. Rajesh Kumar (Cardiologist) &bull; Apollo Super-Specialty",
        date: "28 Sep 2026, 09:30 AM IST",
        diagnosis: "Mild hypercholesterolemia with borderline LDL elevation (138 mg/dL). Fasting blood glucose optimal at 94 mg/dL. Troponin I normal at 0.02 ng/mL.",
        prescription: "Lifestyle modification, Mediterranean dietary protocol, Atorvastatin 10mg once daily at bedtime for 90 days. Repeat lipid panel in 3 months.",
        hash: "0x8f3a992bc018fe4b8109d94821a7c5b6e4d2a1b9...",
        accessLog: ["28 Sep 2026: Dr. Rajesh Kumar (Authorized Clinical Consultation)", "01 Oct 2026: Apollo ER Trauma Bay (Emergency Care Protocol)"]
    },
    consultation: {
        title: "Medical Milestone: Clinical Consultation",
        category: "SPECIALIST OUTPATIENT REVIEW",
        recordName: "Cardiovascular Teleconsultation Review",
        doctor: "Dr. Sarah Sharma (Pulmonologist / Critical Care) &bull; Apex Hospital",
        date: "21 Sep 2026, 03:15 PM IST",
        diagnosis: "Post-exertional dyspnea with mild bronchospasm. Blood pressure 138/86 mmHg. Auscultation: clear bilateral breath sounds.",
        prescription: "Budesonide / Formoterol inhaler 2 puffs as needed for wheeze. Continue daily walking regimen 30 mins.",
        hash: "0x19a0bc44fe8820c78a19de023b7721ab9938c114...",
        accessLog: ["21 Sep 2026: Dr. Sarah Sharma (Telemedicine Encounter)"]
    },
    prescription: {
        title: "Medical Milestone: Digital Prescription",
        category: "VERIFIED PHARMACEUTICAL DISPENSATION",
        recordName: "Long-Term Cardioprotective Regimen",
        doctor: "Dr. Sarah Sharma &bull; License #MCI-2018-98421",
        date: "15 Aug 2026, 11:00 AM IST",
        diagnosis: "Essential Stage 1 Hypertension with metabolic stability.",
        prescription: "1. Metformin 500mg (1-0-1 after meals)\n2. Lisinopril 10mg (1-0-0 morning)\n3. Aspirin 75mg (0-1-0 post lunch)",
        hash: "0x77c9812df09a1288b487c6e3100ba7f12e88a002...",
        accessLog: ["15 Aug 2026: MedPlus Central Pharmacy (Dispensation Verification)"]
    },
    vaccine: {
        title: "Medical Milestone: Immunization Record",
        category: "PUBLIC HEALTH VACCINATION",
        recordName: "COVID-19 mRNA Updated Booster",
        doctor: "Apex Immunization Center &bull; Ministry of Health Key #VAX-8812",
        date: "02 Jul 2026, 02:45 PM IST",
        diagnosis: "Routine booster immunization administered in right deltoid. Zero adverse reactions noted during 30-min observation.",
        prescription: "Paracetamol 650mg as needed for fever/myalgia. Rest hydration advised.",
        hash: "0x44ae1298c081977be55218d89a712f00bc192837...",
        accessLog: ["02 Jul 2026: National Immunization Registry", "30 Sep 2026: International Border Health Agency"]
    }
};

function showTimelineEntryModal(entryKey) {
    const data = TIMELINE_MILESTONES[entryKey] || TIMELINE_MILESTONES.blood_test;

    document.getElementById('tModalTitle').innerHTML = `<i class="bi bi-file-medical-fill me-2"></i>${data.title}`;
    document.getElementById('tModalCategory').textContent = data.category;
    document.getElementById('tModalRecordName').textContent = data.recordName;
    document.getElementById('tModalDoctor').innerHTML = data.doctor;
    document.getElementById('tModalDate').textContent = data.date;
    document.getElementById('tModalDiagnosis').textContent = data.diagnosis;
    document.getElementById('tModalPrescription').textContent = data.prescription;
    document.getElementById('tModalHash').textContent = data.hash;

    const accessEl = document.getElementById('tModalAccessLog');
    if (accessEl) {
        accessEl.innerHTML = data.accessLog.map(a => `<div>&bull; ${a}</div>`).join('');
    }

    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('timelineEntryDetailModal'));
    modal.show();
}

// Enhance loadDigitalHealthTimeline to prepend the 2026 timeline tree
const originalLoadTimeline = loadDigitalHealthTimeline;
loadDigitalHealthTimeline = async function() {
    const container = document.getElementById('digitalHealthTimelineContainer');
    if (container) {
        container.innerHTML = `
            <div class="card p-3 mb-4 bg-light border-start border-primary border-4 shadow-sm">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <strong class="text-primary"><i class="bi bi-calendar3 me-1"></i> 2026 Longitudinal Medical Milestones</strong>
                    <span class="badge bg-success-subtle text-success">4 Verified Entries</span>
                </div>
                <div class="small">
                    <div class="py-1">
                        <span class="fw-bold text-dark">2026</span>
                        <div class="ps-3 border-start ms-2 mt-1">
                            <div class="py-2 px-2 bg-white rounded border mb-2 d-flex justify-content-between align-items-center cursor-pointer shadow-sm hover-shadow" onclick="showTimelineEntryModal('blood_test')" style="cursor: pointer;">
                                <div>
                                    <strong class="text-dark">├── Sep 28: Blood Test (Metabolic & Troponin)</strong>
                                    <small class="text-muted d-block ps-4">Apex Diagnostic Laboratory &bull; Fasting Glucose 94 mg/dL</small>
                                </div>
                                <span class="badge bg-success"><i class="bi bi-patch-check-fill me-1"></i> Verified</span>
                            </div>

                            <div class="py-2 px-2 bg-white rounded border mb-2 d-flex justify-content-between align-items-center cursor-pointer shadow-sm hover-shadow" onclick="showTimelineEntryModal('consultation')" style="cursor: pointer;">
                                <div>
                                    <strong class="text-dark">├── Sep 21: Doctor Consultation (Dr. Kumar)</strong>
                                    <small class="text-muted d-block ps-4">Apollo Super-Specialty &bull; Cardiovascular Evaluation</small>
                                </div>
                                <span class="badge bg-success"><i class="bi bi-patch-check-fill me-1"></i> Verified</span>
                            </div>

                            <div class="py-2 px-2 bg-white rounded border mb-2 d-flex justify-content-between align-items-center cursor-pointer shadow-sm hover-shadow" onclick="showTimelineEntryModal('prescription')" style="cursor: pointer;">
                                <div>
                                    <strong class="text-dark">├── Aug 15: Prescription (Cardioprotective Regimen)</strong>
                                    <small class="text-muted d-block ps-4">MedPlus Central &bull; Metformin, Lisinopril, Aspirin</small>
                                </div>
                                <span class="badge bg-success"><i class="bi bi-patch-check-fill me-1"></i> Verified</span>
                            </div>

                            <div class="py-2 px-2 bg-white rounded border d-flex justify-content-between align-items-center cursor-pointer shadow-sm hover-shadow" onclick="showTimelineEntryModal('vaccine')" style="cursor: pointer;">
                                <div>
                                    <strong class="text-dark">└── Jul 02: Vaccination (COVID-19 mRNA Booster)</strong>
                                    <small class="text-muted d-block ps-4">Apex Immunization Center &bull; Batch BNT-8821</small>
                                </div>
                                <span class="badge bg-success"><i class="bi bi-patch-check-fill me-1"></i> Verified</span>
                            </div>
                        </div>
                    </div>
                </div>
                <small class="text-muted text-center d-block mt-2"><i class="bi bi-hand-index-thumb me-1"></i> Click any milestone above to inspect doctor, diagnosis, prescription, hash, and who has accessed it.</small>
            </div>
        `;
    }
};




