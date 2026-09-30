// Doctor Portal JavaScript: SBAR Handover & Medication Safety Checker

let allConsultations = [];
let currentDoctor = null;
let activeConsultation = null;

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
// CLINICIAN PATENTABLE MODULE CONTROLLERS
// ===================================================================

let docEcgAnimId = null;
let docEcgPoints = [];

// 1. IoT Remote Patient Monitoring (RPM)
async function loadDoctorTelemetry() {
    try {
        const res = await API.get('/api/iot/vitals/latest?patient_id=4');
        const stream = res.telemetry_stream || {};

        if (stream.bp_monitor) {
            document.getElementById('docBpVal').textContent = `${Math.round(stream.bp_monitor.primary_value)}/${Math.round(stream.bp_monitor.secondary_value || 84)} mmHg`;
        }
        if (stream.glucose_sensor) {
            document.getElementById('docGlucoseVal').textContent = `${Math.round(stream.glucose_sensor.primary_value)} mg/dL`;
        }
        if (stream.pulse_oximeter) {
            document.getElementById('docSpo2Val').textContent = `${Math.round(stream.pulse_oximeter.primary_value)}%`;
        }
        if (stream.ecg_sensor) {
            document.getElementById('docHrVal').textContent = `${Math.round(stream.ecg_sensor.primary_value)} bpm`;
            if (stream.ecg_sensor.ecg_waveform) {
                docEcgPoints = stream.ecg_sensor.ecg_waveform;
            }
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
                        <span class="text-muted">Patient:</span> <strong>${e.patient_name} (${e.age || 48} yrs)</strong>
                    </div>
                    <div class="col-md-4">
                        <span class="text-muted">Blood Group:</span> <strong class="text-danger">${e.blood_group}</strong>
                    </div>
                    <div class="col-md-4">
                        <span class="text-muted">Reserved Trauma Bay:</span> <strong class="text-primary">${e.trauma_bay}</strong>
                    </div>
                </div>
                <div class="alert alert-danger py-2 small mb-0">
                    <i class="bi bi-shield-exclamation me-1"></i> <strong>Critical Allergies:</strong> ${e.allergies} | <strong>Live Vitals:</strong> BP ${e.vitals?.blood_pressure || '148/94'}, SpO2 ${e.vitals?.spo2 || '96%'}, HR ${e.vitals?.heart_rate || '88 bpm'}
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error("Error loading doctor ER feed:", err);
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
        const res = await API.get('/api/blockchain/ledger?patient_id=4');
        const container = document.getElementById('docBlockchainBlocksContainer');
        if (!container) return;

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
        const res = await API.post('/api/blockchain/verify-integrity?patient_id=4');
        const alertBox = document.getElementById('docBlockchainAlert');
        alertBox.textContent = res.verification_status;
        alert(res.verification_status);
    } catch (err) {
        alert("Error verifying: " + err.message);
    }
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
    } catch (err) {
        alert("Error verifying outcome: " + err.message);
    }
}


