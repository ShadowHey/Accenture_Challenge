const API_BASE = '/api';

// ─── State ─────────────────────────────────────────────────────────────────────
const activeFilters = new Set();
let autoDischargeIntervalId = null;
let isAutoDischargeOn = false;

document.getElementById('queue-filters').addEventListener('click', (e) => {
    if (e.target.classList.contains('filter-btn')) {
        if (e.target.id === 'btn-clear-filters') {
            activeFilters.clear();
            document.querySelectorAll('#queue-filters .filter-btn').forEach(btn => btn.classList.remove('active'));
        } else {
            const filterValue = e.target.getAttribute('data-filter');
            if (activeFilters.has(filterValue)) {
                activeFilters.delete(filterValue);
                e.target.classList.remove('active');
            } else {
                activeFilters.add(filterValue);
                e.target.classList.add('active');
            }
        }
        fetchQueue();
    }
});

// ─── Data Fetching ─────────────────────────────────────────────────────────────

async function fetchQueue() {
    try {
        const res = await fetch(`${API_BASE}/queue`);
        const data = await res.json();
        
        let filteredData = data;
        if (activeFilters.size > 0) {
            filteredData = data.filter(item => {
                const priority = item.triage_result.priority;
                const source = item.triage_result.source;
                const isLevelMatch = activeFilters.has(priority);
                const isClinicianMatch = activeFilters.has('CLINICIAN_REVIEW_REQUIRED') && source === 'CLINICIAN_REVIEW_REQUIRED';
                return isLevelMatch || isClinicianMatch;
            });
        }
        
        renderQueue(filteredData);
    } catch (e) { console.error('Failed to fetch queue:', e); }
}

async function fetchAudit() {
    try {
        const filter = document.getElementById('audit-filter-type').value;
        const url = filter ? `${API_BASE}/audit?event_type=${filter}` : `${API_BASE}/audit`;
        const res = await fetch(url);
        const data = await res.json();
        renderAudit(data);
    } catch (e) { console.error('Failed to fetch audit:', e); }
}

async function fetchStats() {
    try {
        const res = await fetch(`${API_BASE}/stats`);
        const data = await res.json();
        renderStats(data);
    } catch (e) { console.error('Failed to fetch stats:', e); }
}

// ─── Rendering ─────────────────────────────────────────────────────────────────

function renderStats(stats) {
    const q = stats.queue;
    const a = stats.audit;

    document.getElementById('stat-total').textContent = q.total_patients;
    document.getElementById('stat-l1').textContent = q.level_counts['LEVEL 1'] || 0;
    document.getElementById('stat-l2').textContent = q.level_counts['LEVEL 2'] || 0;
    document.getElementById('stat-l3').textContent = q.level_counts['LEVEL 3'] || 0;
    document.getElementById('stat-l4').textContent = q.level_counts['LEVEL 4'] || 0;
    document.getElementById('stat-l5').textContent = q.level_counts['LEVEL 5'] || 0;

    const avgWait = q.avg_wait_seconds;
    document.getElementById('stat-avg-wait').textContent =
        avgWait > 60 ? `${Math.floor(avgWait/60)}m` : `${Math.round(avgWait)}s`;

    document.getElementById('stat-ml-agree').textContent =
        a.ml_agreement_rate !== null ? `${Math.round(a.ml_agreement_rate * 100)}%` : '—';

    const surgeInd = document.getElementById('surge-indicator');
    const surgeStopBtn = document.getElementById('btn-surge-stop');
    if (q.surge_mode) {
        surgeInd.style.display = 'flex';
        surgeStopBtn.style.display = 'inline-block';
    } else {
        surgeInd.style.display = 'none';
        surgeStopBtn.style.display = 'none';
    }
}

