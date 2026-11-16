// Doctor Portal JavaScript: SBAR Handover & Medication Safety Checker

let allConsultations = [];
let currentDoctor = null;
let activeConsultation = null;

function toggleDoctorSidebar() {
    const el = document.getElementById('doctorSidebarOffcanvas');
    if (!el) return;
    if (window.bootstrap && bootstrap.Offcanvas) {
        const offcanvas = bootstrap.Offcanvas.getOrCreateInstance(el);
        offcanvas.toggle();
    } else {
        el.classList.toggle('show');
    }
}

function activateDoctorTab(tabId) {
    if (!tabId) return;
    const cleanId = tabId.replace(/^#/, '').trim();
    
    // 1. Hide all tab panes in .tab-content
    const allPanes = document.querySelectorAll('.tab-content > .tab-pane');
    allPanes.forEach(pane => {
        pane.classList.remove('show', 'active');
        pane.style.display = 'none';
    });

    // 2. Show the target pane
    const targetPane = document.getElementById(cleanId);
    if (targetPane) {
        targetPane.classList.add('show', 'active');
        targetPane.style.display = 'block';
    }

    // 3. Update active states in sidebar
    const sidebarButtons = document.querySelectorAll('#doctorSidebarTabs .sidebar-tab-btn');
    sidebarButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.id === `btn-${cleanId}` || (btn.getAttribute('onclick') || '').includes(cleanId)) {
            btn.classList.add('active');
        }
    });

    // 4. Close offcanvas
    const offcanvasEl = document.getElementById('doctorSidebarOffcanvas');
    if (offcanvasEl && window.bootstrap && bootstrap.Offcanvas) {
        const instance = bootstrap.Offcanvas.getInstance(offcanvasEl);
        if (instance) instance.hide();
    }
}

window.addEventListener('DOMContentLoaded', async () => {
    currentDoctor = API.getUser();
    if (!currentDoctor) {
        window.location.href = '/';
        return;
    }
    if (currentDoctor.role !== 'doctor') {
        window.location.href = '/patient';
        return;
    }

    document.getElementById('docNameDisplay').textContent = currentDoctor.full_name;
    document.getElementById('docSpecDisplay').textContent = currentDoctor.specialization || 'Medical Specialist';
    document.getElementById('prescribeDoctorName').value = currentDoctor.full_name;

    await loadDoctorConsultations();
    initDoctorPatientPickers().catch(() => {});

    // Proactively pre-populate all clinical dashboard tabs
    loadDoctorCalibration().catch(() => {});
    loadDoctorDisagreements().catch(() => {});
    loadDoctorBlockchain().catch(() => {});
    loadDoctorQueue().catch(() => {});
    loadDoctorERFeed().catch(() => {});
    loadDoctorTelemetry().catch(() => {});
});

// Load Consultations
async function loadDoctorConsultations() {
    const container = document.getElementById('queueContainer');
    container.innerHTML = `<div class="col-12 text-center py-5 text-muted"><div class="spinner-border text-primary"></div><p class="mt-2">Loading clinical handovers...</p></div>`;

    try {
        allConsultations = await API.get('/api/consultations');
        updateStatistics(allConsultations);
        filterQueue();
    } catch (err) {
        container.innerHTML = `<div class="col-12 alert alert-danger">Error: ${err.message}</div>`;
    }
}

function updateStatistics(list) {
    const total = list.length;
    const pending = list.filter(c => c.status === 'pending').length;
    const completed = list.filter(c => c.status === 'completed').length;

    document.getElementById('statTotal').textContent = total;
    document.getElementById('statPending').textContent = pending;
    document.getElementById('statCompleted').textContent = completed;
}

function filterQueue() {
    const filter = document.getElementById('statusFilter').value;
    let filtered = allConsultations;
    if (filter !== 'all') {
        filtered = allConsultations.filter(c => c.status === filter);
    }
    renderQueue(filtered);
}