function renderQueue(queue) {
    const container = document.getElementById('queue-container');
    const hContainer = document.getElementById('horizontal-queue-container');
    const hWrapper = document.getElementById('hq-wrapper');
    
    container.innerHTML = '';
    hContainer.innerHTML = '';

    if (queue.length === 0) {
        container.innerHTML = '<p class="empty-state">No patients in queue. Click "Add Patient" or "Load Seed Patients" to begin.</p>';
        if (hWrapper) hWrapper.style.display = 'none';
        return;
    }
    
    if (hWrapper) hWrapper.style.display = 'flex';

    queue.forEach(item => {
        const p = item.patient;
        const tr = item.triage_result;

        // Badges
        let badges = '';
        if (item.reassessment_required) badges += '<span class="badge-reassess pulse">⚠ REASSESSMENT DUE</span> ';
        if (item.escalation_required) badges += '<span class="badge-escalate pulse">🔴 ESCALATION REQUIRED</span> ';
        if (tr.escalation) badges += '<span class="badge-escalate">⬆ SAFETY ESCALATION</span> ';

        const waitTime = Math.floor(Date.now()/1000 - item.added_at);
        const waitDisplay = waitTime > 60 ? `${Math.floor(waitTime/60)}m ${waitTime%60}s` : `${waitTime}s`;

        const cardClass = tr.priority.replace(' ', '-').toLowerCase();

        // Age group badge
        const ageGroupBadge = `<span class="badge-age-${tr.age_group.toLowerCase()}">${tr.age_group}</span>`;

        // Source badge
        let sourceBadge = '';
        if (tr.source === 'ML_ESCALATED') sourceBadge = '<span class="badge-ml-escalated">ML ⬆</span>';
        else if (tr.source === 'HYBRID_AGREE') sourceBadge = '<span class="badge-ml-agree">ML ✓</span>';
        else if (tr.source === 'RULES_FLOOR') sourceBadge = '<span class="badge-rules-floor">Rules Floor</span>';
        else if (tr.source === 'CLINICIAN_OVERRIDE') sourceBadge = '<span class="badge-override">Clinician</span>';
        else sourceBadge = '<span class="badge-rules-only">Rules Only</span>';

        // Confidence bar
        const confPct = Math.round(tr.confidence * 100);
        const confColor = confPct >= 80 ? '#28a745' : confPct >= 50 ? '#ffc107' : '#dc3545';

        // ML confidence bar
        let mlBar = '';
        if (tr.ml_confidence !== null && tr.ml_confidence !== undefined) {
            const mlPct = Math.round(tr.ml_confidence * 100);
            mlBar = `
                <div class="confidence-row">
                    <span class="conf-label">ML: ${tr.ml_priority || 'N/A'} (${mlPct}%)</span>
                    <div class="conf-bar"><div class="conf-fill" style="width:${mlPct}%;background:#6f42c1;"></div></div>
                </div>`;
        }

        // Disagreement
        let disagreementHtml = '';
        if (tr.disagreement) {
            disagreementHtml = `<div class="disagreement">⚡ ${tr.disagreement}</div>`;
        }

        // Reasons
        const reasonsHtml = tr.reasons.map(r => `<li>${r}</li>`).join('');

        // Feature importances
        let importancesHtml = '';
        if (tr.feature_importances) {
            const entries = Object.entries(tr.feature_importances).slice(0, 5);
            if (entries.length > 0) {
                importancesHtml = `
                    <details class="importances">
                        <summary>ML Feature Importances</summary>
                        <ul>${entries.map(([k, v]) => `<li>${k}: ${(v*100).toFixed(1)}%</li>`).join('')}</ul>
                    </details>`;
            }
        }

        // Vitals display
        const v = p.vitals;
        const vitalsHtml = [
            v.heart_rate !== null ? `HR:${v.heart_rate}` : null,
            v.spo2 !== null ? `SpO2:${v.spo2}%` : null,
            v.temperature !== null ? `T:${v.temperature}°C` : null,
            v.respiratory_rate !== null ? `RR:${v.respiratory_rate}` : null,
            v.gcs !== null ? `GCS:${v.gcs}` : null,
            v.pain_scale !== null ? `Pain:${v.pain_scale}/10` : null,
            v.blood_pressure !== null ? `BP:${v.blood_pressure}` : null,
        ].filter(Boolean).join(' | ');

        // Reassessment count
        let reassessInfo = '';
        if (item.reassessment_count > 0) {
            reassessInfo = `<span class="reassess-count">Re-assessed ${item.reassessment_count}×</span>`;
        }

        const card = document.createElement('div');
        card.className = `patient-card ${cardClass}`;
        card.innerHTML = `
            <div class="card-header">
                <h3>${p.name} <span class="patient-id">(${p.id})</span></h3>
                <div class="card-badges">
                    ${ageGroupBadge}
                    <span class="priority-badge ${cardClass}">${tr.priority}</span>
                    ${sourceBadge}
                </div>
            </div>
            <div class="card-meta">
                Age: ${p.age} | ${p.gender} | ${p.arrival_mode || 'walk-in'} ${reassessInfo}
            </div>
            <p><strong>Complaint:</strong> ${p.chief_complaint}</p>
            <p class="vitals-line"><strong>Vitals:</strong> ${vitalsHtml || 'No vitals recorded'}</p>
            <div class="confidence-row">
                <span class="conf-label">Rules: ${tr.rules_priority} (${confPct}% conf)</span>
                <div class="conf-bar"><div class="conf-fill" style="width:${confPct}%;background:${confColor};"></div></div>
            </div>
            ${mlBar}
            ${disagreementHtml}
            <p><strong>Wait:</strong> ${waitDisplay} ${badges}</p>
            <details><summary>Triage Reasons</summary><ul>${reasonsHtml}</ul></details>
            ${importancesHtml}
            <div class="card-actions">
                <button class="btn-primary btn-sm" onclick="openOverrideModal('${p.id}', '${tr.priority}')">Override</button>
                <button class="btn-warning btn-sm" onclick="openVitalsModal('${p.id}')">Update Vitals</button>
                <button class="btn-danger btn-sm" onclick="dischargePatient('${p.id}')">Discharge</button>
            </div>
        `;
        container.appendChild(card);
        
        // --- Horizontal Queue Item ---
        const hCard = document.createElement('div');
        hCard.className = `horizontal-queue-item level-${tr.priority.split(' ')[1]}`;
        const genderFull = p.gender === 'M' ? 'Male' : (p.gender === 'F' ? 'Female' : 'Other');
        hCard.innerHTML = `
            <div class="hq-name">${p.name}</div>
            <div class="hq-gender">${genderFull}</div>
            <div class="hq-age">${p.age}</div>
            <div class="hq-id">${p.id}</div>
            <div class="hq-tooltip-data" style="display: none;">
                <strong>Complaint:</strong> ${p.chief_complaint}<br>
                <strong>Vitals:</strong> ${vitalsHtml || 'No vitals'}<br>
                <strong>Priority:</strong> ${tr.priority}<br>
                <strong>Wait:</strong> ${waitDisplay}
            </div>
        `;
        if (hContainer) hContainer.appendChild(hCard);
    });
}

function renderAudit(logs) {
    const container = document.getElementById('audit-container');
    container.innerHTML = '';

    if (logs.length === 0) {
        container.innerHTML = '<p class="empty-state">No events recorded.</p>';
        return;
    }

    // Show latest 50
    logs.slice(0, 50).forEach(log => {
        const div = document.createElement('div');
        div.className = `audit-log audit-${log.event_type.toLowerCase()}`;
        const d = new Date(log.timestamp * 1000);
        const time = d.toLocaleTimeString();

        let detailHtml = '';
        const det = log.details;
        switch(log.event_type) {
            case 'TRIAGE':
                detailHtml = `Priority: <strong>${det.priority}</strong> | Source: ${det.source} | Confidence: ${Math.round(det.confidence*100)}%`;
                break;
            case 'RETRIAGE':
                detailHtml = `${det.old_priority} → <strong>${det.new_priority}</strong> | Trigger: ${det.trigger}`;
                break;
            case 'OVERRIDE':
                detailHtml = `${det.original_priority} → <strong>${det.new_priority}</strong><br/>Reason: <em>${det.reason}</em>`;
                break;
            case 'DISAGREEMENT':
                detailHtml = `Rules: ${det.rules_priority} vs ML: ${det.ml_priority} → Final: <strong>${det.final_priority}</strong> (${det.resolution})`;
                break;
            case 'DETERIORATION':
                detailHtml = `Vitals worsened`;
                break;
            case 'SURGE':
                detailHtml = `Action: ${det.action} | Patients: ${det.patient_count}`;
                break;
            case 'DISCHARGE':
                detailHtml = `Patient discharged`;
                break;
            default:
                detailHtml = JSON.stringify(det);
        }

        div.innerHTML = `
            <div class="audit-header">
                <span class="audit-type badge-${log.event_type.toLowerCase()}">${log.event_type}</span>
                <span class="audit-time">${time}</span>
            </div>
            <div class="audit-patient">${log.patient_id}</div>
            <div class="audit-detail">${detailHtml}</div>
        `;
        container.appendChild(div);
    });
}