function renderQueue(list) {
    const container = document.getElementById('queueContainer');
    if (!list || list.length === 0) {
        container.innerHTML = `<div class="col-12 text-center py-5 text-muted">No handovers found in this category.</div>`;
        return;
    }

    container.innerHTML = list.map(c => {
        const isCompleted = c.status === 'completed';
        const hasReports = c.reports && c.reports.length > 0;
        const triageLevel = c.triage_level || 'Doctor Consultation';

        return `
            <div class="col-12">
                <div class="card border rounded-4 p-3 ${isCompleted ? 'bg-light' : 'bg-white shadow-sm'}">
                    <div class="d-flex justify-content-between align-items-start flex-wrap gap-2 mb-2">
                        <div>
                            <div class="d-flex align-items-center gap-2 flex-wrap">
                                <h5 class="fw-bold text-dark mb-0">${c.patient_name}</h5>
                                <span class="badge ${triageLevel === 'Emergency Care' ? 'bg-danger text-white' : 'bg-primary-subtle text-primary'}">
                                    <i class="bi bi-shield-check"></i> ${triageLevel}
                                </span>
                                ${hasReports ? `<span class="badge bg-info-subtle text-info"><i class="bi bi-paperclip"></i> ${c.reports.length} Scans / Reports</span>` : ''}
                                ${c.patient_allergies ? `<span class="badge bg-danger-subtle text-danger"><i class="bi bi-shield-alert"></i> Allergy: ${c.patient_allergies}</span>` : ''}
                            </div>
                            <small class="text-muted"><i class="bi bi-clock"></i> Transmitted on ${new Date(c.created_at).toLocaleString()}</small>
                        </div>
                        <div>
                            <button class="btn ${isCompleted ? 'btn-outline-primary' : 'btn-primary'} btn-sm fw-semibold" onclick="openReviewModal(${c.id})">
                                <i class="bi ${isCompleted ? 'bi-eye' : 'bi-file-medical'} me-1"></i> ${isCompleted ? 'View SBAR & Rx' : 'Review SBAR & Prescribe'}
                            </button>
                        </div>
                    </div>

                    <div class="row g-2 small text-secondary">
                        <div class="col-md-4">
                            <strong>AI Suspected Condition:</strong> <span class="text-dark fw-semibold">${c.predicted_disease || 'General'}</span> (${c.confidence_score || 0}%)
                        </div>
                        <div class="col-md-4">
                            <strong>Age / Gender:</strong> ${c.patient_age ? `${c.patient_age} yrs, ` : ''}${c.patient_gender || 'Not specified'}
                        </div>
                        <div class="col-md-4">
                            <strong>Chronic Conditions:</strong> ${c.patient_conditions || 'None reported'}
                        </div>
                    </div>

                    ${c.clinical_handover_summary && c.clinical_handover_summary.situation ? `
                        <div class="mt-2 p-2 bg-light rounded-2 small text-dark border">
                            <strong>SBAR Situation:</strong> ${c.clinical_handover_summary.situation.chief_complaint} (Duration: ${c.clinical_handover_summary.situation.onset_duration})
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

// Open SBAR Handover Review Modal
function openReviewModal(consultId) {
    activeConsultation = allConsultations.find(c => c.id === consultId);
    if (!activeConsultation) return;

    const c = activeConsultation;
    document.getElementById('prescribeConsultId').value = c.id;
    document.getElementById('reviewPatientTitle').textContent = `Clinical Handover Review: ${c.patient_name}`;
    document.getElementById('reviewConsultSubtitle').textContent = `Consultation #${c.id} • ${new Date(c.created_at).toLocaleDateString()}`;

    // Fill SBAR Handover
    const handover = c.clinical_handover_summary || {};
    const sit = handover.situation || {};
    const bg = handover.background || {};
    const ass = handover.assessment || {};
    const rec = handover.recommendation || {};

    document.getElementById('caseSituation').innerHTML = `
        <strong>Chief Complaint:</strong> ${sit.chief_complaint || c.symptoms_list.join(', ')}<br>
        <strong>Duration & Onset:</strong> ${sit.onset_duration || 'Recent'}<br>
        <strong>Discomfort Rating:</strong> ${sit.pain_intensity_scale || 'N/A'}<br>
        <strong>Patient Stated:</strong> <em>"${sit.patient_stated_concern || c.patient_notes || 'None'}"</em>
    `;

    document.getElementById('caseBackground').innerHTML = `
        <strong>Demographics:</strong> ${bg.demographics || 'Adult'}<br>
        <strong>Pre-existing Conditions:</strong> ${bg.pre_existing_conditions || c.patient_conditions || 'None'}<br>
        <strong>Current Regular Medications:</strong> ${bg.regular_medications || 'None'}<br>
        <strong class="text-danger">Known Drug Allergies:</strong> <span class="badge bg-danger-subtle text-danger">${bg.drug_allergies || c.patient_allergies || 'No Known Drug Allergies'}</span><br>
        <strong>Self-meds taken for this issue:</strong> ${bg.medication_already_taken_for_this_episode || 'None'}
    `;

    document.getElementById('caseAssessment').innerHTML = `
        <strong>AI Triage Level:</strong> <span class="badge bg-primary">${ass.ai_triage_level || c.triage_level || 'Doctor Consultation'}</span><br>
        <strong>Suspected Etiology:</strong> ${ass.probable_diagnosis || c.predicted_disease}<br>
        <strong>Flagged Lab Anomalies:</strong> ${Array.isArray(ass.abnormal_biomarkers_identified) ? ass.abnormal_biomarkers_identified.join('; ') : 'None'}
    `;

    document.getElementById('caseRecommendation').innerHTML = `
        ${Array.isArray(rec.suggested_clinical_inquiries) ? rec.suggested_clinical_inquiries.map(q => `<div>• ${q}</div>`).join('') : 'Physical examination recommended.'}
    `;

    // Populate Biomarkers Box
    const bioBox = document.getElementById('caseBiomarkersBox');
    const bio = c.extracted_biomarkers || {};
    const params = bio.extracted_parameters || {};
    const flags = bio.abnormal_flags || [];
    const rad = bio.radiology_findings || [];

    if (Object.keys(params).length > 0 || flags.length > 0 || rad.length > 0) {
        bioBox.innerHTML = `
            <div class="mb-2">
                <strong>Extracted Lab Parameters:</strong><br>
                ${Object.entries(params).map(([k, v]) => `<span class="biomarker-pill normal">${k}: ${v}</span>`).join('')}
            </div>
            ${flags.length > 0 ? `
                <div class="mb-2">
                    <strong class="text-danger">Abnormal Flags Detected:</strong><br>
                    ${flags.map(f => `<span class="biomarker-pill abnormal"><i class="bi bi-exclamation-triangle"></i> ${f}</span>`).join('')}
                </div>
            ` : ''}
            ${rad.length > 0 ? `
                <div class="text-dark"><strong>Radiology Findings:</strong> ${rad.join('; ')}</div>
            ` : ''}
        `;
    } else {
        bioBox.innerHTML = `<p class="text-muted mb-0">No lab biomarkers or radiology findings attached.</p>`;
    }

    // Reports Attachments
    const repContainer = document.getElementById('caseReportsContainer');
    if (c.reports && c.reports.length > 0) {
        repContainer.innerHTML = c.reports.map(r => `
            <div class="card p-2 border">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong class="small d-block">${r.report_type}</strong>
                        <small class="text-muted">${r.original_filename}</small>
                    </div>
                    <button type="button" class="btn btn-outline-primary btn-sm" onclick="previewDoctorScan('${r.file_url}', '${r.report_type}')">
                        <i class="bi bi-eye"></i> View Scan
                    </button>
                </div>
            </div>
        `).join('');
    } else {
        repContainer.innerHTML = `<p class="small text-muted mb-0">No raw scan images uploaded.</p>`;
    }

    // 1. Populate "Why Did AI Decide This?" Decision Map
    loadCaseExplainableMap(c);

    // 2. Pre-fill Diagnosis & Setup Disagreement Tracker
    const aiPred = c.predicted_disease || 'Pneumonia';
    document.getElementById('originalAiPrediction').value = aiPred;
    document.getElementById('aiPredictedLabel').textContent = aiPred;
    document.getElementById('finalDiagnosis').value = aiPred;
    document.getElementById('disagreementAlertBox').classList.add('d-none');
    document.getElementById('doctorRationaleText').value = '';

    // Initialize Medicines
    const medContainer = document.getElementById('medicineRowsContainer');
    medContainer.innerHTML = '';
    document.getElementById('safetyAlertBanner').classList.add('d-none');

    if (c.prescription) {
        const p = c.prescription;
        document.getElementById('finalDiagnosis').value = p.diagnosis;
        document.getElementById('generalAdvice').value = p.general_advice || '';
        document.getElementById('followUpDays').value = p.follow_up_days || 7;
        
        if (p.medicines && p.medicines.length > 0) {
            p.medicines.forEach(m => addMedicineRow(m.name, m.dosage, m.timing, m.duration, m.instructions));
        } else {
            addMedicineRow();
        }
        document.getElementById('issuePrescBtn').disabled = true;
        document.getElementById('issuePrescBtn').innerHTML = `<i class="bi bi-check2-all"></i> Already Prescribed`;
    } else {
        document.getElementById('issuePrescBtn').disabled = false;
        document.getElementById('issuePrescBtn').innerHTML = `<i class="bi bi-check-circle-fill me-1"></i> Sign & Issue Prescription`;
        document.getElementById('generalAdvice').value = 'Take medications on time with water, maintain adequate hydration, rest strictly, and monitor temperature.';
        addMedicineRow("Azithromycin / Cefuroxime", "500 mg", "1-0-0 (After Food)", "5 Days", "Take with water");
    }

    bootstrap.Modal.getOrCreateInstance(document.getElementById('reviewModal')).show();
}

async function loadCaseExplainableMap(c) {
    const barsContainer = document.getElementById('caseDecisionMapBars');
    const missingContainer = document.getElementById('caseMissingParams');
    if (!barsContainer) return;

    try {
        const syms = c.symptoms_list || [];
        const disease = c.predicted_disease || 'Pneumonia';
        const res = await API.post(`/api/closed-loop/explainable-decision-map?target_disease=${encodeURIComponent(disease)}`, syms);
        
        let html = '';
        (res.positive_attributions || []).forEach(f => {
            html += `
                <div class="d-flex justify-content-between align-items-center p-1 px-2 rounded bg-white border">
                    <span><strong class="text-dark">${f.feature}</strong> <small class="text-muted">(${f.category})</small></span>
                    <span class="badge bg-success">+${f.weight}</span>
                </div>
            `;
        });
        (res.negative_attributions || []).forEach(f => {
            html += `
                <div class="d-flex justify-content-between align-items-center p-1 px-2 rounded bg-white border">
                    <span><strong class="text-dark">${f.feature}</strong> <small class="text-muted">(${f.category})</small></span>
                    <span class="badge bg-danger">${f.weight}</span>
                </div>
            `;
        });
        barsContainer.innerHTML = html || '<span class="text-muted">Baseline symptom weighting.</span>';

        const missing = res.missing_information_penalties || [];
        if (missing.length > 0) {
            missingContainer.innerHTML = `<strong class="text-warning">Missing Dimensions:</strong> ` + 
                missing.map(m => `${m.parameter} (${m.impact})`).join('; ');
        } else {
            missingContainer.innerHTML = `<span class="text-success"><i class="bi bi-check-circle"></i> Complete clinical intake.</span>`;
        }
    } catch (e) {
        // Fallback to xai_reasoning list
        barsContainer.innerHTML = (c.xai_reasoning || []).map(r => `
            <div class="p-1 px-2 rounded bg-white border small text-dark"><i class="bi bi-check-circle text-success me-1"></i> ${r}</div>
        `).join('') || '<span class="text-muted">Clinical heuristic alignment.</span>';
    }
}


function addMedicineRow(name = '', dosage = '500 mg', timing = '1-0-1 (After food)', duration = '5 days', instructions = '') {
    const container = document.getElementById('medicineRowsContainer');
    const rowId = 'med_' + Math.random().toString(36).substring(2, 9);

    const div = document.createElement('div');
    div.id = rowId;
    div.className = "row g-2 align-items-center border p-2 rounded-2 bg-light";
    div.innerHTML = `
        <div class="col-md-3">
            <input type="text" class="form-control form-control-sm med-name" placeholder="Medicine Name" value="${name}" oninput="triggerSafetyCheck()" required>
        </div>
        <div class="col-md-2">
            <input type="text" class="form-control form-control-sm med-dosage" placeholder="Dosage" value="${dosage}" required>
        </div>
        <div class="col-md-3">
            <input type="text" class="form-control form-control-sm med-timing" placeholder="Frequency" value="${timing}" required>
        </div>
        <div class="col-md-2">
            <input type="text" class="form-control form-control-sm med-duration" placeholder="Duration" value="${duration}" required>
        </div>
        <div class="col-md-2 d-flex gap-1">
            <input type="text" class="form-control form-control-sm med-instructions" placeholder="Note" value="${instructions}">
            <button type="button" class="btn btn-outline-danger btn-sm px-2" onclick="removeMedicineRow('${rowId}')">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    `;
    container.appendChild(div);
}

function removeMedicineRow(rowId) {
    const el = document.getElementById(rowId);
    if (el) el.remove();
    triggerSafetyCheck();
}

// Live Medication Safety & Drug Allergy Checker
async function triggerSafetyCheck() {
    if (!activeConsultation) return;

    const medicines = collectCurrentMedicines();
    if (medicines.length === 0) return;

    try {
        const payload = {
            consultation_id: activeConsultation.id,
            medicines: medicines
        };
        const res = await API.post('/api/prescriptions/safety-check', payload);
        const banner = document.getElementById('safetyAlertBanner');
        const details = document.getElementById('safetyAlertDetails');

        if (!res.is_safe && res.alerts.length > 0) {
            banner.classList.remove('d-none');
            details.innerHTML = res.alerts.map(a => `
                <div class="mb-1"><strong>[${a.type}] ${a.drug}:</strong> ${a.message}</div>
            `).join('');
        } else {
            banner.classList.add('d-none');
        }
    } catch (err) {
        console.error("Safety check error:", err);
    }
}

function collectCurrentMedicines() {
    const rows = document.querySelectorAll('#medicineRowsContainer > div');
    const medicines = [];
    rows.forEach(row => {
        const name = row.querySelector('.med-name').value.trim();
        const dosage = row.querySelector('.med-dosage').value.trim();
        const timing = row.querySelector('.med-timing').value.trim();
        const duration = row.querySelector('.med-duration').value.trim();
        const instructions = row.querySelector('.med-instructions').value.trim();
        if (name) {
            medicines.push({ name, dosage, timing, duration, instructions });
        }
    });
    return medicines;
}

// Submit Doctor Prescription
async function submitPrescription(e) {
    e.preventDefault();
    const consultId = parseInt(document.getElementById('prescribeConsultId').value);
    const diagnosis = document.getElementById('finalDiagnosis').value;
    const advice = document.getElementById('generalAdvice').value;
    const followUp = parseInt(document.getElementById('followUpDays').value) || 7;

    const medicines = collectCurrentMedicines();
    if (medicines.length === 0) {
        alert("Please add at least one medication to the prescription.");
        return;
    }

    const payload = {
        consultation_id: consultId,
        diagnosis: diagnosis,
        medicines: medicines,
        general_advice: advice,
        follow_up_days: followUp
    };

    const btn = document.getElementById('issuePrescBtn');
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Checking Safety & Signing...`;

    try {
        const res = await API.post('/api/prescriptions', payload);
        bootstrap.Modal.getInstance(document.getElementById('reviewModal')).hide();
        
        // Check if clinical disagreement occurred and log it
        const originalAi = document.getElementById('originalAiPrediction').value.trim();
        const finalDiag = diagnosis.trim();
        const isDivergent = originalAi && finalDiag && (originalAi.toLowerCase() !== finalDiag.toLowerCase());

        if (isDivergent && activeConsultation) {
            try {
                const category = document.getElementById('discrepancyCategorySelect').value || 'PHYSICAL_EXAM_OVERRIDE';
                const rationale = document.getElementById('doctorRationaleText').value || 'Bedside evaluation superseded algorithm output.';
                const disagPayload = {
                    consultation_id: consultId,
                    patient_id: activeConsultation.patient_id,
                    ai_predicted_disease: originalAi,
                    ai_confidence: activeConsultation.confidence_score || 70.0,
                    ai_triage_level: activeConsultation.triage_level || "Doctor Consultation",
                    doctor_diagnosed_disease: finalDiag,
                    doctor_triage_level: "Doctor Consultation",
                    discrepancy_category: category,
                    doctor_rationale: rationale,
                    tests_considered: []
                };
                await API.post('/api/closed-loop/disagreement-record', disagPayload);
                console.log("Clinical Disagreement Record committed to audit trail.");
            } catch (dErr) {
                console.warn("Disagreement logging warning:", dErr);
            }
        }

        if (res.safety_alerts && !res.safety_alerts.is_safe) {
            alert("Prescription issued with safety alerts recorded: " + res.safety_alerts.alerts.map(a => a.message).join(' | '));
        } else {
            alert("Official Prescription digitally signed and issued! Consultation completed." + (isDivergent ? " (Clinician-AI divergence logged in audit trail)." : ""));
        }
        await loadDoctorConsultations();
    initDoctorPatientPickers().catch(() => {});
    } catch (err) {
        alert("Error issuing prescription: " + err.message);
        btn.disabled = false;
        btn.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i> Sign & Issue Prescription`;
    }
}

function checkDoctorAiDivergence() {
    const originalAi = document.getElementById('originalAiPrediction').value.trim().toLowerCase();
    const finalDiag = document.getElementById('finalDiagnosis').value.trim().toLowerCase();
    const alertBox = document.getElementById('disagreementAlertBox');

    if (originalAi && finalDiag && (originalAi !== finalDiag) && !originalAi.includes(finalDiag) && !finalDiag.includes(originalAi)) {
        alertBox.classList.remove('d-none');
    } else {
        alertBox.classList.add('d-none');
    }
}


function previewDoctorScan(url, title) {
    document.getElementById('docImageTitle').textContent = title;
    document.getElementById('docPreviewImg').src = url;
    bootstrap.Modal.getOrCreateInstance(document.getElementById('docImageModal')).show();
}

// ===================================================================
// CLINICIAN ADVANCED MODULE CONTROLLERS
// ===================================================================

let docEcgAnimId = null;
let docEcgPoints = [];

// 1. IoT Remote Patient Monitoring (RPM)
async function loadDoctorTelemetry() {
    try {
        const targetPatientId = activeConsultation?.patient_id || (allConsultations && allConsultations[0]?.patient_id);
        if (!targetPatientId) {
            const bpEl = document.getElementById('docBpVal');
            if (bpEl) bpEl.textContent = '--/-- mmHg';
            const glucEl = document.getElementById('docGlucoseVal');
            if (glucEl) glucEl.textContent = '-- mg/dL';
            const spo2El = document.getElementById('docSpo2Val');
            if (spo2El) spo2El.textContent = '--%';
            const hrEl = document.getElementById('docHrVal');
            if (hrEl) hrEl.textContent = '-- bpm';
            return;
        }
        const res = await API.get(`/api/iot/vitals/latest?patient_id=${targetPatientId}`);
        const stream = res.telemetry_stream || {};

        if (stream.bp_monitor) {
            document.getElementById('docBpVal').textContent = `${Math.round(stream.bp_monitor.primary_value)}/${Math.round(stream.bp_monitor.secondary_value || 84)} mmHg`;
        } else {
            const bpEl = document.getElementById('docBpVal');
            if (bpEl) bpEl.textContent = '--/-- mmHg';
        }
        if (stream.glucose_sensor) {
            document.getElementById('docGlucoseVal').textContent = `${Math.round(stream.glucose_sensor.primary_value)} mg/dL`;
        } else {
            const glucEl = document.getElementById('docGlucoseVal');
            if (glucEl) glucEl.textContent = '-- mg/dL';
        }
        if (stream.pulse_oximeter) {
            document.getElementById('docSpo2Val').textContent = `${Math.round(stream.pulse_oximeter.primary_value)}%`;
        } else {
            const spo2El = document.getElementById('docSpo2Val');
            if (spo2El) spo2El.textContent = '--%';
        }
        if (stream.ecg_sensor) {
            document.getElementById('docHrVal').textContent = `${Math.round(stream.ecg_sensor.primary_value)} bpm`;
            if (stream.ecg_sensor.ecg_waveform) {
                docEcgPoints = stream.ecg_sensor.ecg_waveform;
            }
        } else {
            const hrEl = document.getElementById('docHrVal');
            if (hrEl) hrEl.textContent = '-- bpm';
            docEcgPoints = [];
        }

        initDocEcgCanvas();
    } catch (err) {
        console.error("Error loading doctor telemetry:", err);
    }
}

function initDocEcgCanvas() {
    const canvas = document.getElementById('docEcgCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (docEcgAnimId) cancelAnimationFrame(docEcgAnimId);

    let offset = 0;
    const width = canvas.width;
    const height = canvas.height;
    const baseline = height / 2;

    function renderDocFrame() {
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(0, 0, width, height);

        ctx.beginPath();
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 2.5;
        ctx.shadowColor = '#34d399';
        ctx.shadowBlur = 8;

        for (let x = 0; x < width; x += 3) {
            const idx = Math.floor((x + offset) / 6) % (docEcgPoints.length || 30);
            const val = docEcgPoints[idx] || 0.0;
            const y = baseline - (val * 42);
            if (x === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();

        offset += 2;
        docEcgAnimId = requestAnimationFrame(renderDocFrame);
    }
    renderDocFrame();
}

// 2. Inbound ER & Ambulance Board
async function loadDoctorERFeed() {
    try {
        const res = await API.get('/api/emergency/doctor-feed');
        const container = document.getElementById('doctorErFeedContainer');
        if (!container) return;

        if (!res.inbound_emergencies || res.inbound_emergencies.length === 0) {
            container.innerHTML = '<div class="p-4 bg-light text-center text-muted rounded-3">No active inbound ambulances or ER emergency calls at this time.</div>';
            return;
        }

        container.innerHTML = res.inbound_emergencies.map(e => `
            <div class="card p-3 border-start border-4 ${e.status === 'resolved' ? 'border-secondary' : 'border-danger'} rounded-3 shadow-sm bg-white">
                <div class="d-flex justify-content-between align-items-center mb-2 flex-wrap gap-2">
                    <div>
                        <strong class="text-danger fs-6"><i class="bi bi-truck me-1"></i>${e.ambulance_unit}</strong>
                        <span class="badge bg-danger ms-2">${e.status.toUpperCase()}</span>
                    </div>
                    <span class="badge bg-warning text-dark fs-6"><i class="bi bi-clock-history me-1"></i>ETA: ${e.eta_minutes} Mins</span>
                </div>
                <div class="row g-2 small mb-2">
                    <div class="col-md-4">
                        <span class="text-muted">Patient:</span> <strong>${e.patient_name} (${e.age != null ? e.age + ' yrs' : 'age not recorded'})</strong>
                    </div>
                    <div class="col-md-4">
                        <span class="text-muted">Blood Group:</span> <strong class="text-danger">${e.blood_group}</strong>
                    </div>
                    <div class="col-md-4">
                        <span class="text-muted">Reserved Trauma Bay:</span> <strong class="text-primary">${e.trauma_bay}</strong>
                    </div>
                </div>
                <div class="alert alert-danger py-2 small mb-2">
                    <i class="bi bi-shield-exclamation me-1"></i> <strong>Critical Allergies:</strong> ${e.allergies || 'Not recorded'} | <strong>Live Vitals:</strong> BP ${e.vitals?.blood_pressure || 'Not recorded'}, SpO2 ${e.vitals?.spo2 || 'Not recorded'}, HR ${e.vitals?.heart_rate || 'Not recorded'}
                </div>
                ${e.patient_id ? `<button type="button" class="btn btn-sm btn-outline-danger" onclick="prefillDoctorPassport(${e.patient_id})">Open live emergency passport</button>` : ''}
            </div>
        `).join('');
    } catch (err) {
        console.error("Error loading doctor ER feed:", err);
    }
}

function prefillDoctorPassport(patientId) {
    const idInput = document.getElementById('erPassportPatientId');
    if (idInput) idInput.value = patientId;
    const purpose = document.getElementById('erPassportPurpose');
    if (purpose && !purpose.value) purpose.value = 'Inbound ER trauma assessment';
    document.getElementById('erPassportPurpose')?.focus();
}

async function openDoctorLivePassport(e) {
    e.preventDefault();
    const rawInput = document.getElementById('erPassportPatientId')?.value || '';
    const patientId = rawInput.trim();
    if (!patientId) {
        alert("Please enter a patient name or ID.");
        return;
    }
    const purpose = document.getElementById('erPassportPurpose')?.value || 'Inbound ER trauma assessment';
    const box = document.getElementById('doctorLivePassportBox');
    box.innerHTML = '<div class="text-muted small"><span class="spinner-border spinner-border-sm me-1"></span> Loading read-only emergency profile...</div>';
    try {
        const qs = new URLSearchParams({ purpose, is_emergency: 'true' });
        const res = await API.get(`/api/emergency/live-passport/${encodeURIComponent(patientId)}?${qs.toString()}`);
        const p = res.passport || {};
        const v = p.latest_vitals_snapshot || {};
        const phys = p.physician || {};
        box.innerHTML = `
            <div class="p-3 bg-white rounded-3 border">
                <div class="d-flex justify-content-between align-items-center">
                    <strong class="fs-6">${p.patient_name || p.full_name}</strong>
                    <span class="badge bg-danger fs-6">${p.blood_group || 'Unknown'}</span>
                </div>
                <div class="small mt-2"><strong class="text-danger">Allergies:</strong> ${p.drug_allergies || 'No known allergies'}</div>
                <div class="small"><strong>Conditions:</strong> ${p.pre_existing_conditions || 'None'}</div>
                <div class="small"><strong>Medications:</strong> ${p.current_medications || 'None'}</div>
                <div class="small"><strong>Contact:</strong> ${p.emergency_contact || 'None recorded'}</div>
                <div class="small"><strong>Physician:</strong> ${[phys.name, phys.specialization, phys.hospital].filter(Boolean).join(' · ') || 'Unassigned'}</div>
                <div class="small"><strong>Vitals:</strong> ${v.blood_pressure || '-'} / HR ${v.heart_rate || '-'} / SpO2 ${v.spo2 || '-'}</div>
                <div class="small text-muted mt-2 d-flex justify-content-between">
                    <span>Read-only · access audited · ${res.mode || 'emergency'}</span>
                    <button class="btn btn-sm btn-outline-primary py-0 px-2" onclick="quickFillDoctorPatientSearch('${p.patient_name || p.full_name}')">
                        <i class="bi bi-folder2-open me-1"></i> Open Full Medical Dossier
                    </button>
                </div>
            </div>
        `;
    } catch (err) {
        box.innerHTML = `<div class="alert alert-danger small mb-0">${err.message || err}</div>`;
    }
}

// 3. Live OPD Queue Console
async function loadDoctorQueue() {
    try {
        const res = await API.get('/api/queue/doctor/live-board');
        const container = document.getElementById('doctorQueueBoardContainer');
        if (!container) return;

        if (!res.active_queue || res.active_queue.length === 0) {
            container.innerHTML = '<div class="p-4 bg-light text-center text-muted rounded-3">No patients waiting in OPD queue.</div>';
            return;
        }

        container.innerHTML = `
            <table class="table table-hover align-middle mb-0">
                <thead class="table-light">
                    <tr>
                        <th>Token Code</th>
                        <th>Patient Name</th>
                        <th>Priority Level</th>
                        <th>Department</th>
                        <th>Queue Status</th>
                        <th class="text-end">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${res.active_queue.map(q => `
                        <tr>
                            <td><strong class="fs-6 text-primary">${q.token_code}</strong></td>
                            <td>${q.patient_name} ${q.patient_age ? `(${q.patient_age} yrs)` : ''}</td>
                            <td>
                                <span class="badge ${q.priority_level === 'EMERGENCY_CRITICAL' ? 'bg-danger' : q.priority_level === 'PRIORITY' ? 'bg-warning text-dark' : 'bg-secondary-subtle text-secondary'}">
                                    ${q.priority_level}
                                </span>
                            </td>
                            <td>${q.department}</td>
                            <td><span class="badge bg-light text-dark border">${q.status}</span></td>
                            <td class="text-end">
                                <button class="btn btn-primary btn-sm me-1" onclick="callDoctorQueuePatient(${q.id})">
                                    <i class="bi bi-bell-fill me-1"></i> Call
                                </button>
                                ${q.priority_level !== 'EMERGENCY_CRITICAL' ? `
                                    <button class="btn btn-outline-danger btn-sm" onclick="bumpDoctorQueueEmergency(${q.id})">
                                        <i class="bi bi-arrow-up-circle me-1"></i> Emergency P0
                                    </button>
                                ` : ''}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (err) {
        console.error("Error loading doctor queue:", err);
    }
}

async function callDoctorQueuePatient(tokenId) {
    try {
        const res = await API.post(`/api/queue/call-next/${tokenId}`);
        alert(res.message);
        await loadDoctorQueue();
    } catch (err) {
        alert("Error calling patient: " + err.message);
    }
}

async function bumpDoctorQueueEmergency(tokenId) {
    try {
        const res = await API.post(`/api/queue/emergency-bump/${tokenId}`);
        alert(res.message);
        await loadDoctorQueue();
    } catch (err) {
        alert("Error promoting token: " + err.message);
    }
}

// 4. Blockchain Audit Verifier
async function loadDoctorBlockchain() {
    try {
        const targetPatientId = activeConsultation?.patient_id || (allConsultations && allConsultations[0]?.patient_id);
        const container = document.getElementById('docBlockchainBlocksContainer');
        if (!container) return;

        if (!targetPatientId) {
            container.innerHTML = `<div class="p-4 bg-light rounded-3 text-center text-muted">No blockchain medical ledger records found. Select a patient consultation to view their ledger.</div>`;
            return;
        }

        const res = await API.get(`/api/blockchain/ledger?patient_id=${targetPatientId}`);
        if (!res.chain || res.chain.length === 0) {
            container.innerHTML = `<div class="p-4 bg-light rounded-3 text-center text-muted">No blockchain blocks anchored for Patient #${targetPatientId}.</div>`;
            return;
        }

        container.innerHTML = res.chain.map(b => `
            <div class="block-card p-3 rounded-3 shadow-sm border ${b.record_type === 'GENESIS' ? 'genesis' : ''}">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="badge ${b.record_type === 'GENESIS' ? 'bg-success' : 'bg-primary'}">Block #${b.block_index} • ${b.record_type}</span>
                    <small class="text-muted">${new Date(b.timestamp).toLocaleString()}</small>
                </div>
                <div class="small text-muted">Hash: <span class="hash-mono">${b.block_hash}</span></div>
                <div class="small text-muted mt-1">Prev: <span class="hash-mono text-secondary">${b.previous_hash}</span></div>
            </div>
        `).join('');
    } catch (err) {
        console.error("Error loading doctor blockchain:", err);
    }
}

async function doctorVerifyBlockchain() {
    try {
        const targetPatientId = activeConsultation?.patient_id || (allConsultations && allConsultations[0]?.patient_id);
        if (!targetPatientId) {
            alert("No patient consultation selected for blockchain verification.");
            return;
        }
        const res = await API.post(`/api/blockchain/verify-integrity?patient_id=${targetPatientId}`);
        const alertBox = document.getElementById('docBlockchainAlert');
        if (alertBox) alertBox.textContent = res.verification_status;
        alert(res.verification_status);
    } catch (err) {
        alert("Error verifying: " + err.message);
    }
}

async function executeDemonstrableFileVerification(injectedFile = null) {
    const input = document.getElementById('docVerifyFileInput');
    const resultBox = document.getElementById('fileVerificationResultBox');
    const file = injectedFile || (input && input.files && input.files[0]);

    if (!file) {
        alert("Please select a medical report file to verify.");
        return;
    }

    resultBox.classList.remove('d-none');
    resultBox.innerHTML = `<div class="p-3 bg-white rounded border text-center text-muted"><div class="spinner-border spinner-border-sm text-primary me-2"></div>Computing SHA-256 and validating against immutable ledger...</div>`;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await API.postForm('/api/blockchain/verify-document-file', formData);
        const isMatch = (res.status === 'MATCH');

        resultBox.innerHTML = `
            <div class="p-3 bg-white rounded-3 border">
                <div class="d-flex justify-content-between align-items-center mb-2 flex-wrap gap-2">
                    <span class="badge ${isMatch ? 'bg-success' : 'bg-danger'} fs-6 px-3 py-2">
                        <i class="bi ${isMatch ? 'bi-check-circle-fill' : 'bi-x-octagon-fill'} me-1"></i>
                        ${res.status}: ${res.verdict}
                    </span>
                    <span class="small text-muted">Block #${res.block_index || 1} &bull; Anchored: ${res.anchored_timestamp}</span>
                </div>
                <div class="small mb-2 ${isMatch ? 'text-success fw-bold' : 'text-danger fw-bold'}">
                    ${res.audit_message}
                </div>
                <div class="p-2 bg-light rounded border font-monospace small mb-2" style="font-size:0.75rem; word-break:break-all;">
                    <div><strong>1. Computed File Digest:</strong> <span class="${isMatch ? 'text-success' : 'text-danger'}">${res.computed_file_sha256}</span></div>
                    <div><strong>2. Ledger Anchored Hash:</strong> <span class="text-primary">${res.ledger_anchored_sha256}</span></div>
                    <div><strong>3. Merkle Root:</strong> <span class="text-secondary">${res.merkle_root}</span></div>
                    <div><strong>4. Validator Signature:</strong> <span class="badge ${res.validator_signature_valid ? 'bg-success-subtle text-success' : 'bg-danger-subtle text-danger'}">${res.validator_signature_valid ? 'VALID HMAC-SHA256' : 'INVALID'}</span></div>
                </div>
                <div class="small text-muted">
                    <i class="bi bi-info-circle me-1"></i><strong>Architectural Invariant:</strong> Zero cleartext PHI stored on-chain. Integrity mathematically proven via SHA-256 equality.
                </div>
            </div>
        `;
    } catch (err) {
        resultBox.innerHTML = `<div class="alert alert-danger small py-2 mb-0">Verification Error: ${escapeHtml(err.message)}</div>`;
    }
}

async function testTamperedDocumentDemonstration() {
    const tamperedContent = "MODIFIED_UNAUTHORIZED_ALTERATION: Diagnosed disease altered to Healthy (Fraudulent Tampering Test)";
    const blob = new Blob([tamperedContent], { type: 'text/plain' });
    const file = new File([blob], 'Tampered_Altered_Report.txt', { type: 'text/plain' });
    await executeDemonstrableFileVerification(file);
}

// ===================================================================
// 5. CLINICIAN-AI DISAGREEMENT RECORDS
// ===================================================================

async function loadDoctorDisagreements() {
    const container = document.getElementById('doctorDisagreementsContainer');
    if (!container) return;
    container.innerHTML = `<div class="text-center py-4"><div class="spinner-border text-warning spinner-border-sm"></div><span class="small ms-2">Loading clinical disagreement records...</span></div>`;

    try {
        const res = await API.get('/api/closed-loop/disagreement-records');
        const records = res.disagreement_records || [];
        if (records.length === 0) {
            container.innerHTML = `<div class="text-center py-4 text-muted small">No disagreement records logged yet. Concordance between clinical staff and AI models is currently 100%.</div>`;
            return;
        }

        container.innerHTML = records.map(r => `
            <div class="disagreement-card">
                <div class="d-flex justify-content-between align-items-center mb-2 flex-wrap">
                    <span class="badge ${r.severity_grade.includes('CRITICAL') ? 'bg-danger text-white' : (r.severity_grade.includes('HIGH') ? 'bg-warning text-dark' : 'bg-secondary text-white')}">
                        ${r.severity_grade.replace(/_/g, ' ')}
                    </span>
                    <small class="text-muted"><i class="bi bi-clock"></i> ${new Date(r.created_at).toLocaleString()}</small>
                </div>
                <div class="row g-2 mb-2">
                    <div class="col-md-6">
                        <strong class="small text-danger d-block"><i class="bi bi-robot me-1"></i> AI Prediction:</strong>
                        <span class="fw-semibold text-dark">${r.ai_predicted_disease}</span> (${r.ai_confidence}%)
                    </div>
                    <div class="col-md-6">
                        <strong class="small text-success d-block"><i class="bi bi-person-badge me-1"></i> Doctor Assessment:</strong>
                        <span class="fw-semibold text-dark">${r.doctor_diagnosed_disease}</span>
                    </div>
                </div>
                <div class="small mb-1">
                    <strong>Taxonomy Category:</strong> <span class="badge bg-light text-dark border">${r.discrepancy_category.replace(/_/g, ' ')}</span>
                </div>
                <div class="small p-2 bg-white rounded-2 border text-dark">
                    <strong>Physician Override Rationale:</strong> "${r.doctor_rationale}"
                </div>
                <div class="mt-2 text-end">
                    <span class="badge ${r.reconciliation_status === 'reconciled' ? 'bg-success text-white' : 'bg-warning text-dark'}">
                        ${r.reconciliation_status === 'reconciled' ? 'Ground-Truth Reconciled' : 'Pending Outcome Verification'}
                    </span>
                </div>
            </div>
        `).join('');
    } catch (err) {
        container.innerHTML = `<div class="alert alert-danger small">Error: ${err.message}</div>`;
    }
}

// ===================================================================
// 6. AI CALIBRATION & GROUND TRUTH OUTCOME CLOSED LOOP
// ===================================================================

async function loadDoctorCalibration() {
    try {
        const res = await API.get('/api/closed-loop/ai-performance-calibration');
        
        document.getElementById('kpiAiAccuracy').textContent = `${res.ai_accuracy_percentage}%`;
        document.getElementById('kpiDoctorAccuracy').textContent = `${res.doctor_accuracy_percentage}%`;
        document.getElementById('kpiOverridePrecision').textContent = `${res.clinician_override_precision}%`;
        document.getElementById('kpiDisagreementRate').textContent = `${res.disagreement_rate_percentage}%`;

        // Failure modes breakdown
        const fContainer = document.getElementById('failureModesContainer');
        const breakdown = res.failure_mode_breakdown || {};
        if (Object.keys(breakdown).length === 0) {
            fContainer.innerHTML = '<span class="text-muted small">No verified failure cases logged yet. System calibration index: OPTIMAL.</span>';
        } else {
            fContainer.innerHTML = Object.entries(breakdown).map(([mode, count]) => `
                <div class="p-2 px-3 rounded-pill bg-white border shadow-sm small">
                    <strong>${mode.replace(/_/g, ' ')}:</strong> <span class="badge bg-primary rounded-pill ms-1">${count}</span>
                </div>
            `).join('');
        }
    } catch (err) {
        console.error("Error loading calibration:", err);
    }
}

async function submitOutcomeVerification(e) {
    e.preventDefault();
    const consultId = parseInt(document.getElementById('outcomeConsultId').value);
    const trueDisease = document.getElementById('outcomeTrueDisease').value.trim();
    const method = document.getElementById('outcomeMethod').value;

    const consult = allConsultations.find(c => c.id === consultId);
    const aiPred = consult ? (consult.predicted_disease || 'Pneumonia') : 'Pneumonia';
    const docPred = consult && consult.prescription ? consult.prescription.diagnosis : (consult ? consult.predicted_disease : 'Pneumonia');
    const patientId = consult ? consult.patient_id : 4;

    const payload = {
        consultation_id: consultId,
        patient_id: patientId,
        ai_predicted_disease: aiPred,
        doctor_diagnosed_disease: docPred,
        confirmed_outcome_disease: trueDisease,
        confirmation_method: method,
        days_to_resolution: 5,
        outcome_status: "Resolved"
    };

    try {
        const res = await API.post('/api/closed-loop/verify-outcome', payload);
        const r = res.reconciliation;
        alert(`Outcome Verified!\nReconciliation Verdict: ${r.summary_verdict}\nClassification: ${r.reconciliation_type}\nFeedback Action: ${r.feedback_loop_action}`);
        document.getElementById('verifyOutcomeForm').reset();
        await loadDoctorCalibration();
        await loadDoctorDisagreements();
        await loadDoctorConsultations();
    initDoctorPatientPickers().catch(() => {});
    } catch (err) {
        alert("Error verifying outcome: " + err.message);
    }
}


// ===================================================================
// 7. BREAK-GLASS EMERGENCY OVERRIDE & PATIENT PICKER CONTROLLERS
// ===================================================================

function syncBreakGlassPatientSelect(val) {
    const idInput = document.getElementById('bgPatientId');
    if (idInput) idInput.value = val;
    const txt = document.getElementById('bgPatientSelectedText');
    if (txt) txt.innerHTML = `<i class="bi bi-person-check me-1"></i>Active Patient ID: <strong>${val}</strong>`;
}

function syncConsentRequestPatientSelect(val) {
    const idInput = document.getElementById('docReqPatientId');
    if (idInput) idInput.value = val;
    const txt = document.getElementById('docReqPatientSelectedText');
    if (txt) txt.innerHTML = `<i class="bi bi-person-check me-1"></i>Target Patient ID: <strong>${val}</strong>`;
}

async function initDoctorPatientPickers() {
    try {
        const patients = await API.get('/api/blockchain/patients-list');
        if (!patients || patients.length === 0) return;

        const bgSelect = document.getElementById('bgPatientSelect');
        const reqSelect = document.getElementById('docReqPatientSelect');

        const optionsHtml = patients.map(p => `
            <option value="${p.id}">${p.full_name} (ID: ${p.id}) — Blood: ${p.blood_group}</option>
        `).join('');

        const defaultId = activeConsultation?.patient_id || patients[0].id;

        if (bgSelect) {
            bgSelect.innerHTML = optionsHtml;
            bgSelect.value = String(defaultId);
            syncBreakGlassPatientSelect(defaultId);
        }

        if (reqSelect) {
            reqSelect.innerHTML = optionsHtml;
            reqSelect.value = String(defaultId);
            syncConsentRequestPatientSelect(defaultId);
        }
    } catch (err) {
        console.warn("Could not load dynamic patients list:", err);
    }
}

async function executeDoctorBreakGlass(e) {
    e.preventDefault();
    const btn = document.getElementById('btnSubmitBreakGlass');
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Recording Emergency Override Block...`;

    const patientId = parseInt(document.getElementById('bgPatientId')?.value || document.getElementById('bgPatientSelect')?.value || 5);
    const hospital = document.getElementById('bgHospital').value;
    const justification = document.getElementById('bgJustification').value.trim();

    try {
        const res = await API.post('/api/blockchain/break-glass', {
            patient_id: patientId,
            hospital: hospital,
            justification: justification,
            data_requested: "Critical Allergies, Blood Group, Active Medications, Trauma Baseline"
        });

        const outBox = document.getElementById('bgOutputResult');
        outBox.classList.remove('d-none');
        outBox.innerHTML = `
            <div class="alert alert-success py-2 mb-2 small">
                <i class="bi bi-shield-check me-1"></i>
                <strong>BREAK-GLASS OVERRIDE AUTHORIZED:</strong> Recorded immutably at Block #${res.block_index} (2-Hour Window).
            </div>
            <div class="p-3 bg-white rounded border">
                <h6 class="fw-bold text-danger mb-2"><i class="bi bi-heart-pulse-fill me-1"></i> Decrypted Emergency Baseline: ${res.emergency_data.patient_name} (ID: #${res.emergency_data.patient_id || patientId})</h6>
                <div class="row g-2 small">
                    <div class="col-6"><strong>Blood Group:</strong> <span class="badge bg-danger fs-6">${res.emergency_data.blood_group}</span></div>
                    <div class="col-6"><strong>Critical Allergies:</strong> <span class="text-danger fw-bold">${res.emergency_data.drug_allergies}</span></div>
                    <div class="col-6"><strong>Active Medications:</strong> ${res.emergency_data.current_medications}</div>
                    <div class="col-6"><strong>Chronic Conditions:</strong> ${res.emergency_data.pre_existing_conditions}</div>
                    <div class="col-12 text-muted border-top pt-2 mt-2"><strong>Emergency Next-of-Kin:</strong> <span class="text-dark fw-semibold">${res.emergency_data.emergency_contact}</span></div>
                </div>
            </div>
        `;
        outBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        alert(`🚨 Break-Glass Override Granted!\nPatient: ${res.emergency_data.patient_name}\nBlock Index: #${res.block_index}\nImmutable audit record and notification dispatched.`);
    } catch (err) {
        alert("Break-Glass Error: " + (err.message || err));
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="bi bi-shield-slash-fill me-1"></i> Authorize & Decrypt Records`;
    }
}

function showDoctorLicenseModal() {
    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('docLicenseModal'));
    modal.show();
}

async function submitDoctorConsentRequest(e) {
    e.preventDefault();
    const btn = document.getElementById('btnSubmitDocReq');
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Transmitting Request...`;

    const patientId = parseInt(document.getElementById('docReqPatientId')?.value || document.getElementById('docReqPatientSelect')?.value || 5);
    const purpose = document.getElementById('docReqPurpose').value;
    const hours = parseInt(document.getElementById('docReqHours').value);

    const categories = [];
    if (document.getElementById('dreqHistory').checked) categories.push('medical_history');
    if (document.getElementById('dreqLabs').checked) categories.push('lab_reports');
    if (document.getElementById('dreqMental').checked) categories.push('mental_health');
    if (document.getElementById('dreqGenetic').checked) categories.push('genetic_data');

    try {
        const res = await API.post('/api/blockchain/doctor-request-consent', {
            patient_id: patientId,
            purpose: purpose,
            requested_categories: categories,
            duration_hours: hours
        });

        alert(`✓ Consent Request Transmitted to ${res.patient_name || 'Patient #' + patientId}!\n\nRequested Scopes: ${categories.join(', ')}\nDuration: ${hours} hours.\n\nThe patient can now review and approve this request in their Sovereign Vault.`);
        const modal = bootstrap.Modal.getInstance(document.getElementById('docRequestConsentModal'));
        if (modal) modal.hide();
    } catch (err) {
        alert("Error sending consent request: " + (err.message || err));
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="bi bi-send-fill me-1"></i> Send Granular Consent Request to Patient`;
    }
}

// ==========================================
// PATIENT MEDICAL RECORDS SEARCH (BY NAME)
// Eliminates hash codes: Doctors query by patient name directly
// ==========================================

function focusPatientNameSearch() {
    activateDoctorTab('doc-records');
    setTimeout(() => {
        const inp = document.getElementById('docPatientNameInput');
        if (inp) {
            inp.focus();
            inp.select();
        }
    }, 150);
}

function quickFillDoctorPatientSearch(patientName) {
    activateDoctorTab('doc-records');
    const inp = document.getElementById('docPatientNameInput');
    if (inp) {
        inp.value = patientName;
    }
    searchPatientRecordsByName(patientName);
}

async function searchPatientRecordsByName(queryOverride) {
    if (typeof queryOverride === 'object' && queryOverride !== null && queryOverride.preventDefault) {
        queryOverride.preventDefault();
        queryOverride = null;
    }

    const inputEl = document.getElementById('docPatientNameInput');
    const query = (queryOverride || (inputEl ? inputEl.value : '') || '').trim();
    const resultBox = document.getElementById('docPatientRecordsResult');

    if (!resultBox) return;

    if (!query) {
        resultBox.innerHTML = `
            <div class="alert alert-warning d-flex align-items-center mb-0" role="alert">
                <i class="bi bi-exclamation-triangle-fill fs-4 me-3"></i>
                <div>
                    <strong>Please enter a patient name.</strong> You can enter full or partial names (e.g. <em>Rahul Verma</em>, <em>yogesh</em>), or email / patient ID.
                </div>
            </div>
        `;
        return;
    }

    resultBox.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary mb-3" style="width: 3rem; height: 3rem;" role="status">
                <span class="visually-hidden">Loading patient records...</span>
            </div>
            <h6 class="fw-semibold text-secondary">Searching Sovereign Health Database for "${escapeHtml(query)}"...</h6>
            <p class="text-muted small mb-0">Decoupled from hash codes · Querying verified clinical identity directory</p>
        </div>
    `;

    try {
        const res = await API.get(`/api/doctors/patient-records?name=${encodeURIComponent(query)}`);
        if (!res || !res.success || !res.patient) {
            throw new Error(res?.detail || 'Patient record could not be retrieved.');
        }

        const p = res.patient;
        const rec = res.records || {};
        const consults = rec.consultations || [];
        const prescripts = rec.prescriptions || [];
        const reports = rec.medical_reports || [];
        const vitals = rec.vitals || [];
        const schedules = rec.medication_schedules || [];
        const family = rec.family_members || [];

        // Latest vitals snapshot if available
        const latestVital = vitals.length > 0 ? vitals[0] : null;

        resultBox.innerHTML = `
            <!-- Patient Header Dossier Card -->
            <div class="card border-0 shadow-sm mb-4 overflow-hidden" id="printablePatientDossier">
                <div class="card-header bg-gradient bg-primary text-white p-4">
                    <div class="d-flex flex-wrap justify-content-between align-items-center gap-3">
                        <div class="d-flex align-items-center gap-3">
                            <div class="rounded-circle bg-white text-primary d-flex align-items-center justify-content-center fw-bold shadow-sm" style="width: 64px; height: 64px; font-size: 1.6rem;">
                                ${escapeHtml(p.full_name.charAt(0).toUpperCase())}
                            </div>
                            <div>
                                <div class="d-flex align-items-center gap-2">
                                    <h4 class="fw-bold mb-0 text-white">${escapeHtml(p.full_name)}</h4>
                                    <span class="badge bg-light text-dark fw-bold">ID #${p.id}</span>
                                    ${p.is_profile_verified ? '<span class="badge bg-success-subtle text-white border border-light"><i class="bi bi-shield-check me-1"></i>Verified Identity</span>' : ''}
                                </div>
                                <div class="text-white-50 small mt-1 d-flex flex-wrap gap-3">
                                    <span><i class="bi bi-person me-1"></i> ${p.age} Yrs · ${escapeHtml(p.gender)}</span>
                                    <span><i class="bi bi-envelope me-1"></i> ${escapeHtml(p.email)}</span>
                                    <span><i class="bi bi-telephone me-1"></i> ${escapeHtml(p.phone)}</span>
                                </div>
                            </div>
                        </div>
                        <div class="d-flex align-items-center gap-2">
                            <div class="text-end me-2 d-none d-md-block">
                                <div class="small text-white-50">BLOOD GROUP</div>
                                <span class="badge bg-danger fs-5 px-3 py-2 shadow-sm">${escapeHtml(p.blood_group)}</span>
                            </div>
                            <button class="btn btn-light btn-sm text-primary fw-semibold shadow-sm" onclick="window.print()">
                                <i class="bi bi-printer me-1"></i> Print Dossier
                            </button>
                        </div>
                    </div>
                </div>

                <div class="card-body p-4 bg-light bg-opacity-50">
                    <!-- Critical Clinical Alerts -->
                    <div class="row g-3 mb-4">
                        <div class="col-md-4">
                            <div class="card h-100 border-danger border-start border-4 shadow-sm bg-white">
                                <div class="card-body p-3">
                                    <div class="d-flex align-items-center justify-content-between mb-2">
                                        <h6 class="fw-bold text-danger mb-0"><i class="bi bi-exclamation-octagon-fill me-1"></i> Drug Allergies</h6>
                                        <span class="badge bg-danger-subtle text-danger">CRITICAL</span>
                                    </div>
                                    <p class="mb-0 fw-semibold text-danger fs-6">${escapeHtml(p.allergies)}</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card h-100 border-warning border-start border-4 shadow-sm bg-white">
                                <div class="card-body p-3">
                                    <div class="d-flex align-items-center justify-content-between mb-2">
                                        <h6 class="fw-bold text-warning-emphasis mb-0"><i class="bi bi-activity me-1"></i> Chronic Conditions</h6>
                                        <span class="badge bg-warning-subtle text-warning-emphasis">MONITOR</span>
                                    </div>
                                    <p class="mb-0 text-dark fw-medium">${escapeHtml(p.chronic_conditions)}</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card h-100 border-info border-start border-4 shadow-sm bg-white">
                                <div class="card-body p-3">
                                    <div class="d-flex align-items-center justify-content-between mb-2">
                                        <h6 class="fw-bold text-info-emphasis mb-0"><i class="bi bi-capsule me-1"></i> Active Medications</h6>
                                        <span class="badge bg-info-subtle text-info-emphasis">REGIMEN</span>
                                    </div>
                                    <p class="mb-0 text-dark small">${escapeHtml(p.current_medications)}</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Emergency Contact & Vitals Ribbon -->
                    <div class="card border-0 shadow-sm bg-white mb-4">
                        <div class="card-body p-3">
                            <div class="row g-3 align-items-center">
                                <div class="col-lg-4 border-end-lg">
                                    <div class="d-flex align-items-center gap-2">
                                        <i class="bi bi-telephone-inbound-fill text-danger fs-4"></i>
                                        <div>
                                            <div class="text-muted small fw-semibold">EMERGENCY NEXT-OF-KIN</div>
                                            <div class="fw-bold text-dark">${escapeHtml(p.emergency_contact_name)} (${escapeHtml(p.emergency_contact_phone)})</div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-lg-8">
                                    <div class="d-flex flex-wrap justify-content-around align-items-center gap-2 text-center">
                                        <div>
                                            <div class="text-muted small">Blood Pressure</div>
                                            <strong class="text-dark fs-6">${latestVital ? escapeHtml(latestVital.blood_pressure) : '120/80'} <small class="text-muted">mmHg</small></strong>
                                        </div>
                                        <div class="vr"></div>
                                        <div>
                                            <div class="text-muted small">Heart Rate</div>
                                            <strong class="text-danger fs-6">${latestVital ? latestVital.heart_rate : '74'} <small class="text-muted">bpm</small></strong>
                                        </div>
                                        <div class="vr"></div>
                                        <div>
                                            <div class="text-muted small">SpO2 (Pulse Ox)</div>
                                            <strong class="text-primary fs-6">${latestVital ? latestVital.spo2 : '99'} <small class="text-muted">%</small></strong>
                                        </div>
                                        <div class="vr"></div>
                                        <div>
                                            <div class="text-muted small">Blood Glucose</div>
                                            <strong class="text-warning-emphasis fs-6">${latestVital ? latestVital.blood_glucose : '102'} <small class="text-muted">mg/dL</small></strong>
                                        </div>
                                        <div class="vr"></div>
                                        <div>
                                            <div class="text-muted small">Body Temp</div>
                                            <strong class="text-dark fs-6">${latestVital ? latestVital.temperature : '98.4'} <small class="text-muted">°F</small></strong>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Inner Clinical Records Navigation Tabs -->
                    <ul class="nav nav-pills mb-3 bg-white p-2 rounded-3 border shadow-sm" id="patientRecordPills" role="tablist">
                        <li class="nav-item" role="presentation">
                            <button class="nav-link active fw-semibold" id="tab-consults-btn" data-bs-toggle="pill" data-bs-target="#tab-consults" type="button" role="tab">
                                <i class="bi bi-chat-heart me-1"></i> Consultations (${consults.length})
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link fw-semibold" id="tab-prescripts-btn" data-bs-toggle="pill" data-bs-target="#tab-prescripts" type="button" role="tab">
                                <i class="bi bi-receipt me-1"></i> Prescriptions (${prescripts.length})
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link fw-semibold" id="tab-reports-btn" data-bs-toggle="pill" data-bs-target="#tab-reports" type="button" role="tab">
                                <i class="bi bi-file-earmark-medical me-1"></i> Lab Reports & Scans (${reports.length})
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link fw-semibold" id="tab-schedules-btn" data-bs-toggle="pill" data-bs-target="#tab-schedules" type="button" role="tab">
                                <i class="bi bi-clock-history me-1"></i> Medication Chronotherapy (${schedules.length})
                            </button>
                        </li>
                        ${family.length > 0 ? `
                        <li class="nav-item" role="presentation">
                            <button class="nav-link fw-semibold" id="tab-family-btn" data-bs-toggle="pill" data-bs-target="#tab-family" type="button" role="tab">
                                <i class="bi bi-people me-1"></i> Family Dependents (${family.length})
                            </button>
                        </li>` : ''}
                    </ul>

                    <!-- Inner Tab Contents -->
                    <div class="tab-content" id="patientRecordTabsContent">
                        <!-- 1. Consultations / SBAR Clinical Handovers -->
                        <div class="tab-pane fade show active" id="tab-consults" role="tabpanel">
                            ${consults.length === 0 ? `
                                <div class="p-4 bg-white rounded-3 text-center text-muted border">
                                    <i class="bi bi-journal-medical fs-2 text-secondary mb-2"></i>
                                    <p class="mb-0">No past clinical consultations recorded for this patient.</p>
                                </div>
                            ` : consults.map(c => `
                                <div class="card border-0 shadow-sm mb-3">
                                    <div class="card-header bg-white d-flex justify-content-between align-items-center py-3 border-bottom">
                                        <div>
                                            <span class="badge bg-primary me-2">${escapeHtml(c.consultation_type || 'OPD Consultation')}</span>
                                            <strong class="text-dark">${escapeHtml(c.doctor_name || 'Dr. Self')}</strong>
                                            <span class="text-muted small">· ${escapeHtml(c.department || 'General Medicine')}</span>
                                        </div>
                                        <div class="small text-muted">
                                            <i class="bi bi-calendar3 me-1"></i> ${escapeHtml(c.date || '')} ${escapeHtml(c.time || '')}
                                        </div>
                                    </div>
                                    <div class="card-body p-3">
                                        <div class="mb-2"><strong>Chief Complaint:</strong> <span class="text-danger fw-semibold">${escapeHtml(c.chief_complaint || 'General Checkup')}</span></div>
                                        ${c.sbar_situation || c.sbar_assessment ? `
                                            <div class="p-3 bg-light rounded-3 border mb-2 small">
                                                <div class="fw-bold text-primary mb-1"><i class="bi bi-shield-shaded me-1"></i> SBAR Clinical Handover Protocol</div>
                                                <div class="row g-2">
                                                    <div class="col-md-6"><strong>Situation:</strong> ${escapeHtml(c.sbar_situation || 'Stable')}</div>
                                                    <div class="col-md-6"><strong>Background:</strong> ${escapeHtml(c.sbar_background || 'None')}</div>
                                                    <div class="col-md-6"><strong>Assessment:</strong> ${escapeHtml(c.sbar_assessment || 'Pending')}</div>
                                                    <div class="col-md-6"><strong>Recommendation:</strong> ${escapeHtml(c.sbar_recommendation || 'Continue routine care')}</div>
                                                </div>
                                            </div>
                                        ` : ''}
                                        ${c.consultation_notes ? `<div class="small text-muted mt-2"><strong>Notes:</strong> ${escapeHtml(c.consultation_notes)}</div>` : ''}
                                        ${c.prescription_summary ? `<div class="small text-success mt-1"><strong>Prescribed:</strong> ${escapeHtml(c.prescription_summary)}</div>` : ''}
                                    </div>
                                </div>
                            `).join('')}
                        </div>

                        <!-- 2. Prescriptions -->
                        <div class="tab-pane fade" id="tab-prescripts" role="tabpanel">
                            ${prescripts.length === 0 ? `
                                <div class="p-4 bg-white rounded-3 text-center text-muted border">
                                    <i class="bi bi-prescription fs-2 text-secondary mb-2"></i>
                                    <p class="mb-0">No active electronic prescriptions on record for this patient.</p>
                                </div>
                            ` : prescripts.map(rx => `
                                <div class="card border-0 shadow-sm mb-3">
                                    <div class="card-header bg-white d-flex justify-content-between align-items-center py-2">
                                        <div>
                                            <strong class="text-primary"><i class="bi bi-file-earmark-medical me-1"></i> Rx #${rx.id}</strong>
                                            <span class="text-muted small ms-2">Prescribed by ${escapeHtml(rx.doctor_name || 'Attending Physician')}</span>
                                        </div>
                                        <span class="small text-muted">${escapeHtml(rx.created_at ? new Date(rx.created_at).toLocaleDateString() : '')}</span>
                                    </div>
                                    <div class="card-body p-3">
                                        <div class="fw-bold mb-2">Diagnosis: <span class="badge bg-secondary-subtle text-secondary">${escapeHtml(rx.diagnosis || 'Clinical Assessment')}</span></div>
                                        <div class="table-responsive">
                                            <table class="table table-sm table-bordered align-middle mb-0">
                                                <thead class="table-light small">
                                                    <tr>
                                                        <th>Medicine</th>
                                                        <th>Dosage</th>
                                                        <th>Frequency</th>
                                                        <th>Duration</th>
                                                        <th>Instructions</th>
                                                    </tr>
                                                </thead>
                                                <tbody class="small">
                                                    ${(rx.medicines || []).map(m => `
                                                        <tr>
                                                            <td class="fw-bold text-dark">${escapeHtml(m.name || m.medicine_name || '')}</td>
                                                            <td>${escapeHtml(m.dosage || '-')}</td>
                                                            <td>${escapeHtml(m.frequency || '-')}</td>
                                                            <td>${escapeHtml(m.duration || '-')}</td>
                                                            <td class="text-muted">${escapeHtml(m.instructions || '-')}</td>
                                                        </tr>
                                                    `).join('')}
                                                </tbody>
                                            </table>
                                        </div>
                                        ${rx.clinical_notes ? `<div class="small text-muted mt-2"><strong>Doctor Notes:</strong> ${escapeHtml(rx.clinical_notes)}</div>` : ''}
                                    </div>
                                </div>
                            `).join('')}
                        </div>

                        <!-- 3. Uploaded Lab Reports & Scans -->
                        <div class="tab-pane fade" id="tab-reports" role="tabpanel">
                            ${reports.length === 0 ? `
                                <div class="p-4 bg-white rounded-3 text-center text-muted border">
                                    <i class="bi bi-file-earmark-x fs-2 text-secondary mb-2"></i>
                                    <p class="mb-0">No lab reports or diagnostic scans uploaded for this patient.</p>
                                </div>
                            ` : `
                                <div class="table-responsive bg-white rounded-3 border shadow-sm">
                                    <table class="table table-hover align-middle mb-0">
                                        <thead class="table-light small">
                                            <tr>
                                                <th>Report Name</th>
                                                <th>Type / Category</th>
                                                <th>Date Recorded</th>
                                                <th>Verification</th>
                                                <th class="text-end">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody class="small">
                                            ${reports.map(r => `
                                                <tr>
                                                    <td>
                                                        <div class="fw-bold text-dark"><i class="bi bi-file-earmark-pdf text-danger me-1"></i> ${escapeHtml(r.title)}</div>
                                                        ${r.doctor_notes ? `<small class="text-muted">${escapeHtml(r.doctor_notes)}</small>` : ''}
                                                    </td>
                                                    <td><span class="badge bg-light text-dark border">${escapeHtml(r.report_type || 'Diagnostic Report')}</span></td>
                                                    <td>${escapeHtml(r.date || 'Recent')}</td>
                                                    <td>
                                                        <span class="badge ${r.is_verified ? 'bg-success' : 'bg-warning text-dark'}">
                                                            <i class="bi ${r.is_verified ? 'bi-patch-check-fill' : 'bi-hourglass-split'} me-1"></i>
                                                            ${r.is_verified ? 'Verified' : 'Pending Review'}
                                                        </span>
                                                    </td>
                                                    <td class="text-end">
                                                        <a href="${escapeHtml(r.file_url)}" target="_blank" class="btn btn-sm btn-outline-primary py-1 px-2">
                                                            <i class="bi bi-eye me-1"></i> View Scan
                                                        </a>
                                                    </td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            `}
                        </div>

                        <!-- 4. Chronotherapy Schedules -->
                        <div class="tab-pane fade" id="tab-schedules" role="tabpanel">
                            ${schedules.length === 0 ? `
                                <div class="p-4 bg-white rounded-3 text-center text-muted border">
                                    <i class="bi bi-clock fs-2 text-secondary mb-2"></i>
                                    <p class="mb-0">No active chronotherapy schedule optimized for this patient.</p>
                                </div>
                            ` : `
                                <div class="table-responsive bg-white rounded-3 border shadow-sm">
                                    <table class="table table-hover align-middle mb-0">
                                        <thead class="table-light small">
                                            <tr>
                                                <th>Medicine</th>
                                                <th>Dosage</th>
                                                <th>Prescribed Time</th>
                                                <th>AI-Optimized Timing (Circadian Peak)</th>
                                                <th>Reasoning</th>
                                            </tr>
                                        </thead>
                                        <tbody class="small">
                                            ${schedules.map(s => `
                                                <tr>
                                                    <td class="fw-bold">${escapeHtml(s.medicine_name)}</td>
                                                    <td>${escapeHtml(s.dosage)}</td>
                                                    <td class="text-muted">${escapeHtml(s.prescribed_time || '-')}</td>
                                                    <td><span class="badge bg-success-subtle text-success fw-bold"><i class="bi bi-alarm me-1"></i> ${escapeHtml(s.ai_optimized_time || s.prescribed_time)}</span></td>
                                                    <td class="small text-secondary">${escapeHtml(s.condition_reason || 'Maximal bioavailability timing')}</td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            `}
                        </div>

                        <!-- 5. Family Dependents -->
                        ${family.length > 0 ? `
                            <div class="tab-pane fade" id="tab-family" role="tabpanel">
                                <div class="row g-3">
                                    ${family.map(f => `
                                        <div class="col-md-6">
                                            <div class="card border shadow-sm p-3 bg-white h-100">
                                                <div class="d-flex justify-content-between align-items-center mb-2">
                                                    <h6 class="fw-bold mb-0 text-dark">${escapeHtml(f.full_name)}</h6>
                                                    <span class="badge bg-info-subtle text-info-emphasis">${escapeHtml(f.relationship)}</span>
                                                </div>
                                                <div class="small text-muted mb-1">Blood Group: <span class="badge bg-danger">${escapeHtml(f.blood_group || 'Unknown')}</span></div>
                                                <div class="small text-danger">Allergies: ${escapeHtml(f.known_allergies || 'None recorded')}</div>
                                                <div class="small text-secondary">Conditions: ${escapeHtml(f.chronic_conditions || 'None')}</div>
                                                <div class="mt-2 pt-2 border-top">
                                                    <button class="btn btn-sm btn-outline-secondary w-100 py-1" onclick="quickFillDoctorPatientSearch('${escapeHtml(f.full_name)}')">
                                                        <i class="bi bi-search me-1"></i> Query Family Member Records
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        console.error("Error retrieving patient records:", err);
        resultBox.innerHTML = `
            <div class="alert alert-danger p-4 rounded-3 shadow-sm" role="alert">
                <div class="d-flex align-items-center mb-2">
                    <i class="bi bi-x-circle-fill fs-3 me-2 text-danger"></i>
                    <h5 class="alert-heading mb-0 fw-bold">Patient Not Found</h5>
                </div>
                <p class="mb-2">No active sovereign medical record was found matching "<strong>${escapeHtml(query)}</strong>".</p>
                <hr>
                <div class="small text-muted">
                    <strong>Search Tips:</strong>
                    <ul class="mb-0 mt-1">
                        <li>Enter the patient's full name (e.g. <em>Rahul Verma</em> or <em>yogesh</em>).</li>
                        <li>Search with partial names or their registered email address.</li>
                        <li>Hash codes are <strong>no longer required</strong> for clinician record lookups.</li>
                    </ul>
                </div>
            </div>
        `;
    }
}

// Global window exposure for HTML onclick / onsubmit bindings
window.searchPatientRecordsByName = searchPatientRecordsByName;
window.quickFillDoctorPatientSearch = quickFillDoctorPatientSearch;
window.focusPatientNameSearch = focusPatientNameSearch;
window.openDoctorLivePassport = openDoctorLivePassport;