// ─── Button Handlers ───────────────────────────────────────────────────────────

document.getElementById('btn-surge-seed').addEventListener('click', async () => {
    await fetch(`${API_BASE}/surge`, { method: 'POST' });
    refreshAll();
});

document.getElementById('btn-surge-3x').addEventListener('click', async () => {
    const btn = document.getElementById('btn-surge-3x');
    btn.disabled = true;
    btn.textContent = 'Generating...';
    await fetch(`${API_BASE}/surge/start`, { method: 'POST' });
    btn.disabled = false;
    btn.textContent = 'Simulate Surge (3×)';
    refreshAll();
});

document.getElementById('btn-surge-stop').addEventListener('click', async () => {
    await fetch(`${API_BASE}/surge/stop`, { method: 'POST' });
    refreshAll();
});

document.getElementById('btn-deteriorate').addEventListener('click', async () => {
    const btn = document.getElementById('btn-deteriorate');
    btn.disabled = true;
    const res = await fetch(`${API_BASE}/simulate/deteriorate`, { method: 'POST' });
    const data = await res.json();
    btn.disabled = false;
    if (data.patients_affected > 0) {
        alert(`${data.patients_affected} patient(s) deteriorated and re-triaged.`);
    } else {
        alert('No patients to deteriorate (queue may be empty).');
    }
    refreshAll();
});

document.getElementById('btn-clear').addEventListener('click', async () => {
    await fetch(`${API_BASE}/clear`, { method: 'POST' });
    refreshAll();
});

// ─── Auto Discharge Logic ──────────────────────────────────────────────────────

function stopAutoDischarge() {
    if (autoDischargeIntervalId) {
        clearInterval(autoDischargeIntervalId);
        autoDischargeIntervalId = null;
    }
}

function startAutoDischarge() {
    stopAutoDischarge();
    const intervalSec = parseInt(document.getElementById('auto-discharge-interval').value) || 5;
    
    autoDischargeIntervalId = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/queue`);
            const queueData = await res.json();
            
            if (queueData && queueData.length > 0) {
                const topPatientId = queueData[0].patient.id;
                await fetch(`${API_BASE}/queue/${topPatientId}/discharge`, { method: 'POST' });
                refreshAll();
            }
        } catch (e) {
            console.error('Auto discharge error:', e);
        }
    }, intervalSec * 1000);
}

document.getElementById('btn-auto-discharge').addEventListener('click', (e) => {
    isAutoDischargeOn = !isAutoDischargeOn;
    const btn = e.target;
    
    if (isAutoDischargeOn) {
        btn.textContent = 'Auto Discharge: ON';
        btn.classList.remove('btn-secondary');
        btn.classList.add('btn-primary');
        startAutoDischarge();
    } else {
        btn.textContent = 'Auto Discharge: OFF';
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-secondary');
        stopAutoDischarge();
    }
});

document.getElementById('auto-discharge-interval').addEventListener('change', () => {
    if (isAutoDischargeOn) {
        startAutoDischarge();
    }
});

// ─── Add Patient Modal ─────────────────────────────────────────────────────────

document.getElementById('btn-add-patient').addEventListener('click', () => {
    document.getElementById('add-patient-modal').style.display = 'block';
});

// Toggle Logic
const requiredFormFields = ['ap-name', 'ap-age', 'ap-gender', 'ap-complaint'];
document.querySelectorAll('input[name="ap_mode"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        if (e.target.value === 'form') {
            document.getElementById('ap-form-view').style.display = 'block';
            document.getElementById('ap-json-view').style.display = 'none';
            requiredFormFields.forEach(id => document.getElementById(id).setAttribute('required', 'true'));
        } else {
            document.getElementById('ap-form-view').style.display = 'none';
            document.getElementById('ap-json-view').style.display = 'block';
            requiredFormFields.forEach(id => document.getElementById(id).removeAttribute('required'));
        }
    });
});

// Copy Sample JSON Logic
document.getElementById('btn-copy-sample').addEventListener('click', () => {
    const sample = document.getElementById('ap-json-input').placeholder;
    navigator.clipboard.writeText(sample).then(() => {
        const btn = document.getElementById('btn-copy-sample');
        const origText = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = origText, 2000);
    });
});

document.getElementById('add-patient-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const mode = document.querySelector('input[name="ap_mode"]:checked').value;

    if (mode === 'form') {
        const body = {
            name: document.getElementById('ap-name').value,
            age: parseInt(document.getElementById('ap-age').value),
            gender: document.getElementById('ap-gender').value,
            chief_complaint: document.getElementById('ap-complaint').value,
            arrival_mode: document.getElementById('ap-arrival').value,
            history_available: document.getElementById('ap-history').value === 'true',
        };

        const hr = document.getElementById('ap-hr').value;
        const bp = document.getElementById('ap-bp').value;
        const spo2 = document.getElementById('ap-spo2').value;
        const temp = document.getElementById('ap-temp').value;
        const rr = document.getElementById('ap-rr').value;
        const gcs = document.getElementById('ap-gcs').value;
        const pain = document.getElementById('ap-pain').value;

        if (hr) body.heart_rate = parseInt(hr);
        if (bp) body.blood_pressure = bp;
        if (spo2) body.spo2 = parseInt(spo2);
        if (temp) body.temperature = parseFloat(temp);
        if (rr) body.respiratory_rate = parseInt(rr);
        if (gcs) body.gcs = parseInt(gcs);
        if (pain) body.pain_scale = parseInt(pain);

        const medHist = document.getElementById('ap-med-history').value;
        body.medical_history = medHist ? medHist.split(',').map(s => s.trim()).filter(Boolean) : [];

        const signs = document.getElementById('ap-signs').value;
        body.observed_signs = signs ? signs.split(',').map(s => s.trim()).filter(Boolean) : [];

        body.symptoms = [];

        try {
            await fetch(`${API_BASE}/patient`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            document.getElementById('add-patient-modal').style.display = 'none';
            document.getElementById('add-patient-form').reset();
            document.getElementById('ap-json-input').value = '';
            refreshAll();
        } catch (err) {
            alert('Error adding patient: ' + err.message);
        }

    } else {
        // JSON Mode
        const rawInput = document.getElementById('ap-json-input').value.trim();
        if (!rawInput) {
            alert('Please paste or type JSON data.');
            return;
        }

        // Strip JS-style comments: // and /* */
        const strippedInput = rawInput.replace(/\/\/.*|\/\*[\s\S]*?\*\//g, '');
        let parsedData;
        try {
            parsedData = JSON.parse(strippedInput);
        } catch (err) {
            alert(`Malformed JSON:\n${err.message}`);
            return;
        }

        const patients = Array.isArray(parsedData) ? parsedData : [parsedData];
        if (patients.length === 0) {
            alert('No patients found in JSON.');
            return;
        }

        // Validate required fields
        for (let i = 0; i < patients.length; i++) {
            const p = patients[i];
            const requiredFields = ['name', 'age', 'gender', 'chief_complaint'];
            for (const field of requiredFields) {
                if (p[field] === undefined || p[field] === null || p[field] === '') {
                    alert(`Validation Error in patient #${i + 1}:\nMissing required parameter '${field}'`);
                    return;
                }
            }
        }

        try {
            const apBtn = document.getElementById('ap-submit-btn');
            const originalText = apBtn.textContent;
            apBtn.textContent = 'Submitting...';
            apBtn.disabled = true;

            // Submit all patients concurrently
            await Promise.all(patients.map(p => 
                fetch(`${API_BASE}/patient`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(p)
                }).then(res => {
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    return res.json();
                })
            ));

            document.getElementById('add-patient-modal').style.display = 'none';
            document.getElementById('add-patient-form').reset();
            document.getElementById('ap-json-input').value = '';
            refreshAll();
            
            apBtn.textContent = originalText;
            apBtn.disabled = false;
        } catch (err) {
            alert('Error adding patients: ' + err.message);
            const apBtn = document.getElementById('ap-submit-btn');
            apBtn.textContent = 'Submit Patient';
            apBtn.disabled = false;
        }
    }
});

// ─── Override Modal ────────────────────────────────────────────────────────────

let currentOverrideId = null;

window.openOverrideModal = function(id, prio) {
    currentOverrideId = id;
    document.getElementById('override-patient-id').textContent = id;
    document.getElementById('override-current-prio').textContent = prio;
    document.getElementById('new-priority').value = prio;
    document.getElementById('override-reason').value = '';
    document.getElementById('override-modal').style.display = 'block';
};

document.getElementById('btn-submit-override').onclick = async () => {
    const newPrio = document.getElementById('new-priority').value;
    const reason = document.getElementById('override-reason').value;
    if (!reason) return alert('Please provide a reason for the override.');

    await fetch(`${API_BASE}/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            patient_id: currentOverrideId,
            new_priority: newPrio,
            reason: reason
        })
    });

    document.getElementById('override-modal').style.display = 'none';
    refreshAll();
};

// ─── Vitals Modal ──────────────────────────────────────────────────────────────

let currentVitalsId = null;

window.openVitalsModal = function(id) {
    currentVitalsId = id;
    document.getElementById('vitals-patient-id').textContent = id;
    document.getElementById('vitals-hr').value = '';
    document.getElementById('vitals-spo2').value = '';
    document.getElementById('vitals-temp').value = '';
    document.getElementById('vitals-rr').value = '';
    document.getElementById('vitals-gcs').value = '';
    document.getElementById('vitals-modal').style.display = 'block';
};

document.getElementById('btn-submit-vitals').onclick = async () => {
    const body = { patient_id: currentVitalsId };
    const hr = document.getElementById('vitals-hr').value;
    const spo2 = document.getElementById('vitals-spo2').value;
    const temp = document.getElementById('vitals-temp').value;
    const rr = document.getElementById('vitals-rr').value;
    const gcs = document.getElementById('vitals-gcs').value;

    if (hr) body.heart_rate = parseInt(hr);
    if (spo2) body.spo2 = parseInt(spo2);
    if (temp) body.temperature = parseFloat(temp);
    if (rr) body.respiratory_rate = parseInt(rr);
    if (gcs) body.gcs = parseInt(gcs);

    await fetch(`${API_BASE}/queue/vitals`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });

    document.getElementById('vitals-modal').style.display = 'none';
    refreshAll();
};

// ─── Discharge ─────────────────────────────────────────────────────────────────

window.dischargePatient = async function(id) {
    if (!confirm(`Discharge patient ${id}?`)) return;
    await fetch(`${API_BASE}/queue/${id}/discharge`, { method: 'POST' });
    refreshAll();
};

// ─── Modal Close Handlers ──────────────────────────────────────────────────────

document.querySelectorAll('.close-btn').forEach(btn => {
    btn.onclick = () => {
        const modalId = btn.getAttribute('data-modal');
        if (modalId) document.getElementById(modalId).style.display = 'none';
    };
});

// Close modals on outside click
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
};

// Audit filter change
document.getElementById('audit-filter-type').addEventListener('change', fetchAudit);

// ─── Refresh All ───────────────────────────────────────────────────────────────

function refreshAll() {
    fetchQueue();
    fetchAudit();
    fetchStats();
}

// Polling
setInterval(refreshAll, 3000);

// Init
refreshAll();

// ─── Shared Horizontal Queue Tooltip ───────────────────────────────────────────
const hQueueContainer = document.getElementById('horizontal-queue-container');
const sharedTooltip = document.getElementById('shared-hq-tooltip');

if (hQueueContainer && sharedTooltip) {
    hQueueContainer.addEventListener('mouseover', (e) => {
        const card = e.target.closest('.horizontal-queue-item');
        if (card) {
            const dataDiv = card.querySelector('.hq-tooltip-data');
            if (dataDiv) {
                sharedTooltip.innerHTML = dataDiv.innerHTML;
                const rect = card.getBoundingClientRect();
                sharedTooltip.style.left = `${rect.left + rect.width / 2}px`;
                // Position above the card, centering via transform
                sharedTooltip.style.top = `${rect.top + window.scrollY - 10}px`;
                sharedTooltip.style.transform = 'translate(-50%, -100%)';
                sharedTooltip.classList.add('visible');
            }
        }
    });

    hQueueContainer.addEventListener('mouseout', (e) => {
        const card = e.target.closest('.horizontal-queue-item');
        if (card) {
            sharedTooltip.classList.remove('visible');
        }
    });
}

// --- Chatbot Logic ---
const chatWidget = document.getElementById("chat-widget");
const chatToggleBtn = document.getElementById("chat-toggle-btn");
const chatBody = document.getElementById("chat-body");
const chatInput = document.getElementById("chat-input");
const chatSendBtn = document.getElementById("chat-send-btn");

// Chat states
const CHAT_STATE = {
    IDLE: "IDLE",
    SELECT_PATIENT: "SELECT_PATIENT",
    AWAIT_VITALS: "AWAIT_VITALS"
};

let currentChatState = CHAT_STATE.IDLE;
let selectedChatPatientId = null;
let currentMatches = [];

const btnOpenRhea = document.getElementById("btn-open-rhea");

// Toggle Chat
btnOpenRhea.addEventListener("click", () => {
    chatWidget.classList.remove("closed");
});

chatToggleBtn.addEventListener("click", () => {
    chatWidget.classList.add("closed");
});

// Draggable Logic
const chatHeader = document.querySelector(".chat-header");
let isDragging = false;
let offsetX, offsetY;

chatHeader.addEventListener("mousedown", (e) => {
    if (e.target.id === "chat-toggle-btn") return; // Don't drag if clicking close button
    isDragging = true;
    
    // Get the current computed style to handle 'right' vs 'left' transition
    const rect = chatWidget.getBoundingClientRect();
    
    // Set explicit left and top instead of right so dragging is smooth
    chatWidget.style.left = rect.left + "px";
    chatWidget.style.top = rect.top + "px";
    chatWidget.style.right = "auto";
    chatWidget.style.bottom = "auto";
    
    // Disable CSS transitions while dragging to prevent lag
    chatWidget.style.transition = "none";
    
    offsetX = e.clientX - rect.left;
    offsetY = e.clientY - rect.top;
});

document.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    
    // Calculate new position
    let newX = e.clientX - offsetX;
    let newY = e.clientY - offsetY;
    
    // Optional: Constrain to window bounds
    newX = Math.max(0, Math.min(newX, window.innerWidth - chatWidget.offsetWidth));
    newY = Math.max(0, Math.min(newY, window.innerHeight - chatWidget.offsetHeight));
    
    chatWidget.style.left = newX + "px";
    chatWidget.style.top = newY + "px";
});

document.addEventListener("mouseup", () => {
    if (isDragging) {
        isDragging = false;
        // Re-enable transitions for the open/close animations
        chatWidget.style.transition = "opacity 0.3s ease, transform 0.3s ease";
    }
});

// UI Helpers
function addChatMessage(text, sender, isHtml=false) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-message ${sender}`;
    if (isHtml) {
        msgDiv.innerHTML = text;
    } else {
        msgDiv.textContent = text;
    }
    chatBody.appendChild(msgDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
}

// Initialization
function resetChat(isInitial = false) {
    currentChatState = CHAT_STATE.IDLE;
    selectedChatPatientId = null;
    currentMatches = [];
    
    if (isInitial) {
        chatBody.innerHTML = "";
        addChatMessage("Hi I am Rhea your chat assistant. Which patient information do you want to update? Enter the patient name or ID.", "bot");
    } else {
        addChatMessage("Please enter the next patient's name or ID to update their vitals.", "bot");
    }
}

resetChat(true); // Initialize on load

// Handle input
async function handleChatInput() {
    const text = chatInput.value.trim();
    if (!text) return;
    
    addChatMessage(text, "user");
    chatInput.value = "";
    
    if (currentChatState === CHAT_STATE.IDLE) {
        await handlePatientSearch(text);
    } else if (currentChatState === CHAT_STATE.AWAIT_VITALS) {
        await handleVitalsUpdate(text);
    }
}

chatSendBtn.addEventListener("click", handleChatInput);
chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") handleChatInput();
});

async function handlePatientSearch(query) {
    try {
        const res = await fetch(`/api/chat/patients?name=${encodeURIComponent(query)}`);
        const data = await res.json();
        const matches = data.matches || [];
        
        if (matches.length === 0) {
            addChatMessage(`No patient found for "${query}". Please try again.`, "bot");
        } else if (matches.length === 1) {
            selectPatientForChat(matches[0].id, matches[0].name);
        } else {
            // Multiple matches
            let html = `We have ${matches.length} matches. Select which one you want to update:<br>`;
            matches.forEach((m, idx) => {
                html += `<button class="chat-action-btn" onclick="selectPatientForChat('${m.id}', '${m.name}')">${idx+1}. ${m.name}, ${m.gender}, ${m.age}</button>`;
            });
            currentMatches = matches;
            currentChatState = CHAT_STATE.SELECT_PATIENT;
            addChatMessage(html, "bot", true);
        }
    } catch (err) {
        console.error("Chat search error:", err);
        addChatMessage("Error searching for patient.", "bot");
    }
}

window.selectPatientForChat = function(id, name) {
    selectedChatPatientId = id;
    currentChatState = CHAT_STATE.AWAIT_VITALS;
    addChatMessage(`Okay, please update vitals for ${name}.`, "bot");
};

async function handleVitalsUpdate(text) {
    try {
        addChatMessage("Extracting vitals...", "bot");
        const res = await fetch("/api/chat/extract_vitals", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });
        const data = await res.json();
        const vitals = data.extracted;
        
        if (!vitals || Object.keys(vitals).length === 0) {
            addChatMessage("I couldn't understand any vitals from that. Please try again.", "bot");
            return;
        }
        
        let confirmText = "Updating with: ";
        const updates = [];
        for (const [k, v] of Object.entries(vitals)) {
            updates.push(`${k}: ${v}`);
        }
        confirmText += updates.join(", ");
        addChatMessage(confirmText, "bot");
        
        // Construct the update payload to match VitalsUpdateRequest
        const payload = { patient_id: selectedChatPatientId };
        if (vitals.heart_rate !== undefined) payload.heart_rate = vitals.heart_rate;
        if (vitals.blood_pressure !== undefined) payload.blood_pressure = vitals.blood_pressure;
        if (vitals.spo2 !== undefined) payload.spo2 = vitals.spo2;
        if (vitals.temperature !== undefined) payload.temperature = vitals.temperature;
        if (vitals.respiratory_rate !== undefined) payload.respiratory_rate = vitals.respiratory_rate;
        if (vitals.gcs !== undefined) payload.gcs = vitals.gcs;
        
        // Submit the vitals
        const updateRes = await fetch("/api/queue/vitals", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        if (updateRes.ok) {
            const updateData = await updateRes.json();
            if (updateData.escalation_triggered) {
                addChatMessage("Vitals updated successfully! Critical deterioration detected, triage escalated.", "bot");
            } else {
                addChatMessage("Vitals updated successfully.", "bot");
            }
            // Refresh dashboard
            fetchQueue();
            
            // Ask for next
            setTimeout(() => {
                resetChat();
            }, 2000);
        } else {
            addChatMessage("Failed to update vitals.", "bot");
        }
    } catch (err) {
        console.error("Chat extract error:", err);
        addChatMessage("Error extracting vitals.", "bot");
    }
}
